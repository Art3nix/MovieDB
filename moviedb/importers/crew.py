from moviedb.models import Movie, Person, MovieCrew
from moviedb.extensions import db
from .utils import tsv_rows, preload_map


def import_crew(path: str):
    crew_file = f"{path}/title.crew.tsv"

    movie_map = preload_map(Movie, Movie.imdb_id, Movie.id)
    person_map = preload_map(Person, Person.imdb_id, Person.id)

    inserts = []

    for imdb_id, directors, writers in tsv_rows(crew_file):
        movie_id = movie_map.get(imdb_id)
        if not movie_id:
            continue

        for role, people in (("director", directors), ("writer", writers)):
            if people == "\\N":
                continue

            for imdb_person_id in people.split(","):
                person_id = person_map.get(imdb_person_id)
                if person_id:
                    inserts.append(
                        MovieCrew(
                            movie_id=movie_id,
                            person_id=person_id,
                            role=role,
                        )
                    )

        if len(inserts) >= 5000:
            db.session.bulk_save_objects(inserts)
            inserts.clear()

    if inserts:
        db.session.bulk_save_objects(inserts)

    db.session.commit()
