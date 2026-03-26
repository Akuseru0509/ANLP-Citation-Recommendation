from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl

# If you're using your personal device, running this file might cause cancer to your Laptop/PC.
# Please consider this as a prototype to the actual Kaggle notebook.
# Link: (to be updated)

BASE_DIR = Path(__file__).parents[0].parents[0].parents[0].resolve()
DATA_DIR = BASE_DIR / "data"

class Preprocessor:
    def __init__(self, data_path):
        self.data_path = data_path
        self.cache = {}

    def _load_data(self) -> pd.DataFrame:
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
            ).collect()

            self.cache[self.data_path] = df

            print(df.head())

            return df

        except FileNotFoundError:
            raise ValueError(f"Can't found input data at {self.data_path}")

    def _preprocess(self) -> np.ndarray:
        if not self.cache[self.data_path]:
            raise ValueError("Nothing inside {self.data_path}")
        
        try:
            pass
        except Exception:
            raise ValueError(f"Error when preprocessing data: {self.data_path}")

        
if __name__ == "__main__":
    data_path = DATA_DIR / "arxiv-metadata-oai-snapshot.json"
    preprocessor = Preprocessor(data_path)

    df = preprocessor._load_data()
    # np_array = preprocessor._preprocess()

    # print(np_array.shape)
