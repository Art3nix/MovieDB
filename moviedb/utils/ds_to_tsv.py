from datasets import load_dataset
import pandas as pd
import os

HF_DATASET = "HenryWaltson/TMDB-IMDB-Movies-Dataset"
TSV_PATH = "tmdb_imdb_dataset.tsv"


def download_hf_to_tsv(path=TSV_PATH):
    print("Downloading HuggingFace dataset...")

    ds = load_dataset(HF_DATASET, split="train")

    print("Converting to pandas...")
    df = ds.to_pandas()

    print("Saving TSV...")
    df.to_csv(path, sep="\t", index=False)

    print(f"Saved {path}")

    return path


def remove_tsv(path=TSV_PATH):
    if os.path.exists(path):
        os.remove(path)
        print(f"Removed {path}")
