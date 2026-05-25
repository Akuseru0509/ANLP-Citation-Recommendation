import json
import os
import time
import yaml
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW

from transformers import AutoTokenizer

import numpy as np
from tqdm import tqdm

from scorer import Scorer
from loss import TripletLoss
from rerank_dataset import RerankDataset
from utils import save_model

BASE_DIR = Path(__file__).parents[0].parents[0].resolve()
CONFIG_DIR = BASE_DIR / "configs"

def build_model_input(batch, device):
    inp = {
        "input_ids": batch["input_ids"].to(device),
        "attention_mask": batch["attention_mask"].to(device),
    }

    if "token_type_ids" in batch:
        inp["token_type_ids"] = batch["token_type_ids"].to(device)
    
    return inp

def train_iteration(batch):
    irrelevance_levels = batch["irrelevance_levels"].to(device)
    inp = build_model_input(batch, device)
    n_doc = inp["input_ids"].size(1)

    model_inp = {k: v.view(-1, v.size(2)) for k, v in inp.items()}
    score = scorer(model_inp).view(-1, n_doc)
    loss = triplet_loss(score, irrelevance_levels)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    loss_val = loss.item()
    torch.cuda.empty_cache()
    return loss_val

if __name__ == "__main__":
    args = yaml.safe_load(open(CONFIG_DIR / "train_config.yaml"))

    os.makedirs(args.get("model_folder"), exist_ok=True)
    os.makedirs(args.get("log_folder"), exist_ok=True)

    paper_database = json.load(open(args.get("paper_database_path")))["root"]
    
    context_list = json.load(open(args.get("context_database_path")))
    context_database = {ctx["context_id"]: ctx for ctx in context_list}

    corpus = json.load(open(args.get("train_corpus_path")))

    tokenizer = AutoTokenizer.from_pretrained(args.get("initial_model_path"))
    tokenizer.add_special_tokens({"additional_special_tokens": ["<cit>"]})

    dataset_kwargs = dict(
        paper_database = paper_database,
        context_database = context_database,
        tokenizer = tokenizer,
        rerank_top_K = args.get("rerank_top_K"),
        max_input_length = args.get("max_input_length"),
        n_document = args.get("n_document"),
        max_n_positive = args.get("max_n_positive"),
        sep_token = tokenizer.sep_token
    )

    loader_kwargs = dict(
        batch_size = args.get("n_query_per_batch"),
        num_workers = args.get("num_workers"),
        drop_last = True,
        worker_init_fn = lambda x: [
            np.random.seed(int(time.time()) + x),
            torch.manual_seed(int(time.time()) + x),
        ],
        pin_memory = True,
    )

    rerank_dataset = RerankDataset(corpus, **dataset_kwargs, is_training=True)
    rerank_dataloader = DataLoader(rerank_dataset, shuffle=True, **loader_kwargs)

    vocab_size = len(tokenizer)
    scorer = Scorer(args.get("initial_model_path"), vocab_size)

    device = torch.device(
        f"cuda:{args.get("gpu_list")[0]}" if torch.cuda.is_available() else "cpu"
    )

    scorer.to(device)

    if device.type == "cuda" and args.get("n_device") > 1:
        scorer = nn.DataParallel(scorer, args.get("gpu_list"))
        model_parameters = [p for p in scorer.module.parameters() if p.requires_grad]
    else:
        model_parameters = [p for p in scorer.parameters() if p.requires_grad]

    optimizer = AdamW(model_parameters, lr=args.get("initial_learning_rate"), weight_decay=args.get("l2_weight"))
    triplet_loss = TripletLoss(args.get("base_margin"))

    running_losses = []
    current_batch = 0

    for epoch in range(args.get("num_epochs")):
        print(f"\n=== Epoch {epoch + 1} / {args.get("num_epochs")} ===")

        for count, batch in enumerate(tqdm(rerank_dataloader, desc=f"Epoch {epoch+1}")):
            current_batch += 1
            running_losses.append(train_iteration(batch))

            if current_batch % args.get("print_every") == 0:
                msg = "[batch: %05d] loss: %.4f" % (current_batch, np.mean(running_losses))
                print(msg) 
                running_losses = []

            if current_batch % args.get("save_every") == 0:
                save_model(
                    {
                        "current_batch": current_batch, 
                        "scorer": scorer, 
                        "optimizer": optimizer.state_dict()
                    },
                    f"{args.get("model_folder")}/model_batch_{current_batch}.pt",
                    args.get("max_num_checkpoints"),
                )
                print("Model saved!")

        save_model(
            {"current_batch": current_batch, "scorer": scorer, "optimizer": optimizer.state_dict()},
            f"{args.get("final_folder")}/model_batch_{current_batch}.pt",
            args.get("max_num_checkpoints"),
        )
        print("Model saved!")