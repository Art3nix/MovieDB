from moviedb.extensions import db
from moviedb.models.person import Person
from moviedb.models.movie import Movie
from .utils import tsv_rows, safe_int


def import_people(path: str):
    names = f"{path}/name.basics.tsv"

    movie_ids = set(
        db.session.query(Movie.imdb_id).all()
    )

    needed_people = collect_used_people(path, movie_ids)

    session = db.session
    session.autoflush = False
    batch = []

    for imdb_id, name, birth, death, _, _ in tsv_rows(names):
        if imdb_id not in needed_people:
            continue

        batch.append(
            Person(
                imdb_id=imdb_id,
                name=name,
                birth_year=safe_int(birth),
                death_year=safe_int(death),
            )
        )

        if len(batch) >= 5000:
            session.bulk_save_objects(batch)
            batch.clear()

    if batch:
        session.bulk_save_objects(batch)

    session.commit()

def collect_used_people(path: str, movie_imdb_ids: set[str]) -> set[str]:
    people = set()

    principals = f"{path}/title.principals.tsv"
    crew = f"{path}/title.crew.tsv"

    for imdb_id, _, person_id, *_ in tsv_rows(principals):
        if imdb_id in movie_imdb_ids:
            people.add(person_id)

    for imdb_id, directors, writers in tsv_rows(crew):
        if imdb_id in movie_imdb_ids:
            if directors != "\\N":
                people.update(directors.split(","))
            if writers != "\\N":
                people.update(writers.split(","))

    return people
