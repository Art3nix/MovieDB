"""Module testing importing."""

from semwork.import_data import load_dataset
from semwork.extensions import db
from semwork.models.movie import Movie


def test_load_dataset(test_client):
    """Test movies dataset importing."""

    with test_client.application.app_context():
        load_dataset(db, 'tests/test_dataset.csv')
        try:
            assert db.session.query(Movie).filter_by(name='Movie 1').count() > 0
            assert (
                db.session.query(Movie)
                .filter_by(
                    name='Movie 2',
                    unaccented_name='Movie 2',
                    poster_link='https://link-to-movie-2.com',
                    release_year=2002,
                    certificate='UA',
                    runtime='90 min',
                    genre='GenreA, GenreB',
                    imdb_rating=7.9,
                    summary='Quick summary of the movie',
                    meta_score=80,
                    director='Christopher Nolan',
                    star1='Arnold Schwarzenegger',
                    star2='Brad Pitt',
                    star3='Michael Caine',
                    star4='Scarlett Johansson',
                    no_of_votes=2343110,
                    gross_earned=28341469,
                )
                .count()
                > 0
            )
            assert (
                db.session.query(Movie)
                .filter(Movie.poster_link.ilike('%https://link-to-movie-%'))
                .count()
                == 9
            )
        finally:
            db.session.query(Movie).filter(
                Movie.poster_link.ilike('%https://link-to-movie-%')
            ).delete()
            db.session.commit()
