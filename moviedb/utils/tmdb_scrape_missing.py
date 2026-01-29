
import os
from dotenv import load_dotenv
import csv
import aiohttp
import asyncio
import random

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3/find/"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

OUTPUT_FILE = "tmdb_results.tsv"
INPUT_FILE = "title.basics.tsv"

CONCURRENCY = 25
MAX_RETRIES = 5
BASE_DELAY = 1.5


# -------------------------
# Load already processed IDs
# -------------------------

def load_existing():
    existing = {}
    if not os.path.exists(OUTPUT_FILE):
        return existing

    with open(OUTPUT_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            existing[row["imdb_id"]] = row["tmdb_id"]

    return existing


# -------------------------
# TMDB fetch with retry
# -------------------------

async def fetch(session, imdb_id):
    url = f"{BASE_URL}{imdb_id}"
    params = {"api_key": API_KEY, "external_source": "imdb_id"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, params=params) as r:

                if r.status == 429:
                    wait = BASE_DELAY * (2 ** (attempt - 1)) + random.random()
                    await asyncio.sleep(wait)
                    continue

                if r.status != 200:
                    return None

                data = await r.json()

                result = None
                if data.get("movie_results"):
                    result = data["movie_results"][0]
                elif data.get("tv_results"):
                    result = data["tv_results"][0]

                if result:
                    return [
                        imdb_id,
                        result["id"],
                        IMG_BASE + result["poster_path"] if result.get("poster_path") else "",
                        result.get("overview", "").replace("\n", " ")
                    ]

                return None

        except:
            await asyncio.sleep(BASE_DELAY)

    return None


# -------------------------
# Collect missing IMDb IDs
# -------------------------

def get_missing(existing):
    missing = []

    with open(INPUT_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            if row["titleType"] != "movie":
                continue
            if row["startYear"] == "\\N" or row["runtimeMinutes"] == "\\N":
                continue

            imdb_id = row["tconst"]

            # missing or blank in output
            if imdb_id not in existing or not existing[imdb_id]:
                missing.append(imdb_id)

    return missing


# -------------------------
# Retry and append
# -------------------------

async def main():
    existing = load_existing()
    missing = get_missing(existing)

    print(f"Retrying {len(missing)} missing movies...")

    if not missing:
        print("Nothing to retry")
        return

    connector = aiohttp.TCPConnector(limit=CONCURRENCY)

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as out:
        writer = csv.writer(out, delimiter="\t")

        async with aiohttp.ClientSession(connector=connector) as session:

            tasks = []

            for imdb_id in missing:
                tasks.append(fetch(session, imdb_id))

                if len(tasks) >= 3000:
                    results = await asyncio.gather(*tasks)
                    tasks.clear()

                    for row in results:
                        if row:
                            writer.writerow(row)

                    print("Appended batch...")

            if tasks:
                results = await asyncio.gather(*tasks)
                for row in results:
                    if row:
                        writer.writerow(row)

    print("Retry pass finished!")


if __name__ == "__main__":
    asyncio.run(main())
