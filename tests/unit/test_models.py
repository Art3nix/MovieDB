"""Module testing models."""

from datetime import datetime

from semwork.extensions import bcrypt


def test_user(new_user):
    """Test user model."""

    assert new_user.username == 'TestClient'
    assert new_user.password != 'TestPasswd'
    assert bcrypt.check_password_hash(new_user.password, 'TestPasswd')
    assert repr(new_user) == '<User TestClient>'


def test_movie(new_movie):
    """Test movie model."""

    assert new_movie.name == 'Gekijô-ban: Air/Magokoro'
    assert new_movie.unaccented_name == 'Gekijo-ban: Air/Magokoro'
    assert new_movie.poster_link == 'https://testPoster.com'
    assert new_movie.release_year == 1994
    assert new_movie.runtime == '142 min'
    assert new_movie.genre == 'Action, Drama, Fantasy'
    assert new_movie.imdb_rating == 9.3
    assert new_movie.summary == 'Long story short...'
    assert new_movie.director == 'Frank Darabont'
    assert new_movie.star1 == 'Tim Robbins'
    assert new_movie.star2 == 'Morgan Freeman'
    assert new_movie.star3 == 'Bob Gunton'
    assert new_movie.star4 == 'William Sadler'
    assert new_movie.no_of_votes == 2343110
    assert repr(new_movie) == (
        '<Movie Gekijô-ban: Air/Magokoro>'
        ' Gekijo-ban: Air/Magokoro'
        ' https://testPoster.com'
        ' 1994'
        ' 142 min'
        ' Action, Drama, Fantasy'
        ' 9.3'
        ' Long story short...'
        ' Frank Darabont'
        ' Tim Robbins'
        ' Morgan Freeman'
        ' Bob Gunton'
        ' William Sadler'
        ' 2343110'
    )


def test_watch_list(new_watch_list):
    """Test WatchList model."""

    new_watch_list.id = 1
    assert new_watch_list.user_id == 1
    assert new_watch_list.movie_id == 1
    assert new_watch_list.date_watched == datetime.strptime(
        '2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S'
    )
    assert (
        repr(new_watch_list)
        == '<Watchlist 1> User: 1 Movie: 1 Date watched: 2024-02-01 00:00:00'
    )


def test_watch_later(new_watch_later):
    """Test WatchLater model."""

    new_watch_later.id = 1
    assert new_watch_later.user_id == 1
    assert new_watch_later.movie_id == 1
    assert repr(new_watch_later) == '<Watchlater 1> User: 1 Movie: 1'
