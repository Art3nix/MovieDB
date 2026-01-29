"""Importer for scraped dataset containing movie details from TMDb."""

from moviedb.extensions import db
from moviedb.models.movie import Movie
from .utils import tsv_rows, preload_map


def import_movie_details(path: str):
    details = f"{path}/tmdb_results.tsv"

    session = db.session
    session.autoflush = False

    # preload imdb_id -> movie_id
    movie_map = preload_map(Movie, Movie.imdb_id, Movie.id)

    updates = []

    for row in tsv_rows(details):
        imdb_id, tmdb_id, poster_url, summary = row

        movie_id = movie_map.get(imdb_id)
        if not movie_id:
            continue

        updates.append({
            "id": movie_id,
            "tmdb_id": int(tmdb_id) if tmdb_id else None,
            "poster_path": poster_url or "",
            "summary": summary or "",
        })

        if len(updates) >= 5000:
            session.bulk_update_mappings(Movie, updates)
            updates.clear()

    if updates:
        session.bulk_update_mappings(Movie, updates)

    session.commit()
