import logging
import requests
import os
from dotenv import load_dotenv

from moviedb.extensions import db

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

def refresh_tmdb_data(queried_movie):
    tmdb_data = fetch_tmdb_data(queried_movie.imdb_id)
    if not tmdb_data:
        tmdb_data = search_tmdb_by_title(queried_movie.title, queried_movie.release_year)
    if tmdb_data:
        queried_movie.tmdb_id = tmdb_data.get("tmdb_id") or None
        queried_movie.backdrop_path = tmdb_data.get("backdrop_path") or ""
        queried_movie.language = tmdb_data.get("language") or ""
        queried_movie.summary = tmdb_data.get("summary") or ""
        queried_movie.poster_path = tmdb_data.get("poster_path") or ""
        db.session.commit()

def fetch_tmdb_data(imdb_id: str) -> dict | None:
    """Fetch TMDb movie info by IMDb ID. Raises RuntimeError on rate limit."""
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    params = {"api_key": API_KEY, "external_source": "imdb_id"}

    try:
        resp = requests.get(url, params=params)
        if resp.status_code == 429:  # TMDb rate limit hit
            raise RuntimeError("TMDb rate limit reached")
        resp.raise_for_status()
        results = resp.json().get("movie_results")
        if not results:
            return None
        movie = results[0]
        return {
            "tmdb_id": int(movie["id"]) if movie["id"] else None,
            "backdrop_path": movie["backdrop_path"] or "",
            "language": movie["original_language"] or "",
            "summary": movie["overview"] or "",
            "poster_path": movie["poster_path"] or "",
        }
    except requests.exceptions.HTTPError as e:
        logger.warning(f"TMDb fetch failed for {imdb_id}: {e}")
        return None
    except Exception as e:
        logger.warning(f"TMDb fetch failed for {imdb_id}: {e}")
        return None


def search_tmdb_by_title(title, year):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": API_KEY, "query": title, "year": year}

    try:
        resp = requests.get(url, params=params)
        if resp.status_code == 429:  # TMDb rate limit hit
            raise RuntimeError("TMDb rate limit reached")
        resp.raise_for_status()
        results = resp.json().get("results")
        if not results:
            return None

        for movie in results:
            if movie["title"] == title and int(movie["release_date"].split("-")[0]) == int(year):
                return {
                    "tmdb_id": int(movie["id"]) if movie["id"] else None,
                    "backdrop_path": movie["backdrop_path"] or "",
                    "language": movie["original_language"] or "",
                    "summary": movie["overview"] or "",
                    "poster_path": movie["poster_path"] or "",
                }
    except requests.exceptions.HTTPError as e:
        logger.warning(f"TMDb fetch failed for {title}: {e}")
        return None
    except Exception as e:
        logger.warning(f"TMDb fetch failed for {title}: {e}")
        return None
