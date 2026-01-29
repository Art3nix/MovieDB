from moviedb.extensions import db
from moviedb.models.movie import Movie
from .utils import tsv_rows


def import_movies(path: str):
    basics = f"{path}/title.basics.tsv"

    batch = []
    session = db.session
    session.autoflush = False

    for row in tsv_rows(basics):
        (
            imdb_id,
            title_type,
            primary_title,
            _,
            _,
            year,
            _,
            runtime,
            _
        ) = row

        if title_type != "movie":
            continue
        if year == "\\N" or runtime == "\\N":
            continue

        movie = Movie(
            title=primary_title,
            release_year=int(year),
            runtime=runtime,
            summary="",
            poster_path="",
            imdb_rating=0.0,
            imdb_votes=0,
        )
        movie.imdb_id = imdb_id

        batch.append(movie)

        if len(batch) >= 1000:
            session.bulk_save_objects(batch)
            batch.clear()

    if batch:
        session.bulk_save_objects(batch)

    session.commit()
