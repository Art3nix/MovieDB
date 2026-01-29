# importers/movie_genres.py
from moviedb.extensions import db
from moviedb.models import Movie, Genre, MovieGenre
from .utils import tsv_rows, preload_map


def import_movie_genres(path: str):
    basics = f"{path}/title.basics.tsv"

    movie_map = preload_map(Movie, Movie.imdb_id, Movie.id)
    genre_map = preload_map(Genre, Genre.name, Genre.id)

    inserts = []

    for row in tsv_rows(basics):
        imdb_id = row[0]
        genres = row[8]

        movie_id = movie_map.get(imdb_id)
        if not movie_id or genres == "\\N":
            continue

        for genre_name in genres.split(","):
            genre_id = genre_map.get(genre_name)
            if genre_id:
                inserts.append(
                    MovieGenre(
                        movie_id=movie_id,
                        genre_id=genre_id,
                    )
                )

        if len(inserts) >= 5000:
            db.session.bulk_save_objects(inserts)
            inserts.clear()

    if inserts:
        db.session.bulk_save_objects(inserts)

    db.session.commit()
