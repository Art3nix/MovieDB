from moviedb.extensions import db
from moviedb.models import Movie
from .utils import tsv_rows, preload_map


def import_certificates(path: str):
    akas = f"{path}/title.akas.tsv"

    movie_map = preload_map(Movie, Movie.imdb_id, Movie.id)

    updates = {}
    allowed = {"G", "PG", "PG-13", "R", "NC-17", "TV-MA", "TV-14"}

    for row in tsv_rows(akas):
        imdb_id = row[0]
        region = row[3]
        attributes = row[7]

        if region != "US" or attributes == "\\N":
            continue

        movie_id = movie_map.get(imdb_id)
        if not movie_id or movie_id in updates:
            continue

        for rating in attributes.split(","):
            if rating in allowed:
                updates[movie_id] = rating
                break

    db.session.bulk_update_mappings(
        Movie,
        [{"id": mid, "certificate": cert} for mid, cert in updates.items()]
    )

    db.session.commit()
