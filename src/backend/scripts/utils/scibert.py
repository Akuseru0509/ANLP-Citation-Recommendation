import yaml
from pathlib import Path
from chromadb import QueryResult
import torch
from transformers import AutoTokenizer

from model.scripts.scorer import Scorer

torch.set_num_threads(4)

BASE_DIR = Path(__file__).parents[0].parents[0].parents[0].resolve()
MODEL_DIR = BASE_DIR / "model"
CONFIG_DIR = BASE_DIR / "scripts" / "config" / "config.yaml"

class ModelInference:
    def __init__(self):
        args = yaml.safe_load(open(CONFIG_DIR, "r", encoding="utf-8"))

        self.model_path = MODEL_DIR / "checkpoints" / args.get("train")
        self.base_model = args.get("base_model")

        print("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        self.tokenizer.add_special_tokens({ 
            'additional_special_tokens': ['<cit>'] 
        })

        print("Initializing scorer...")
        self.scorer = Scorer(self.base_model, vocab_size=len(self.tokenizer))

        print("Loading state dict...")
        state_dicts = torch.load(self.model_path, map_location="cpu")

        self.scorer.load_state_dict(state_dicts["scorer"], strict=False)
        self.scorer.eval()

        print("Model ready!")

    def _infer(self, query: str) -> float:
        inputs = self.tokenizer(
            query,
            max_length=512,
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        with torch.inference_mode():
            score = self.scorer(inputs)

        return score

    @staticmethod
    def scibert_reranking(reranker, query: str, results: QueryResult, threshold: float = 50.0, decay: float = 0.5, min_threshold: float = 5.0):
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        n = len(ids)
        scores = [0.0] * n

        query_text = " ".join(["text before citation:", query])

        for i, (distance, meta) in enumerate(zip(dists, metas)):
            concat_query = (query_text, " ".join(["title:", meta.get("title"), "abstract:", meta.get("abstract")]))

            base = 1.0 / distance + 1e-6
            relevance_scores = reranker._infer(concat_query) * 100
            user_preference_scores = meta["ratings"]

            scores[i] += relevance_scores + base + user_preference_scores

        current_threshold = threshold

        while True:
            kept_indices = [i for i in range(0, len(scores)) if scores[i].item() >= current_threshold]

            if kept_indices is not None:
                break

            current_threshold *= decay

            if current_threshold < min_threshold:
                break

        if kept_indices is None:
            return {}

        kept_indices.sort(key=lambda i: scores[i], reverse=True)

        sorted_results = [
            {
                "id": ids[i],
                "document": docs[i],
                "metadata": metas[i],
                "distance": dists[i],
                "score": scores[i].item()
            }
            for i in kept_indices
        ]

        return sorted_results