"""Module testing importing."""

from moviedb.import_data import load_dataset
from moviedb.extensions import db
from moviedb.models.movie import Movie


def test_load_dataset(test_client):
    """Test movies dataset importing."""

    with test_client.application.app_context():
        load_dataset(db, 'tests/test_dataset.csv')
        try:
            assert db.session.query(Movie).filter_by(title='Movie 1').count() > 0
            assert (
                db.session.query(Movie)
                .filter_by(
                    title='Movie 2',
                    unaccented_title='Movie 2',
                    release_year=2002,
                    runtime='90 min',
                    summary='Quick summary of the movie',
                    poster_path='https://link-to-movie-2.com',
                    certificate='UA',
                    imdb_rating=7.9,
                    meta_score=80,
                    imdb_votes=2343110,
                    gross_earned=28341469,
                )
                .count()
                > 0
            )
            assert (
                db.session.query(Movie)
                .filter(Movie.poster_path.ilike('%https://link-to-movie-%'))
                .count()
                == 9
            )
        finally:
            db.session.query(Movie).filter(
                Movie.poster_path.ilike('%https://link-to-movie-%')
            ).delete()
            db.session.commit()
