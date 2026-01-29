from moviedb.extensions import db
from moviedb.models.genre import Genre
from .utils import tsv_rows


def import_genres(path: str):
    basics = f"{path}/title.basics.tsv"
    genre_names = set()

    for row in tsv_rows(basics):
        genres = row[8]
        if genres != "\\N":
            genre_names.update(genres.split(","))

    for name in genre_names:
        db.session.merge(Genre(name=name))

    db.session.commit()
