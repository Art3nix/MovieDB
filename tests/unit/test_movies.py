"""Module testing movies modules."""

from datetime import datetime
import pytest

from flask_login import current_user

from semwork.extensions import db
from semwork.models.movie import Movie
from semwork.models.watch_later import WatchLater
from semwork.models.watch_list import WatchList
from semwork.models.user import User
from semwork.movies.filters import movie_name_to_url, query_empty, in_watch_later


@pytest.mark.parametrize(
    'name, result',
    [
        ('The Inception', 'the-inception'),
        ('Spider-Man: Homecoming', 'spider-man-homecoming'),
        (
            'Tropa de Elite 2: O Inimigo Agora é Outro',
            'tropa-de-elite-2-o-inimigo-agora-e-outro',
        ),
    ],
)
def test_movie_name_to_url(name, result):
    """Test filter transforming movie name to url name."""

    assert movie_name_to_url(name) == result


def test_query_empty(test_client, new_user):
    """Test filter if query returns empty list."""

    with test_client.application.app_context():
        assert (
            db.session.query(User).filter_by(username=new_user.username).first() is None
        )
        db.session.add(new_user)
        assert (
            db.session.query(User).filter_by(username=new_user.username).first()
            is not None
        )

        assert query_empty(db.session.query(User).all()) is False
        assert query_empty(db.session.query(User).filter(False).all())
        assert query_empty(None)


def test_watch_later(test_client, new_movie):
    """Test filter if movie is in user's watch later."""

    assert db.session.query(User).filter_by(username='TestClient').first() is None

    new_user = User(username='TestClient', password='TestPasswd')
    db.session.add(new_user)
    assert (
        db.session.query(User).filter_by(username=new_user.username).first() is not None
    )

    db.session.add(new_movie)
    assert (
        db.session.query(Movie).filter_by(poster_link=new_movie.poster_link).first()
        is not None
    )

    db.session.add(WatchLater(new_user.id, new_movie.id))

    assert (
        in_watch_later(new_movie.id, current_user) is False
    )  # needs to be authenticated to access WatchLater

    # log in
    response = test_client.post(
        '/users/login', data={'username': 'TestClient', 'password': 'TestPasswd'}
    )
    assert current_user.username == 'TestClient'

    assert in_watch_later(new_movie.id, current_user)
    assert in_watch_later(new_movie.id + 1, current_user) is False

    db.session.delete(db.session.query(WatchLater).filter_by(user_id=new_user.id).first())
    assert in_watch_later(new_movie.id, current_user) is False

    try:
        response = test_client.post(
            f'/movies/add-to-watch-list/{new_movie.id}',
            data={
                'datewatched': datetime.strptime(
                    '2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S'
                )
            },
            follow_redirects=True,
        )
        assert (
            b'<span class="w-100 text-success">Added this movie to watch list</span>'
            in response.data
        )

        response = test_client.get('/movies/watch-history', follow_redirects=True)
        assert b'<span>Your Watch history is empty.</span>' not in response.data
        assert (
            f'<h5 class="card-title">{new_movie.name}</h5>'.encode('UTF-8')
            in response.data
        )
    finally:
        # clear all test data
        db.session.query(WatchList).filter_by(user_id=new_user.id).delete()
        db.session.query(User).filter_by(username=new_user.username).delete()
        db.session.query(Movie).filter_by(id=new_movie.id).delete()
        db.session.commit()


def test_browse_movies(test_client):
    """Test browse movies page."""

    response = test_client.get('/movies/browse')
    assert response.status_code == 200
    assert b'<span>No movies are available.</span>' not in response.data

    db.session.query(WatchLater).delete()
    db.session.query(WatchList).delete()
    db.session.query(Movie).delete()

    response = test_client.get('/movies/browse')
    assert response.status_code == 200
    assert b'<span>No movies are available.</span>' in response.data


def test_movie_page(test_client):
    """Test specific movie page."""

    movie = db.session.query(Movie).order_by(Movie.id.desc()).first()
    url_name = movie_name_to_url(movie.name)
    response = test_client.get(f'/movies/movie/{movie.id}-{url_name}')
    assert response.status_code == 200

    response = test_client.get(
        f'/movies/movie/{movie.id + 1}-{url_name}', follow_redirects=True
    )
    assert response.request.path == "/movies/not-found"

    response = test_client.get(
        f'/movies/movie/{movie.id}-{url_name + "wrongName"}', follow_redirects=True
    )
    assert response.request.path == "/movies/not-found"


def test_search_movie(test_client):
    """Test searching for movies."""

    movie = db.session.query(Movie).first()
    response = test_client.post('/movies/search-movie', data={'search': movie.name})
    assert f'<title>{movie.name}</title>'.encode('UTF-8') in response.data

    response = test_client.post(
        '/movies/search-movie', data={'search': ''}, follow_redirects=True
    )
    assert response.request.path == "/movies/browse"

    response = test_client.post(
        '/movies/search-movie', data={'search': None}, follow_redirects=True
    )
    assert response.request.path == "/movies/not-found"

    assert db.session.query(Movie).filter_by(name='pkmjnhgs').first() is None
    response = test_client.post(
        '/movies/search-movie', data={'search': 'pkmjnhgs'}, follow_redirects=True
    )
    assert b'<span>No movies were found</span>' in response.data


def test_watch_list_manipulation(test_client, new_movie):
    """Test adding and removing movies from watch history."""

    assert db.session.query(User).filter_by(username='TestClient').first() is None
    assert db.session.query(User).filter_by(username='TestClient2').first() is None

    new_user = User(username='TestClient', password='TestPasswd')
    db.session.add(new_user)
    assert (
        db.session.query(User).filter_by(username=new_user.username).first() is not None
    )

    # try unauthorized manipulation
    impostor = User(username='TestClient2', password='TestPasswd')
    db.session.add(impostor)
    assert (
        db.session.query(User).filter_by(username=impostor.username).first() is not None
    )

    db.session.add(new_movie)
    assert (
        db.session.query(Movie).filter_by(poster_link=new_movie.poster_link).first()
        is not None
    )
    id_new_movie = new_movie.id

    try:

        response = test_client.post(
            f'/movies/add-to-watch-list/{new_movie.id}', follow_redirects=True
        )
        assert response.request.path == "/users/login"

        # log in as new_user
        response = test_client.post(
            '/users/login', data={'username': 'TestClient', 'password': 'TestPasswd'}
        )
        assert current_user.username == 'TestClient'

        response = test_client.post(
            f'/movies/add-to-watch-list/{new_movie.id}', follow_redirects=True
        )
        assert (
            response.request.path
            == f"/movies/movie/{new_movie.id}-{movie_name_to_url(new_movie.name)}"
        )
        assert b'<span class="w-100 text-danger">Select the date</span>' in response.data

        # add movie to watch list
        response = test_client.post(
            f'/movies/add-to-watch-list/{new_movie.id}',
            data={
                'datewatched': datetime.strptime(
                    '2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S'
                )
            },
            follow_redirects=True,
        )
        assert (
            response.request.path
            == f"/movies/movie/{new_movie.id}-{movie_name_to_url(new_movie.name)}"
        )
        assert (
            b'<span class="w-100 text-success">Added this movie to watch list</span>'
            in response.data
        )
        id_new_watch_list = (
            db.session.query(WatchList).filter_by(user_id=new_user.id).first().id
        )

        # log in as impostor
        response = test_client.get('/users/logout')
        assert current_user.is_authenticated is False
        response = test_client.post(
            '/users/login', data={'username': 'TestClient2', 'password': 'TestPasswd'}
        )
        assert current_user.username == 'TestClient2'

        response = test_client.post(
            f'/movies/remove-from-watch-list/{id_new_watch_list}', follow_redirects=True
        )
        assert response.request.path == "/access-denied"

        # log in as new_user
        response = test_client.get('/users/logout')
        assert current_user.is_authenticated is False
        response = test_client.post(
            '/users/login', data={'username': 'TestClient', 'password': 'TestPasswd'}
        )
        assert current_user.username == 'TestClient'

        # remove movie from watch list
        response = test_client.post(
            f'/movies/remove-from-watch-list/{id_new_watch_list}', follow_redirects=True
        )
        assert response.request.path == "/movies/watch-history"
        assert db.session.query(WatchList).filter_by(user_id=new_user.id).first() is None

        # non existing movie
        id_new_movie = new_movie.id
        db.session.delete(new_movie)
        response = test_client.post(
            f'/movies/add-to-watch-list/{id_new_movie}',
            data={
                'datewatched': datetime.strptime(
                    '2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S'
                )
            },
            follow_redirects=True,
        )
        assert response.request.path == "/movies/not-found"

        watch_list_count = db.session.query(WatchList).count()
        response = test_client.post(
            f'/movies/remove-from-watch-list/{id_new_watch_list}', follow_redirects=True
        )
        assert response.request.path == "/movies/watch-history"
        assert db.session.query(WatchList).count() == watch_list_count
    finally:
        db.session.query(WatchList).filter_by(user_id=new_user.id).delete()
        db.session.query(User).filter_by(username=new_user.username).delete()
        db.session.query(User).filter_by(username=impostor.username).delete()
        db.session.query(Movie).filter_by(id=id_new_movie).delete()
        db.session.commit()


def test_watch_history(test_client, new_movie):
    """Test page with user's watch history."""

    assert db.session.query(User).filter_by(username='TestClient').first() is None

    new_user = User(username='TestClient', password='TestPasswd')
    db.session.add(new_user)
    assert (
        db.session.query(User).filter_by(username=new_user.username).first() is not None
    )

    db.session.add(new_movie)
    assert (
        db.session.query(Movie).filter_by(poster_link=new_movie.poster_link).first()
        is not None
    )

    response = test_client.get('/movies/watch-history', follow_redirects=True)
    assert response.request.path == "/users/login"

    # log in
    response = test_client.post(
        '/users/login', data={'username': 'TestClient', 'password': 'TestPasswd'}
    )
    assert current_user.username == 'TestClient'

    response = test_client.get('/movies/watch-history', follow_redirects=True)
    assert b'<span>Your Watch history is empty.</span>' in response.data

    try:
        response = test_client.post(
            f'/movies/add-to-watch-list/{new_movie.id}',
            data={
                'datewatched': datetime.strptime(
                    '2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S'
                )
            },
            follow_redirects=True,
        )
        assert (
            b'<span class="w-100 text-success">Added this movie to watch list</span>'
            in response.data
        )

        response = test_client.get('/movies/watch-history', follow_redirects=True)
        assert b'<span>Your Watch history is empty.</span>' not in response.data
        assert (
            f'<h5 class="card-title">{new_movie.name}</h5>'.encode('UTF-8')
            in response.data
        )
    finally:
        # clear all test data
        db.session.query(WatchList).filter_by(user_id=new_user.id).delete()
        db.session.query(User).filter_by(username=new_user.username).delete()
        db.session.query(Movie).filter_by(id=new_movie.id).delete()
        db.session.commit()


def test_watch_later_manipulation(test_client, new_movie):
    """Test adding and removing movies from watch later."""

    assert db.session.query(User).filter_by(username='TestClient').first() is None
    assert db.session.query(User).filter_by(username='TestClient2').first() is None

    new_user = User(username='TestClient', password='TestPasswd')
    db.session.add(new_user)
    assert (
        db.session.query(User).filter_by(username=new_user.username).first() is not None
    )

    db.session.add(new_movie)
    assert (
        db.session.query(Movie).filter_by(poster_link=new_movie.poster_link).first()
        is not None
    )
    id_new_movie = new_movie.id

    try:

        response = test_client.post(
            f'/movies/add-to-watch-later/{new_movie.id}', follow_redirects=True
        )
        assert response.request.path == "/users/login"

        response = test_client.get(
            f'/movies/movie/{new_movie.id}-{movie_name_to_url(new_movie.name)}'
        )
        assert (
            b'<button type="submit" class="btn btn-primary" disabled>Add to watch later</button>'
            in response.data
        )

        # log in as new_user
        response = test_client.post(
            '/users/login', data={'username': 'TestClient', 'password': 'TestPasswd'}
        )
        assert current_user.username == 'TestClient'

        response = test_client.get(
            f'/movies/movie/{new_movie.id}-{movie_name_to_url(new_movie.name)}'
        )
        assert (
            b'<button type="submit" class="btn btn-primary">Add to watch later</button>'
            in response.data
        )

        # add movie to watch later
        response = test_client.post(
            f'/movies/add-to-watch-later/{new_movie.id}', follow_redirects=True
        )
        assert (
            response.request.path
            == f"/movies/movie/{new_movie.id}-{movie_name_to_url(new_movie.name)}"
        )
        assert (
            b'<button type="submit" class="btn btn-primary">Remove from watch later</button>'
            in response.data
        )

        # add movie already in watch later
        response = test_client.post(
            f'/movies/add-to-watch-later/{new_movie.id}', follow_redirects=True
        )
        assert (
            response.request.path
            == f"/movies/movie/{new_movie.id}-{movie_name_to_url(new_movie.name)}"
        )

        # remove movie from watch later
        response = test_client.post(
            f'/movies/remove-from-watch-later/{new_movie.id}', follow_redirects=True
        )
        assert (
            response.request.path
            == f"/movies/movie/{new_movie.id}-{movie_name_to_url(new_movie.name)}"
        )
        assert (
            b'<button type="submit" class="btn btn-primary">Add to watch later</button>'
            in response.data
        )
        assert db.session.query(WatchLater).filter_by(user_id=new_user.id).first() is None

        # remove movie not in watch later
        response = test_client.post(
            f'/movies/remove-from-watch-later/{new_movie.id}', follow_redirects=True
        )
        assert (
            response.request.path
            == f"/movies/movie/{new_movie.id}-{movie_name_to_url(new_movie.name)}"
        )

        # non existing movie
        id_new_movie = new_movie.id
        db.session.delete(new_movie)
        response = test_client.post(
            f'/movies/add-to-watch-later/{id_new_movie}', follow_redirects=True
        )
        assert response.request.path == "/movies/not-found"

        watch_later_count = db.session.query(WatchLater).count()
        response = test_client.post(
            f'/movies/remove-from-watch-later/{id_new_movie}', follow_redirects=True
        )
        assert response.request.path == "/movies/not-found"
        assert db.session.query(WatchLater).count() == watch_later_count
    finally:
        db.session.query(WatchLater).filter_by(user_id=new_user.id).delete()
        db.session.query(User).filter_by(username=new_user.username).delete()
        db.session.query(Movie).filter_by(id=id_new_movie).delete()
        db.session.commit()
