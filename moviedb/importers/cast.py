from moviedb.models import Movie, Person, MovieCast
from moviedb.extensions import db
from .utils import tsv_rows, preload_map


def import_cast(path: str):
    principals = f"{path}/title.principals.tsv"

    movie_map = preload_map(Movie, Movie.imdb_id, Movie.id)
    person_map = preload_map(Person, Person.imdb_id, Person.id)

    inserts = []

    for imdb_id, _, person_id, category, ordering, characters in tsv_rows(principals):
        if category not in ("actor", "actress"):
            continue

        movie_id = movie_map.get(imdb_id)
        person_db_id = person_map.get(person_id)

        if not movie_id or not person_db_id:
            continue

        inserts.append(
            MovieCast(
                movie_id=movie_id,
                person_id=person_db_id,
                billing=int(ordering),
                character=None if characters == "\\N" else characters,
            )
        )

        if len(inserts) >= 5000:
            db.session.bulk_save_objects(inserts)
            inserts.clear()

    if inserts:
        db.session.bulk_save_objects(inserts)

    db.session.commit()
