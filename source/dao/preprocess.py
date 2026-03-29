import json
import polars as pl
import numpy as np
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from tqdm import tqdm

model = "all-MiniLM-L6-v2"
sentence_model = SentenceTransformer(model, device="cuda")

kw_model = KeyBERT(model=sentence_model)


# Please note that on the actual notebook, we use GPU to accelerate the process -> we load model and dataframe to gpu.
# If you're using your personal device, running this file might cause problems.
# Please consider this as a prototype, compared to the actual Kaggle notebook.
# Link: https://www.kaggle.com/code/akuseru59/arxiv

BASE_DIR = Path(__file__).parents[0].parents[0].parents[0].resolve()
DATA_DIR = BASE_DIR / "data"

class Preprocessor:
    def __init__(self, data_path):
        self.data_path = data_path
        self.cache = {}

    def _load_data(self) -> pl.DataFrame:
        if not self.data_path:
            raise ValueError(f"{self.data_path} is empty!")
        
        if self.data_path in self.cache:
            return self.cache[self.data_path]

        try:
            df = pl.scan_ndjson(
                self.data_path,
                batch_size=64,
                low_memory=True,
                ignore_errors=True,
            ).collect(engine="gpu").drop_nulls()

            self.cache[self.data_path] = df

            return df

        except FileNotFoundError:
            raise ValueError(f"Can't found input data at {self.data_path}")

    def _preprocess(self, df: pl.DataFrame) -> np.ndarray:
        if self.cache[self.data_path].is_empty():
            raise ValueError(f"Nothing inside {self.data_path}")
        
        try:
            # Lấy id, title, authors_parsed, update_date, abtract, doi
            # Filter df và lấy năm từ 2015 - 2026
            # Với mỗi id, dùng KeyBERT để extract keywords
            # return DataFrame chứa các thông tin trên + keywords (độ dài 1-3)

            # Loại bỏ những cột không cần thiết
            cols_to_drop = ["submitter", "authors", "comments", "journal-ref", "report-no", "categories", "license", "versions"]
            existing_cols_to_drop = [col for col in cols_to_drop if col in df.columns]
            filtered_df = df.drop(existing_cols_to_drop)
            
            # Lọc những dòng không thuộc năm 2015 - 2026
            filtered_df = filtered_df.with_columns(
                pl.col("update_date").str.to_date(strict=False) 
            ).filter(
                pl.col("update_date").dt.year().is_between(2015, 2026)
            )

            def join_author(parsed_authors: list[list[str]]) -> list[str]:
                result = []
                for author in parsed_authors:
                    result.append(" ".join(author))

                return result
                
            # Với mỗi parsed_author -> Chuyển list[list[str]] -> list[str]
            filtered_df = filtered_df.with_columns(
                pl.col("authors_parsed").map_elements(
                    join_author,
                    return_dtype=pl.List(pl.String)
                )
            )

            keywords = []

            # Dựa theo ví dụ của KeyBERT, không cần normalize/bỏ punctuations 
            for row in tqdm(filtered_df.iter_rows(named=True), total=filtered_df.height):
                keyword = kw_model.extract_keywords(
                    row["abstract"],
                    keyphrase_ngram_range=(1,3),
                    stop_words='english',
                )
                
                keywords.append([kw[0] for kw in keyword])
            
            filtered_df = filtered_df.with_columns(
                    key_words = pl.Series(keywords)
                ).with_columns(
                    pl.col("authors_parsed").map_elements(
                        lambda x: ", ".join(x), 
                        return_dtype=pl.String)
                ).with_columns(
                    pl.col("key_words").map_elements(
                        lambda x: ", ".join(x), 
                        return_dtype=pl.String
                    )
                )

            print(filtered_df.head())

            return filtered_df
        except Exception:
            raise ValueError(f"Error when preprocessing data: {self.data_path}")

        
if __name__ == "__main__":
    data_path = DATA_DIR / "arxiv-metadata-oai-snapshot.json"
    output_path = DATA_DIR / "processed.csv"
    preprocessor = Preprocessor(data_path)

    df = preprocessor._load_data()
    filtered_df = preprocessor._preprocess(df)

    filtered_df.write_csv(output_path)
