"""Configuration module for pytest."""

from datetime import datetime
import pytest

import config
from moviedb import create_app
from moviedb.models.user import User
from moviedb.models.movie import Movie
from moviedb.models.watch_later import WatchLater
from moviedb.models.watch_history import WatchHistory


@pytest.fixture
def new_user():
    """Fixture for creating new user."""

    user = User(username='TestClient', password='TestPasswd')
    return user


@pytest.fixture
def new_movie():
    """Fixture for creating new movie."""

    movie = Movie(
        title='Gekijô-ban: Air/Magokoro',
        release_year=1994,
        runtime='142 min',
        summary='Long story short...',
        poster_path='https://testPoster.com',
        imdb_rating=9.3,
        imdb_votes=2343110,
    )
    return movie


@pytest.fixture
def new_watch_history():
    """Fixture for creating new watch list movie."""

    watch_history = WatchHistory(
        1, 1, datetime.strptime('2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    )
    return watch_history


@pytest.fixture
def new_watch_later():
    """Fixture for creating new watch later movie."""

    watch_later = WatchLater(1, 1)
    return watch_later


@pytest.fixture
def test_client():
    """Fixture for creating new test app."""

    test_app = create_app(config_class=config.LocalTestingConfig)

    with test_app.test_client() as app_test_client:
        with test_app.app_context():
            yield app_test_client
