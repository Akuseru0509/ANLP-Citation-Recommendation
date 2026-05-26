import dotenv
import os
import requests
from pathlib import Path
import json
import re
from tqdm import tqdm
import time

dotenv.load_dotenv()

BASE_DIR = Path(__file__).parents[0].parents[0].parents[0].resolve()
DATA_DIR = BASE_DIR / "data"

API_KEY = os.getenv("API_KEY")
BASE = "https://api.semanticscholar.org/graph/v1"
DATASET_BASE = "https://api.semanticscholar.org/datasets/v1"
HEADERS = {"x-api-key": API_KEY}

class ContextCreator():
    def __init__(self, data_path):
        self.data_path = data_path

    def _chunked(self, lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    def _batch_map_arxiv_to_s2(self, arxiv_ids: list[str]) -> dict[str, str]:
        mapping = {}

        chunks = list(self._chunked(arxiv_ids, 500))

        for chunk in tqdm(chunks, desc="Mapping arXiv → S2 IDs"):
            payload = {"ids": [f"ArXiv:{aid}" for aid in chunk]}
            resp = requests.post(
                f"{BASE}/paper/batch",
                headers=HEADERS,
                params={"fields": "paperId,externalIds"},
                json=payload
            )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 5))
                time.sleep(retry_after)
                continue

            elif resp.status_code != 200:
                print(f"Batch error {resp.status_code}: {resp.text[:200]}")
                time.sleep(2)
                continue

            for item in resp.json():
                if not item:
                    continue

                ext = item.get("externalIds") or {}
                arxiv_id = ext.get("ArXiv", "").strip()
                s2_id = item.get("paperId", "")

                if arxiv_id and s2_id:
                    mapping[arxiv_id] = s2_id

            time.sleep(1.1)

        print(f"Mapped {len(mapping)} / {len(arxiv_ids)} papers to S2 IDs")
        return mapping

    @staticmethod
    def _get_citations_dataset_urls() -> list[str]:
        resp = requests.get(
            f"{DATASET_BASE}/release/latest/dataset/citations",
            headers=HEADERS
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get dataset URLs: {resp.status_code} {resp.text}")
        
        urls = resp.json().get("files", [])

        print(f"  Found {len(urls)} citation dataset shards")
        return urls

    @staticmethod
    def _normalize_context(sentence: str, target_position: int) -> str:
        citation_pattern = re.compile(
            r'\([A-Z][^)]{2,60}\d{4}[^)]*\)'
            r'|\[\d+(?:[,;\s]+\d+)*\]'
            r'|\(\d{4}\)'
        )
    
        matches = list(citation_pattern.finditer(sentence))
        if not matches:
            return sentence
    
        target_idx = target_position % len(matches)
    
        result = list(sentence)
        for i, match in enumerate(reversed(matches)):
            forward_i = len(matches) - 1 - i
            tag = "TARGETCIT" if forward_i == target_idx else "OTHERCIT"
            result[match.start():match.end()] = list(tag)
    
        return "".join(result)

    def _batch_fetch_citations(
        self,
        arxiv_to_s2: dict[str, str],
        arxiv_id_set: set[str]
    ) -> list[dict]:

        s2_to_arxiv = {v: k for k, v in arxiv_to_s2.items()}
        corpus_s2_set = set(arxiv_to_s2.values())
        seen_pairs = {}
        contexts = []

        out_path = DATA_DIR / "contexts.json"
        done_path = DATA_DIR / "done_s2_ids.json"
        pairs_path = DATA_DIR / "intra_pairs.json"

        done_ids = set(json.load(open(done_path)) if done_path.exists() else [])

        if out_path.exists() and done_ids:
            with open(out_path) as f:
                contexts = json.load(f)

            for ctx in contexts:
                pair_key = (ctx["citing_id"], ctx["refid"])
                seen_pairs[pair_key] = seen_pairs.get(pair_key, 0) + 1

            print(f"Resuming — {len(done_ids)} papers done, {len(contexts)} contexts loaded")

        if pairs_path.exists():
            print("Found cached intra_pairs, skipping Phase 1...")

            with open(pairs_path) as f:
                intra_pairs = json.load(f)
        else:
            print("Phase 1: finding intra-corpus citation pairs...")

            intra_pairs: dict[str, dict] = {}
            s2_ids = list(arxiv_to_s2.values())

            for chunk in tqdm(list(self._chunked(s2_ids, 500)), desc="Batch fetching citation links"):
                for attempt in range(3):
                    try:
                        resp = requests.post(
                            f"{BASE}/paper/batch",
                            headers=HEADERS,
                            params={"fields": "paperId,citations.paperId,citations.externalIds"},
                            json={"ids": chunk}
                        )

                        if resp.status_code == 429:
                            time.sleep(int(resp.headers.get("Retry-After", 10)))
                            continue

                        elif resp.status_code != 200:
                            print(f"Batch error {resp.status_code}: {resp.text[:200]}")
                            time.sleep(5)
                            continue

                        for paper in resp.json():
                            if not paper:
                                continue

                            cited_s2  = paper.get("paperId", "")
                            if not cited_s2:
                                continue

                            citations = paper.get("citations", [])
                            needs_full_fetch = len(citations) >= 1000

                            for citation in citations:
                                citing_s2 = citation.get("paperId", "")

                                if citing_s2 not in corpus_s2_set:
                                    continue

                                citing_arxiv = s2_to_arxiv.get(citing_s2)

                                if not citing_arxiv:
                                    continue

                                if cited_s2 not in intra_pairs:
                                    intra_pairs[cited_s2] = {
                                        "citing": [],
                                        "needs_full_fetch": needs_full_fetch
                                    }

                                intra_pairs[cited_s2]["citing"].append(citing_arxiv)

                        break

                    except Exception as e:
                        print(f"  Attempt {attempt+1}/3 error: {e}")
                        time.sleep(5 * (attempt + 1))

                time.sleep(1.1)

            with open(pairs_path, "w") as f:
                json.dump(intra_pairs, f)

            print(f"Found {sum(len(v['citing']) for v in intra_pairs.values())} intra-corpus pairs across {len(intra_pairs)} cited papers")

        print("Phase 2: fetching citation contexts...")

        for cited_s2, pair_data in tqdm(intra_pairs.items(), desc="Fetching contexts"):
            if cited_s2 in done_ids:
                continue

            cited_arxiv = s2_to_arxiv.get(cited_s2)
            if not cited_arxiv:
                continue

            citing_set = set(pair_data["citing"])
            needs_full_fetch = pair_data["needs_full_fetch"]
            offset = 0
            limit = 1000

            while True:
                success = False
                for attempt in range(3):
                    try:
                        resp = requests.get(
                            f"{BASE}/paper/{cited_s2}/citations",
                            headers=HEADERS,
                            params={
                                "fields": "paperId,externalIds,contexts,intents",
                                "limit": limit,
                                "offset": offset
                            }
                        )
                        if resp.status_code == 429:
                            time.sleep(int(resp.headers.get("Retry-After", 10)))
                            continue
                        elif resp.status_code != 200:
                            print(f"Error {resp.status_code} for {cited_arxiv}")
                            break

                        data = resp.json()
                        items = data.get("data", [])

                        for item in items:
                            citing_paper = item.get("citingPaper", {})
                            ext = citing_paper.get("externalIds") or {}
                            citing_arxiv = ext.get("ArXiv", "").strip()

                            if needs_full_fetch:
                                if citing_arxiv not in arxiv_id_set:
                                    continue
                            else:
                                if citing_arxiv not in citing_set:
                                    continue

                            for sentence in item.get("contexts", []):
                                pair_key = (citing_arxiv, cited_arxiv)
                                idx = seen_pairs.get(pair_key, 0)
                                seen_pairs[pair_key] = idx + 1
                                
                                masked = self._normalize_context(sentence, target_position=idx)
                                if "TARGETCIT" not in masked:
                                    continue
                                
                                contexts.append({
                                    "masked_text": masked,
                                    "context_id": f"{citing_arxiv}_{cited_arxiv}_{idx}",
                                    "citing_id": citing_arxiv,
                                    "refid": cited_arxiv
                                })

                        if len(items) < limit:
                            offset = -1
                        else:
                            offset += limit

                        success = True
                        break

                    except Exception as e:
                        print(f"  Attempt {attempt+1}/3 error: {e}")
                        time.sleep(5 * (attempt + 1))

                if not success or offset == -1:
                    break

                time.sleep(1.1)

            done_ids.add(cited_s2)

            if len(done_ids) % 500 == 0:
                with open(out_path, "w") as f:
                    json.dump(contexts, f)
                with open(done_path, "w") as f:
                    json.dump(list(done_ids), f)
                print(f"  Checkpoint: {len(contexts)} contexts, {len(done_ids)} papers done")

            time.sleep(1.1)

        with open(out_path, "w") as f:
            json.dump(contexts, f, indent=2)
            
        with open(done_path, "w") as f:
            json.dump(list(done_ids), f)

        return contexts

    def _create_contexts(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            papers = json.load(f)["root"]

        all_arxiv_ids = list(papers.keys())
        arxiv_id_set  = set(all_arxiv_ids)
        print(f"Loaded {len(all_arxiv_ids)} papers")

        mapping_path = DATA_DIR / "arxiv_to_s2.json"
        if mapping_path.exists():
            print("Found cached arXiv -> S2 mapping, loading...")
            with open(mapping_path) as f:
                arxiv_to_s2 = json.load(f)
        else:
            print("Building arXiv -> S2 mapping via batch API...")
            arxiv_to_s2 = self._batch_map_arxiv_to_s2(all_arxiv_ids)
            with open(mapping_path, "w") as f:
                json.dump(arxiv_to_s2, f, indent=2)

        print("Fetching citations via batch API...")
        contexts = self._batch_fetch_citations(arxiv_to_s2, arxiv_id_set)

        out_path = DATA_DIR / "contexts.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(contexts, f, indent=2)

        print(f"\nDone! {len(contexts)} contexts saved to {out_path}")
        return contexts

if __name__ == "__main__":
    data_path = DATA_DIR / "papers.json"
    creator = ContextCreator(data_path)

    creator._create_contexts() 