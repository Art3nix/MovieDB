"""Module testing models."""

from datetime import datetime

from moviedb.extensions import bcrypt


def test_user(new_user):
    """Test user model."""

    assert new_user.username == 'TestClient'
    assert new_user.password != 'TestPasswd'
    assert bcrypt.check_password_hash(new_user.password, 'TestPasswd')


def test_movie(new_movie):
    """Test movie model."""

    assert new_movie.title == 'Gekijô-ban: Air/Magokoro'
    assert new_movie.unaccented_title == 'Gekijo-ban: Air/Magokoro'
    assert new_movie.release_year == 1994
    assert new_movie.runtime == '142 min'
    assert new_movie.summary == 'Long story short...'
    assert new_movie.poster_path == 'https://testPoster.com'
    assert new_movie.imdb_rating == 9.3
    assert new_movie.imdb_votes == 2343110


def test_watch_list(new_watch_history):
    """Test WatchList model."""

    new_watch_history.id = 1
    assert new_watch_history.user_id == 1
    assert new_watch_history.movie_id == 1
    assert new_watch_history.date_watched == datetime.strptime(
        '2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S'
    )


def test_watch_later(new_watch_later):
    """Test WatchLater model."""

    new_watch_later.id = 1
    assert new_watch_later.user_id == 1
    assert new_watch_later.movie_id == 1
