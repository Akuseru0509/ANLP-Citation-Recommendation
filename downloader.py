# Script to download the arXiv Dataset from Kaggle

import kagglehub
import os

kagglehub.login()

if not os.path.exist("data"):
    os.makedirs("data")

path = kagglehub.dataset_download("Cornell-University/arxiv", output_dir="data")

print("Dataset downloaded successfully")
print(f"Dataset located at: {path}")