"""Module providing routes for default path."""

from flask import render_template
from flask_login import login_required, current_user

from semwork.home import bp  # pylint: disable=R0401; # noqa
from semwork.home.services import get_watch_again, get_new_recommendations
from semwork.extensions import db
from semwork.models.movie import Movie
from semwork.models.watch_later import WatchLater


@bp.route('/')
@login_required
def index():
    """Route to the home page."""
    watch_later = (
        db.session.query(Movie)
        .join(WatchLater, Movie.id == WatchLater.movie_id)
        .where(WatchLater.user_id == current_user.id)
        .all()
    )
    recommendations = get_new_recommendations()
    watch_again = get_watch_again()
    return render_template(
        'home.html',
        name=current_user.username,
        watch_later=watch_later,
        recommendations=recommendations,
        watch_again=watch_again,
    )


@bp.route('/access-denied')
def access_denied():
    """Route to the error site for cases when user does not have access."""
    return render_template('error_sites/access_denied.html')
