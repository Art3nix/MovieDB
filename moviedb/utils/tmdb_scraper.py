import os
import random
from dotenv import load_dotenv
import csv
import aiohttp
import asyncio
from tqdm import tqdm


load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3/find/"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

OUTPUT_FILE = "tmdb_results.tsv"

CONCURRENCY = 40
BATCH_SIZE = 5000

MAX_RETRIES = 5
BASE_DELAY = 1.5   # seconds


async def fetch(session, imdb_id):
    url = f"{BASE_URL}{imdb_id}"
    params = {
        "api_key": API_KEY,
        "external_source": "imdb_id"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, params=params, timeout=20) as r:

                # Rate limited
                if r.status == 429:
                    wait = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    print(f"429 on {imdb_id} → retrying in {wait:.1f}s (attempt {attempt})")
                    await asyncio.sleep(wait)
                    continue

                if r.status != 200:
                    print(f"HTTP {r.status} on {imdb_id}")
                    return [imdb_id, "", "", ""]

                data = await r.json()

                if data.get("movie_results"):
                    movie = data["movie_results"][0]
                    return [
                        imdb_id,
                        movie["id"],
                        IMG_BASE + movie["poster_path"] if movie["poster_path"] else "",
                        movie["overview"].replace("\n", " ")
                    ]

                return [imdb_id, "", "", ""]

        except Exception as e:
            wait = BASE_DELAY * (2 ** (attempt - 1))
            print(f"Error {imdb_id}: {e} → retry in {wait:.1f}s")
            await asyncio.sleep(wait)

    print(f"Failed after retries: {imdb_id}")
    return [imdb_id, "", "", ""]


async def process_batch(session, batch, writer):
    tasks = [fetch(session, imdb_id) for imdb_id in batch]
    results = await asyncio.gather(*tasks)

    for row in results:
        writer.writerow(row)


async def main():
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    timeout = aiohttp.ClientTimeout(total=30)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out, delimiter="\t")
        writer.writerow(["imdb_id", "tmdb_id", "poster_url", "summary"])

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

            batch = []
            processed = 0

            with open("datasets/imdb/title.basics.tsv", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")

                for row in reader:
                    title_type = row["titleType"]
                    year = row["startYear"]
                    runtime = row["runtimeMinutes"]

                    if title_type != "movie":
                        continue
                    if year == "\\N" or runtime == "\\N":
                        continue

                    batch.append(row["tconst"])

                    if len(batch) >= BATCH_SIZE:
                        await process_batch(session, batch, writer)
                        processed += len(batch)
                        print(f"Processed {processed} movies...")
                        batch.clear()

                # leftover
                if batch:
                    await process_batch(session, batch, writer)
                    processed += len(batch)

            print("\nDone!")
            print(f"Total movies processed: {processed}")
            print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
