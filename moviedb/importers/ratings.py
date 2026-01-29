from moviedb.models import Movie
from moviedb.extensions import db
from .utils import tsv_rows, preload_map


def import_ratings(path: str):
    ratings = f"{path}/title.ratings.tsv"

    movie_map = preload_map(Movie, Movie.imdb_id, Movie.id)

    updates = []

    for imdb_id, rating, votes in tsv_rows(ratings):
        movie_id = movie_map.get(imdb_id)
        if not movie_id:
            continue

        updates.append({
            "id": movie_id,
            "imdb_rating": float(rating),
            "imdb_votes": int(votes),
        })

        if len(updates) >= 5000:
            db.session.bulk_update_mappings(Movie, updates)
            updates.clear()

    if updates:
        db.session.bulk_update_mappings(Movie, updates)

    db.session.commit()
