"""Configuration module for pytest."""

from datetime import datetime
import pytest

import config
from semwork import create_app
from semwork.models.user import User
from semwork.models.movie import Movie
from semwork.models.watch_later import WatchLater
from semwork.models.watch_list import WatchList


@pytest.fixture
def new_user():
    """Fixture for creating new user."""

    user = User(username='TestClient', password='TestPasswd')
    return user


@pytest.fixture
def new_movie():
    """Fixture for creating new movie."""

    movie = Movie(
        name='Gekijô-ban: Air/Magokoro',
        poster_link='https://testPoster.com',
        release_year=1994,
        runtime='142 min',
        genre='Action, Drama, Fantasy',
        imdb_rating=9.3,
        summary='Long story short...',
        director='Frank Darabont',
        star1='Tim Robbins',
        star2='Morgan Freeman',
        star3='Bob Gunton',
        star4='William Sadler',
        no_of_votes=2343110,
    )
    return movie


@pytest.fixture
def new_watch_list():
    """Fixture for creating new watch list movie."""

    watch_list = WatchList(
        1, 1, datetime.strptime('2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    )
    return watch_list


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
