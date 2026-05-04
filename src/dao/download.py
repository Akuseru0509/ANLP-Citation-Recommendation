from pathlib import Path
import kagglehub
import subprocess

BASE_DIR = Path(__file__).parents[0].parents[0].parents[0].resolve()
DATA_DIR = BASE_DIR / "data"

def download_dataset(data_path):
    try:
        print(f"[INFO] Downloading to {data_path}...")
        path = kagglehub.dataset_download("Cornell-University/arxiv", output_dir=DATA_DIR, force_download=True)
        
        print(f"[INFO] Success! Path to data file: {path}")
    except FileNotFoundError:
        raise ValueError(f"Error finding file at {data_path}")

if __name__ == "__main__":
    download_dataset(DATA_DIR)