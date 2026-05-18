from pathlib import Path
from chromadb import QueryResult
import torch
from transformers import AutoTokenizer
from src.backend.model.scripts.scorer import Scorer

BASE_DIR = Path(__file__).parents[0].parents[0].parents[0].resolve()
MODEL_DIR = BASE_DIR / "model"

class ModelInference:
    def __init__(self, model_path, base_model):
        self.model_path = model_path
        self.base_model = base_model

        print("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        self.tokenizer.add_special_tokens({ 
            'additional_special_tokens': ['<cit>'] 
        })

        print("Initializing scorer...")
        self.scorer = Scorer(base_model, vocab_size=len(self.tokenizer))

        print("Loading state dict...")
        state_dicts = torch.load(model_path, map_location="cpu")

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

        with torch.no_grad():
            score = self.scorer(inputs)

        return score

    def scibert_reranking(self, query: str, results: QueryResult, threshold: float = 50.0, decay: float = 0.5, min_threshold: float = 5.0):
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        n = len(ids)
        scores = [0.0] * n

        query_text = " ".join("text before citation:", query)

        for i, (distance, meta) in enumerate(
            zip(docs, dists, metas)
        ):
            concat_query = (query_text, " ".join(["title:", meta.get("title"), "abstract:", meta.get("abstract")]))

            base = 1.0 / distance + 1e-6
            relevance_scores = ModelInference._infer(concat_query)
            user_preference_scores = meta["ratings"]

            scores[i] += relevance_scores + base + user_preference_scores

        current_threshold = threshold

        while True:
            kept_indices = [i for i in range(n) if scores[i] >= current_threshold]

            if kept_indices is not None:
                break

            current_threshold *= decay

            if current_threshold < min_threshold:
                break

        if kept_indices is None:
            return {}

        kept_indices.sort(key=lambda i: scores[i], reverse=True)

        sorted_results = {
            "ids": [[ids[i] for i in kept_indices]],
            "documents": [[docs[i] for i in kept_indices]],
            "metadatas": [[metas[i] for i in kept_indices]],
            "distances": [[dists[i] for i in kept_indices]],
            "scores": [[scores[i] for i in kept_indices]]
        }

        return sorted_results
    
# if __name__ == "__main__":
#     model_pt = "model_batch_5072.pt"
#     base_model = "allenai/scibert_scivocab_uncased"
#     inference = ModelInference(MODEL_DIR / model_pt, base_model=base_model)
#     concat_query = """
#     text before citation: Our architecture slightly performed better than the original transformer architecture.  
#     title: Attention Is All You Need 
#     abstract: The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English to-German translation task, improving over the existing best results, including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs, a small fraction of the training costs of the best models from the literature. We show that the Transformer generalizes well to other tasks by applying it successfully to English constituency parsing both with large and limited training data.
#     """
#     score = inference._infer(concat_query)

#     print(score)