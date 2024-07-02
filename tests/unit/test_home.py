"""Module testing home modules."""

from datetime import datetime, timedelta
from flask_login import current_user

from semwork.extensions import db
from semwork.import_data import load_dataset
from semwork.models.movie import Movie
from semwork.models.watch_later import WatchLater
from semwork.models.watch_list import WatchList
from semwork.models.user import User
from semwork.home.services import (
    find_and_calculate_recommendations,
    get_new_recommendations,
    get_watch_again,
)


def test_homepage_access(test_client, new_user, new_movie):
    """Test access to home page."""

    assert db.session.query(User).filter_by(username=new_user.username).first() is None
    db.session.add(new_user)
    assert (
        db.session.query(User).filter_by(username=new_user.username).first() is not None
    )

    # user has to be logged in
    response = test_client.get('/', follow_redirects=True)
    assert response.request.path == '/users/login'

    # log in
    response = test_client.post(
        '/users/login', data={'username': 'TestClient', 'password': 'TestPasswd'}
    )
    assert current_user.username == 'TestClient'

    response = test_client.get('/')
    assert b'<title>Home</title>' in response.data
    assert b'<span>You have no movies to watch.</span>' in response.data
    assert (
        b'<span>There are no movies recommended for you. Try watching some to get recommendations.</span>'
        in response.data
    )
    assert (
        b'<span>There are currently no movies for you to watch again.</span>'
        in response.data
    )

    try:
        db.session.add(new_movie)
        assert (
            db.session.query(Movie).filter_by(poster_link=new_movie.poster_link).first()
            is not None
        )
        db.session.add(WatchLater(user_id=new_user.id, movie_id=new_movie.id))
        assert (
            db.session.query(WatchLater).filter_by(user_id=new_user.id).first()
            is not None
        )
        response = test_client.get('/')
        assert b'<span>You have no movies to watch.</span>' not in response.data

        assert (
            b'<span>There are no movies recommended for you. Try watching some to get recommendations.</span>'
            in response.data
        )
        assert (
            b'<span>There are currently no movies for you to watch again.</span>'
            in response.data
        )
    finally:
        db.session.query(WatchLater).filter_by(user_id=new_user.id).delete()
        db.session.query(Movie).filter_by(id=new_movie.id).delete()
        db.session.query(User).filter_by(username=new_user.username).delete()
        db.session.commit()


def test_find_and_calculate_recommendations(test_client, new_user):
    """Test recommendation calculations."""

    assert db.session.query(User).filter_by(username='TestClient').first() is None

    try:
        # prepare watch history
        load_dataset(db, 'tests/test_dataset.csv')
        db.session.add(new_user)
        _ = test_client.post(
            '/users/login', data={'username': 'TestClient', 'password': 'TestPasswd'}
        )
        assert current_user.username == 'TestClient'
        watch_date = datetime.strptime('2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        movie_ids = dict(db.session.query(Movie.name, Movie.id)
                        .filter(Movie.poster_link.ilike('%https://link-to-movie-%'))
                        .all())

        assert len(movie_ids) == 9

        wh = (
            db.session.query(Movie)
            .where(
                Movie.id.in_(
                    [movie_ids['Movie 1'], movie_ids['Movie 2'], movie_ids['Movie 3']]
                )
            )
            .all()
        )
        assert len(wh) == 3

        # 1 genre
        recommendations = find_and_calculate_recommendations(
            [db.session.query(Movie).filter_by(id=movie_ids['Movie 9']).first()]
        )
        assert {(movie[0].name, movie[1]) for movie in recommendations.all()[:2]} == {
            ('Movie 9', 210),
            ('Movie 7', 177),
        }

        # 2 genres
        recommendations = find_and_calculate_recommendations([wh[0]])
        assert {(movie[0].name, movie[1]) for movie in recommendations.all()[:2]} == {
            ('Movie 1', 210),
            ('Movie 2', 170.5),
        }

        # 3 genres
        recommendations = find_and_calculate_recommendations(wh)

        assert {movie[0].name for movie in recommendations.all()[:3]} == {
            movie.name for movie in wh
        }
        assert {(movie[0].name, movie[1]) for movie in recommendations.all()[:3]} == {
            ('Movie 1', 188.75),
            ('Movie 2', 186.75),
            ('Movie 3', 158),
        }

        db.session.add(WatchList(new_user.id, movie_ids['Movie 1'], watch_date))

        # Movie 1 in watchlist so it should not be recommended
        recommendations = find_and_calculate_recommendations(wh)

        assert 'Movie 1' not in [movie[0].name for movie in recommendations.all()]
        assert {(movie[0].name, movie[1]) for movie in recommendations.all()[:2]} == {
            ('Movie 2', 186.75),
            ('Movie 3', 158),
        }
    finally:
        db.session.query(WatchList).filter_by(user_id=new_user.id).delete()
        db.session.query(Movie).filter(
            Movie.poster_link.ilike('%https://link-to-movie-%')
        ).delete()
        db.session.query(User).filter_by(username=new_user.username).delete()
        db.session.commit()


def test_get_new_recommendations(test_client, new_user):
    """Test retrieving new recommendations."""

    assert db.session.query(User).filter_by(username='TestClient').first() is None

    try:
        # prepare watch history
        load_dataset(db, 'tests/test_dataset.csv')
        db.session.add(new_user)
        _ = test_client.post(
            '/users/login', data={'username': 'TestClient', 'password': 'TestPasswd'}
        )
        assert current_user.username == 'TestClient'
        watch_date = datetime.strptime('2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        movie_ids = dict(db.session.query(Movie.name, Movie.id)
                        .filter(Movie.poster_link.ilike('%https://link-to-movie-%'))
                        .all())

        assert len(movie_ids) == 9

        wh = (
            db.session.query(Movie)
            .where(
                Movie.id.in_(
                    [
                        movie_ids['Movie 1'],
                        movie_ids['Movie 2'],
                        movie_ids['Movie 3'],
                        movie_ids['Movie 4'],
                        movie_ids['Movie 5'],
                    ]
                )
            )
            .all()
        )
        assert len(wh) == 5

        recommendations = get_new_recommendations()
        assert recommendations == []

        for i in range(1, 6):
            db.session.add(WatchList(new_user.id, movie_ids[f'Movie {i}'], watch_date))
            watch_date = watch_date + timedelta(days=1)

        recommendations = get_new_recommendations(maximum=3, recent_limit=0)
        assert len(recommendations) == 0

        recommendations = get_new_recommendations(maximum=0, recent_limit=2)
        assert len(recommendations) == 0

        recommendations = get_new_recommendations(maximum=4, recent_limit=2)
        assert len(recommendations) == 4
        assert {movie[0].name for movie in recommendations} == {
            'Movie 6',
            'Movie 7',
            'Movie 8',
            'Movie 9',
        }
    finally:
        db.session.query(WatchList).filter_by(user_id=new_user.id).delete()
        db.session.query(Movie).filter(
            Movie.poster_link.ilike('%https://link-to-movie-%')
        ).delete()
        db.session.query(User).filter_by(username=new_user.username).delete()
        db.session.commit()


def test_watch_again(test_client, new_user):
    """Test getting movies to watch again."""

    assert db.session.query(User).filter_by(username='TestClient').first() is None

    try:
        # prepare watch history
        load_dataset(db, 'tests/test_dataset.csv')
        db.session.add(new_user)
        _ = test_client.post(
            '/users/login', data={'username': 'TestClient', 'password': 'TestPasswd'}
        )
        assert current_user.username == 'TestClient'
        watch_date = datetime.now() - timedelta(days=30)
        movie_ids = dict(db.session.query(Movie.name, Movie.id)
                        .filter(Movie.poster_link.ilike('%https://link-to-movie-%'))
                        .all())

        assert len(movie_ids) == 9

        watch_again = get_watch_again()
        assert watch_again == []

        # add movies to watch history
        db.session.add(WatchList(new_user.id, movie_ids['Movie 1'], watch_date))
        db.session.add(
            WatchList(new_user.id, movie_ids['Movie 1'], watch_date + timedelta(days=7))
        )
        db.session.add(
            WatchList(new_user.id, movie_ids['Movie 1'], watch_date + timedelta(days=14))
        )
        db.session.add(
            WatchList(new_user.id, movie_ids['Movie 1'], watch_date + timedelta(days=21))
        )
        db.session.add(
            WatchList(new_user.id, movie_ids['Movie 1'], watch_date + timedelta(days=28))
        )
        db.session.add(WatchList(new_user.id, movie_ids['Movie 2'], watch_date))
        db.session.add(
            WatchList(new_user.id, movie_ids['Movie 2'], watch_date + timedelta(days=7))
        )
        db.session.add(
            WatchList(new_user.id, movie_ids['Movie 2'], watch_date + timedelta(days=14))
        )
        db.session.add(
            WatchList(new_user.id, movie_ids['Movie 2'], watch_date + timedelta(days=21))
        )
        db.session.add(WatchList(new_user.id, movie_ids['Movie 3'], watch_date))
        db.session.add(WatchList(new_user.id, movie_ids['Movie 4'], watch_date))
        db.session.add(
            WatchList(new_user.id, movie_ids['Movie 4'], watch_date + timedelta(days=14))
        )

        watch_again = get_watch_again()
        assert len(watch_again) == 2
        assert [movie.name for movie in watch_again] == ['Movie 4', 'Movie 2']
    finally:
        db.session.query(WatchList).filter_by(user_id=new_user.id).delete()
        db.session.query(Movie).filter(
            Movie.poster_link.ilike('%https://link-to-movie-%')
        ).delete()
        db.session.query(User).filter_by(username=new_user.username).delete()
        db.session.commit()
