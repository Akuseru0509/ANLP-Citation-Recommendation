import os
import json
import time
import pickle
import yaml
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.amp import autocast

from transformers import AutoTokenizer

from tqdm.auto import tqdm
import numpy as np

from scorer import Scorer
from rerank_dataset import RerankDatasetForTesting

BASE_DIR = Path(__file__).parents[0].parents[0].resolve()
CONFIG_DIR = BASE_DIR / "configs"

args = yaml.safe_load(open(CONFIG_DIR / "test_config.yaml"))

os.makedirs(args.get("rerank_results_save_path"), exist_ok=True)

paper_database = json.load(open(args.get("papers_path")))["root"]
context_list = json.load(open(args.get("contexts_path")))
context_database = {ctx["context_id"]: ctx for ctx in context_list}
corpus = json.load(open(args.get("test_path")))

dataset_kwargs = dict(
    paper_database = paper_database,
    context_database = context_database,
    rerank_top_K = args.get("rerank_top_K"),
    max_input_length = args.get("max_input_length"),
    is_training = args.get("is_training"),
)

loader_kwargs = dict(
    batch_size = args.get("n_query_per_batch"),
    shuffle = False,
    num_workers = args.get("num_workers"),
    drop_last = False,
    pin_memory = True
)

def _infer_with_trained():
    tokenizer = AutoTokenizer.from_pretrained(args.get("initial_model_path"))
    tokenizer.add_special_tokens({
        'additional_special_tokens': ['<cit>']
    })
    
    rerank_dataset = RerankDatasetForTesting(corpus, **dataset_kwargs, tokenizer=tokenizer)
    dataloader = DataLoader(rerank_dataset, **loader_kwargs)
    
    vocab_size = len(tokenizer)
    scorer = Scorer(args.get("initial_model_path"), vocab_size)
    state_dicts = torch.load(args.get("trained_model_path"), map_location="cpu")
    scorer.load_state_dict(state_dicts["scorer"], strict=False)
    
    device = torch.device("cuda:%d" % (args.get("gpu_list")[0]) if torch.cuda.is_available() else "cpu")
    scorer.to(device)
    
    if device.type == "cuda" and args.get("n_device") > 1:
        scorer = nn.DataParallel(scorer, args.get("gpu_list"))

    sorted_irrelevance_levels_list = []
    num_positive_ids_list = []
    query_time_list = []
    print("Starting test ...", flush=True)

    for count, batch in enumerate(tqdm(dataloader)):
        irrelevance_levels = batch["irrelevance_levels"].to(device)
        input_ids = batch["input_ids"].to(device)
        token_type_ids = batch["token_type_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        num_positive_ids = batch["num_positive_ids"]
        n_doc = input_ids.size(1)
        num_positive_ids_list += num_positive_ids.detach().cpu().numpy().tolist()

        input_ids = input_ids.view(-1, input_ids.size(2))
        token_type_ids = token_type_ids.view(-1, token_type_ids.size(2))
        attention_mask = attention_mask.view(-1, attention_mask.size(2))

        tic = time.time()
        score = []
        sub_size = args.get("sub_batch_size")
        for pos in range(0, input_ids.size(0), sub_size):
            with torch.no_grad():
                with autocast(device_type="cuda"):
                    score.append(
                        scorer({
                            "input_ids": input_ids[pos:pos + sub_size],
                            "token_type_ids": token_type_ids[pos:pos + sub_size],
                            "attention_mask": attention_mask[pos:pos + sub_size]
                        }).detach()
                    )
        score = torch.cat(score, dim=0).view(-1, n_doc).cpu().numpy()
        tac = time.time()
        query_time_list.append(tac - tic)

        irrelevance_levels = irrelevance_levels.detach().cpu().numpy()
        for pos in range(irrelevance_levels.shape[0]):
            sorted_irrelevance_level = list(
                zip(
                    *sorted(zip(irrelevance_levels[pos], score[pos]), key=lambda x: -x[1])
                )
            )[0]
            sorted_irrelevance_levels_list.append(sorted_irrelevance_level)

        if (count + 1) % 200 == 0:
            num_positive_ids_arr = np.asarray(num_positive_ids_list)
            max_len = max(len(item) for item in sorted_irrelevance_levels_list)

            sorted_irrelevance_levels_arr = np.asarray([
                list(item) + [-1] * (max_len - len(item))
                for item in sorted_irrelevance_levels_list
            ])

            hit_matrix = (sorted_irrelevance_levels_arr == rerank_dataset.irrelevance_level_for_positive)

            metrics = {"recall": {}}
            for K in args.K_list:
                top_k_hits = hit_matrix[:, :K]
                recall = (top_k_hits.sum(axis=1) / num_positive_ids_arr).mean()
                metrics["recall"][K] = recall

            print(f"\n[Batch {count + 1}] Cumulative avg metrics so far:", flush=True)
            for k, v in metrics.items():
                print(f"K = {k} -> {v}", flush=True)

    num_positive_ids_arr = np.asarray(num_positive_ids_list)
    max_len = max(len(item) for item in sorted_irrelevance_levels_list)

    sorted_irrelevance_levels_arr = np.asarray([
        list(item) + [-1] * (max_len - len(item))
        for item in sorted_irrelevance_levels_list
    ])

    hit_matrix = (sorted_irrelevance_levels_arr == rerank_dataset.irrelevance_level_for_positive)

    metrics = {"recall": {}}
    for K in args.K_list:
        top_k_hits = hit_matrix[:, :K]
        recall = (top_k_hits.sum(axis=1) / num_positive_ids_arr).mean()
        metrics["recall"][K] = recall

    print("\n[FINAL] Average metrics over all batches:", flush=True)
    print(metrics, flush=True)

    with open(f"{args.get("rerank_results_save_path")}/output_trained.pkl", "wb") as f:
        pickle.dump(
            {"hit_matrix": hit_matrix, "num_positive_ids": num_positive_ids_arr},
            f,
            protocol=-1
        )
    print("Finished!")

if __name__ == "__main__":
    _infer_with_trained()