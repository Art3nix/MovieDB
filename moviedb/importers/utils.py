
import os
import csv
import gzip
import shutil
import requests

import os
import gzip
import shutil
import requests

from moviedb.extensions import db

IMDB_BASE = "https://datasets.imdbws.com"


FILES = {
    "basics": "title.basics.tsv.gz",
    "ratings": "title.ratings.tsv.gz",
    "crew": "title.crew.tsv.gz",
    "cast": "title.principals.tsv.gz",
    "people": "name.basics.tsv.gz",
}

def preload_map(model, key_col, value_col):
    """
    Returns dict[key_col -> value_col]
    Example: imdb_id -> movie.id
    """
    return dict(
        db.session.query(key_col, value_col).all()
    )


def tsv_rows(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            yield line.rstrip("\n").split("\t")


def tsv_rows_hf(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quotechar='"')
        for line in reader:
            yield line


def safe_int(value):
    return None if value == "\\N" else int(value)


def safe_str(value):
    return None if value == "\\N" else value


def download_and_extract(filename: str, dest_dir: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)

    gz_path = os.path.join(dest_dir, filename)
    tsv_path = gz_path.replace(".gz", "")

    url = f"{IMDB_BASE}/{filename}"

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(gz_path, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)

    # extract
    with gzip.open(gz_path, "rb") as f_in:
        with open(tsv_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    os.remove(gz_path)

    return tsv_path


def cleanup(path: str):
    if os.path.exists(path):
        os.remove(path)
