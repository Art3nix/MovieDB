"""Module testing user modules."""

from flask_login import current_user

from semwork.extensions import db
from semwork.models.user import User


def test_login_pages(test_client):
    """Test login and register pages."""

    response = test_client.get('/users/register')
    assert response.status_code == 200
    response = test_client.get('/users/login')
    assert response.status_code == 200


def test_register_user(test_client):
    """Test registering new user."""

    assert db.session.query(User).filter_by(username='TestClient').first() is None

    response = test_client.post(
        '/users/register',
        data={'username': 'TestClient', 'password': 'TestPasswd'},
        follow_redirects=True,
    )
    assert response.request.path == "/users/login"

    try:
        response = test_client.post(
            '/users/register', data={'username': 'TestClient', 'password': 'TestPasswd'}
        )
        assert (
            b'<span class="w-100 text-danger">This username already exists</span>'
            in response.data
        )
    finally:
        db.session.delete(db.session.query(User).filter_by(username='TestClient').first())
        db.session.commit()


def test_login(test_client):
    """Test logging in as existing user."""

    assert db.session.query(User).filter_by(username='TestClient').first() is None

    # registering new user
    response = test_client.post(
        '/users/register',
        data={'username': 'TestClient', 'password': 'TestPasswd'},
        follow_redirects=True,
    )
    assert response.request.path == "/users/login"

    try:
        response = test_client.post(
            '/users/login', data={'username': 'TestClient', 'password': 'WrongPasswd'}
        )
        assert (
            b'<span class="w-100 text-danger">Wrong credentials</span>' in response.data
        )
        response = test_client.post(
            '/users/login',
            data={'username': 'TestClient', 'password': 'TestPasswd'},
            follow_redirects=True,
        )
        assert response.request.path == "/"

        assert current_user.username == 'TestClient'
        assert b'<span class="float-right">TestClient</span>' in response.data

        response = test_client.get('/users/register', follow_redirects=True)
        assert response.request.path == "/"
        response = test_client.get('/users/login', follow_redirects=True)
        assert response.request.path == "/"

        response = test_client.get('/users/logout', follow_redirects=True)
        assert response.request.path == "/users/login"
        assert current_user.is_authenticated is False
    finally:
        db.session.delete(db.session.query(User).filter_by(username='TestClient').first())
        db.session.commit()
