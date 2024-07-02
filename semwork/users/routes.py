"""Module providing routes for /users sites."""

from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user

from semwork.users import bp  # pylint: disable=R0401; # noqa
from semwork.models.user import User
from semwork.extensions import db, bcrypt


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Route to the login form page."""

    if request.method == 'POST':
        # submit login form
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            remember = bool(request.form.get('remember'))
            login_user(user, remember=remember)
            return redirect(url_for('home.index'))
        return render_template('users/login.html', error='Wrong credentials')

    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    return render_template('users/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Route to the logout page."""

    logout_user()
    return redirect(url_for('users.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Route to the register form page."""

    if request.method == 'POST':
        # submit register form
        if db.session.query(User).filter_by(username=request.form['username']).count() >= 1:
            return render_template('users/register.html', error='This username already exists')

        new_user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('users.login'))

    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    return render_template('users/register.html')
