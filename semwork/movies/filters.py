"""App template filters for movies module."""

import re
import unicodedata

from semwork.movies import bp  # pylint: disable=R0401; # noqa
from semwork.extensions import db
from semwork.models.watch_later import WatchLater


@bp.app_template_filter('movie_name_to_url')
def movie_name_to_url(movie_name):
    """Filter transforming movie name to corresponding url name."""

    # remove accents
    url_name = unicodedata.normalize('NFD', movie_name).encode('ASCII', 'ignore').decode("utf-8")
    # remove non-words character and lowercase letters
    url_name = re.sub('[^a-zA-Z0-9 -]+', '', url_name)
    # replace ' - ' with just one space
    url_name = re.sub('( - )+', ' ',  url_name)
    # lowercase all and replace spaces with dash
    url_name = url_name.lower().replace(' ', '-')
    return url_name


@bp.app_template_filter('query_empty')
def query_empty(query):
    """Filter to check if the query returns empty list."""

    return not query or len(query) == 0


@bp.app_template_filter('in_watch_later')
def in_watch_later(movie, user):
    """Check if the movie is in user's watch later."""

    if not user or not user.is_authenticated:
        # user has to be authenticated
        return False
    return db.session.query(WatchLater).where(WatchLater.user_id == user.id, WatchLater.movie_id == movie).count() > 0
