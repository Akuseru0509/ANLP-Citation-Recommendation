from pathlib import Path
import polars as pl
from tqdm import tqdm
import json

# import nltk
# nltk.download('punkt')

from nltk.tokenize import sent_tokenize
from sklearn.model_selection import train_test_split

from src.backend.db.chroma import collection

BASE_DIR = Path(__file__).parents[0].parents[0].parents[0].resolve()
DATA_DIR = BASE_DIR / "data"

class DataProcessor():
    def __init__(self, data_path):
        self.data_path = data_path

    def _process(self) -> pl.DataFrame:
        try:
            def get_year(arxiv_id):
                if "/" in arxiv_id:
                    yy = int(arxiv_id.split("/")[1][:2])

                    if yy >= 90:
                        return 1900 + yy
                    return 2000 + yy

                return 2000 + int(arxiv_id[:2])

            df = pl.scan_ndjson(
                self.data_path
            ).select(
                pl.col(["id", "authors", "abstract", "title", "categories"])
            ).drop_nulls().with_columns(
                pl.col("id").map_elements(
                    lambda x: get_year(x),
                    return_dtype=pl.Int16    
                ).alias("year")
            ).with_columns(
                pl.col("categories").str.split(" ").alias("splitted_categories")
            ).with_columns(
                pl.lit(0, dtype=pl.Int16).alias("ratings")
            ).filter(
                (pl.col("year") >= 2015) & (pl.col("year") <= 2026)
            ).filter(
                pl.col("splitted_categories").list.eval(
                    pl.element().str.starts_with("cs.")
                ).list.any()
            ).collect()

            return df
        except FileNotFoundError:
            raise ValueError(f"[ERROR]: No file at {self.data_path}")
        
    def _split(self, df: pl.DataFrame):
        try:
            pdf = df.to_pandas()

            train, test = train_test_split(
                pdf,
                test_size=0.05,
                stratify=pdf["year"],
                random_state=42
            )

            return pl.from_pandas(test)

        except Exception as e:
            raise ValueError(f"[ERROR]: {e}")

    def _create_papers(self, df):
        try:
            def get_year_month(arxiv_id: str):
                if "/" in arxiv_id:
                    part = arxiv_id.split("/")[1]

                    yy = int(part[:2])
                    mm = int(part[2:4])

                    year = 1900 + yy if yy >= 90 else 2000 + yy

                    return {
                        "year": year,
                        "month": mm
                    }

                return {
                    "year": 2000 + int(arxiv_id[:2]),
                    "month": int(arxiv_id[2:4])
                }

            df = (
                df
                .select(
                    pl.col(["id", "authors", "abstract", "title"])
                )
                .with_columns(
                    pl.col("authors").map_elements(
                        lambda x: x.strip().split(","),
                        return_dtype=pl.List(pl.String)
                    )
                )
                .with_columns(
                    pl.lit("ArXiv").alias("venue"),
                    pl.lit("").alias("venueType")
                )
                .with_columns(
                    pl.col("id").map_elements(
                        get_year_month,
                        return_dtype=pl.Struct({
                            "year": pl.Int16,
                            "month": pl.Int8
                        })
                    ).alias("date")
                )
                .unnest("date")
                .filter(
                    (pl.col("year") >= 2015) & (pl.col("year") <= 2026)
                )
            )

            rows = df.to_dicts()

            result = {
                row["id"]: row
                for row in tqdm(rows, desc="Building JSON")
                if row["id"] is not None
            }

            final_json = {
                "root": result
            }

            output_path = DATA_DIR / "papers.json"

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(final_json, f, indent=2)
        except FileNotFoundError:
            raise ValueError(f"Error: No file found at {self.data_path}")
        except Exception as e:
            raise ValueError(f"Error: {e}")    
        
    def _add_to_db(self, df: pl.DataFrame):
        try:
            BATCH_SIZE = 1000
            for start in tqdm(range(0, len(df), BATCH_SIZE), desc="Inserting..."):
                batch = df.slice(start, BATCH_SIZE)

                documents = batch.select(
                    pl.concat_str(
                        ["title", "abstract"],
                        separator=" "
                    ).alias("document")
                )["document"].to_list()

                ids = batch["id"].cast(pl.String).to_list()

                metadatas = (
                    batch.select(
                        ["title", "abstract", "year", "authors", "categories", "ratings"]
                    ).to_dicts()
                )

                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
        except Exception as e:
            raise ValueError(f"[ERROR]: {e}")
        
    def _train_test_split(self, df):
        try:
            pdf = df.to_pandas()

            train, test = train_test_split(
                pdf,
                test_size=0.2,
                stratify=pdf["year"],
                random_state=42
            )

            train_df = pl.from_pandas(train)
            test_df = pl.from_pandas(test)

            train_df.write_json(DATA_DIR / "train_metadata.json")
            test_df.write_json(DATA_DIR / "test_metadata.json")
        except Exception as e:
            raise ValueError(f"Error: {e}")

if __name__ == "__main__":
    DATA_PATH = DATA_DIR / "arxiv-metadata-oai-snapshot.json"
    print("[INFO]: Initializing DataProcessor Instance...")
    processor = DataProcessor(DATA_PATH)

    print("[INFO]: Preprocessing Data...")
    df = processor._process()

    print("[INFO]: Splitting Data...")
    df = processor._split(df)

    print("[INFO]: Split to train/test...")
    processor._train_test_split(df)

    print("[INFO]: Creating papers.json")
    processor._create_papers(df)

    print("[INFO]: Adding To Vector Database...")
    processor._add_to_db(df)