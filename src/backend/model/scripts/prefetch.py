from pathlib import Path
import json
from tqdm import tqdm
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import Optional

from src.backend.db.chroma import collection

BASE_DIR = Path(__file__).parents[0].parents[0].parents[0].parents[0].parents[0].resolve()
DATA_DIR = BASE_DIR / "data"

class Prefetcher:
    def __init__(
        self,
        collection,
        encoder,
        context_database: dict,
        paper_database: dict,
        rerank_top_K: int     = 500,
        max_input_length: int = 512,
        sep_token: str        = "<sep>",
        cit_token: str        = "<cit>",
        batch_size: int       = 32,
        resume: bool          = True,
    ):
        self.collection       = collection
        self.encoder          = encoder
        self.context_database = context_database
        self.paper_database   = paper_database
        self.rerank_top_K     = rerank_top_K
        self.max_input_length = max_input_length
        self.sep_token        = sep_token
        self.cit_token        = cit_token
        self.batch_size       = batch_size
        self.resume           = resume


    @staticmethod
    def build_corpus(context_list: list, output_path: str = "train_corpus.json") -> list[dict]:
        corpus = [
            {
                "context_id":    ctx["context_id"],
                "positive_ids":  [ctx["refid"]],
                "prefetched_ids": [],
            }
            for ctx in context_list
        ]
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        json.dump(corpus, open(output_path, "w"), indent=2)
        return corpus

    def _get_paper_text(self, paper_id: str) -> str:
        info = self.paper_database.get(paper_id, {})
        return info.get("title", "") + " " + info.get("abstract", "")

    def _build_query_text(self, job: dict) -> str:
        ctx          = self.context_database[job["context_id"]]
        citing_text  = self._get_paper_text(ctx["citing_id"])
        context_text = ctx["masked_text"].replace("TARGETCIT", self.cit_token)

        truncated = " ".join(citing_text.split()[:int(self.max_input_length * 0.35)])
        return truncated + self.sep_token + context_text

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self.encoder.encode(
            texts, show_progress_bar=False, convert_to_numpy=True
        ).tolist()

    def _query_chroma_batch(self, embeddings: list[list[float]]) -> list[list[str]]:
        return self.collection.query(
            query_embeddings=embeddings,
            n_results=self.rerank_top_K,
            include=["metadatas"],
        )["ids"]

    def _prefetch(self, corpus: list[dict]) -> list[dict]:
        pending = [
            i for i, job in enumerate(corpus)
            if not (self.resume and job.get("prefetched_ids"))
        ]

        for start in tqdm(range(0, len(pending), self.batch_size), desc="Prefetching"):
            batch_idx  = pending[start : start + self.batch_size]
            batch_jobs = [corpus[i] for i in batch_idx]

            embeddings = self._embed_batch(
                [self._build_query_text(job) for job in batch_jobs]
            )
            for corpus_idx, retrieved_ids in zip(batch_idx, self._query_chroma_batch(embeddings)):
                corpus[corpus_idx]["prefetched_ids"] = retrieved_ids

        return corpus

    def _run(self, input_path: str, output_path: Optional[str] = None, overwrite: bool = False) -> list[dict]:
        input_path  = Path(input_path)
        output_path = Path(output_path) if output_path else input_path

        load_path = (output_path
                     if (not overwrite and output_path.exists())
                     else input_path)

        corpus = json.load(open(load_path))

        corpus = self._prefetch(corpus)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        json.dump(corpus, open(output_path, "w"), indent=2)

        return corpus

    def run_splits(self, splits: dict[str, tuple], overwrite: bool = False):
        for split_name, (inp, out) in splits.items():
            self._run(inp, out, overwrite=overwrite)

if __name__ == "__main__":
    print("[INFO]: Initializing encoders and data files...")

    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    contexts = json.load(open(DATA_DIR /"contexts.json", "r", encoding="utf-8"))
    papers = json.load(open(DATA_DIR / "papers.json", "r", encoding="utf-8"))["root"]
    contexts_database = {ctx["context_id"]: ctx for ctx in contexts}

    print("[INFO]: Initializing prefetcher...")
    prefetcher = Prefetcher(
        collection = collection,
        encoder = encoder,
        context_database = contexts_database,
        paper_database = papers
    )

    print("[INFO]: Building corpus...")
    corpus = prefetcher.build_corpus(
        context_list = contexts,
        output_path = DATA_DIR / "train_corpus.json"
    )

    print("[INFO]: Building train set...")
    prefetcher._run(DATA_DIR / "train_corpus.json", DATA_DIR / "train.json")

    print("[INFO]: Success!")
