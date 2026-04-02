# Script to download the arXiv Dataset from Kaggle

import kagglehub
import os
from pathlib import Path

BASE_DIR = Path(__file__).parents[0].resolve()
DATA_DIR = BASE_DIR / "data" / "arxiv"

kagglehub.login()

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

path = kagglehub.dataset_download("Cornell-University/arxiv", output_dir=DATA_DIR, force_download=True)

print("Dataset downloaded successfully")
print(f"Dataset located at: {path}")