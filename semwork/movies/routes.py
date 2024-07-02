"""Module providing routes for /movies sites."""

import re
import unicodedata

from sqlalchemy import select, case
from flask import request, render_template, redirect, url_for
from flask_login import login_required, current_user

from semwork.extensions import db
from semwork.movies import bp  # pylint: disable=R0401; # noqa
from semwork.movies.filters import movie_name_to_url
from semwork.models.movie import Movie
from semwork.models.watch_list import WatchList
from semwork.models.watch_later import WatchLater


@bp.route('/browse')
def browse():
    """Route to the browse movies page."""

    page = request.args.get('page', 1, type=int)
    query = select(Movie).order_by(Movie.id)
    pagination = db.paginate(query, page=page, per_page=24)
    return render_template('movies/browse.html', pagination=pagination)


@bp.route('/movie/<int:movie_id>-<string:name>')
def movie(movie_id, name):
    """Route to the specific movie page."""

    queried_movie = db.session.query(Movie).filter_by(id=movie_id).first()
    if queried_movie is None:
        # incorrect id
        return redirect(url_for('movies.not_found'))

    url_name = movie_name_to_url(queried_movie.name)
    if url_name != name.lower():
        # incorrect name
        return redirect(url_for('movies.not_found'))

    return render_template('movies/movie.html', movie=queried_movie, **request.args)


@bp.route('/not-found')
def not_found():
    """Route to the error site when movie does not exist."""

    return render_template('error_sites/movie_not_found.html')


@bp.route('watch-history')
@login_required
def watch_history():
    """Route to the page with user's watch history."""

    page = request.args.get('page', 1, type=int)
    # pagination.items are now a tuple (Movie, int, datetime)
    pagination = (
        Movie.query.join(WatchList)
        .add_columns(WatchList.id, WatchList.date_watched)
        .where(WatchList.user_id == current_user.id)
        .order_by(WatchList.date_watched)
        .paginate(page=page, per_page=24, error_out=False)
    )

    return render_template('movies/watch_history.html', pagination=pagination)


@bp.route('add-to-watch-list/<int:movie_id>', methods=['POST'])
@login_required
def add_to_watch_list(movie_id):
    """Route to page that will add specified movie to user's watch history."""

    queried_movie = db.session.query(Movie).filter_by(id=movie_id).first()
    if queried_movie is None:
        return redirect(url_for('movies.not_found'))

    date_watched = request.form.get('datewatched')
    name = movie_name_to_url(queried_movie.name)

    if not date_watched:
        return redirect(url_for('movies.movie', movie_id=queried_movie.id, name=name, error='Select the date'))

    db.session.add(WatchList(user_id=current_user.id, movie_id=movie_id, date_watched=date_watched))
    db.session.commit()
    return redirect(
        url_for(
            'movies.movie',
            movie_id=queried_movie.id,
            name=name,
            success='Added this movie to watch list',
        )
    )


@bp.route('remove-from-watch-list/<int:movie_id>', methods=['POST'])
@login_required
def remove_from_watch_list(movie_id):
    """Route to page that will remove specified movie from user's watch history."""

    watched_movie = db.session.query(WatchList).filter_by(id=movie_id).first()
    if watched_movie is None:
        return redirect(url_for('movies.watch_history'))

    if watched_movie.user_id != current_user.id:
        return redirect(url_for('home.access_denied'))

    db.session.delete(watched_movie)
    db.session.commit()
    return redirect(url_for('movies.watch_history'))


@bp.route('add-to-watch-later/<int:movie_id>', methods=['POST'])
@login_required
def add_to_watch_later(movie_id):
    """Route to page that will add specified movie to user's watch later."""

    queried_movie = db.session.query(Movie).filter_by(id=movie_id).first()
    if queried_movie is None:
        return redirect(url_for('movies.not_found'))

    watch_later_movie = db.session.query(WatchLater).filter_by(user_id=current_user.id, movie_id=movie_id).first()
    name = movie_name_to_url(queried_movie.name)

    if watch_later_movie:
        return redirect(url_for('movies.movie', movie_id=movie_id, name=name))

    db.session.add(WatchLater(user_id=current_user.id, movie_id=movie_id))
    db.session.commit()
    return redirect(url_for('movies.movie', movie_id=movie_id, name=name))


@bp.route('remove-from-watch-later/<int:movie_id>', methods=['POST'])
@login_required
def remove_from_watch_later(movie_id):
    """Route to page that will remove specified movie from user's watch later."""

    queried_movie = db.session.query(Movie).filter_by(id=movie_id).first()
    if queried_movie is None:
        return redirect(url_for('movies.not_found'))

    watch_later_movie = db.session.query(WatchLater).filter_by(user_id=current_user.id, movie_id=movie_id).first()
    name = movie_name_to_url(queried_movie.name)

    if watch_later_movie is None:
        return redirect(url_for('movies.movie', movie_id=movie_id, name=name))

    db.session.delete(watch_later_movie)
    db.session.commit()
    return redirect(url_for('movies.movie', movie_id=movie_id, name=name))


@bp.route('search-movie', methods=['POST'])
def search_movie():
    """Route to the page with search results."""

    prompt = request.form.get('search')
    if prompt is None:
        return redirect(url_for('movies.not_found'))
    if prompt == '':
        return redirect(url_for('movies.browse'))

    prompt_words = unicodedata.normalize('NFD', prompt).encode('ASCII', 'ignore').decode("utf-8")
    # remove non-words character and lowercase letters
    prompt_words = re.sub('[^a-zA-Z0-9 ]+', ' ', prompt_words).lower()
    # remove words the, a, and
    prompt_words = re.sub('(?<![a-zA-Z0-9_])(the|a|and)+(?![a-zA-Z0-9_])', '', prompt_words)
    # remove leading or trailing whitespaces
    prompt_words = re.sub('^[\r\n\t\f\v ]+|[\r\n\t\f\v ]+$', '', prompt_words)
    # squash whitespaces and split into words
    prompt_words = re.sub('[\r\n\t\f\v ]+', ' ', prompt_words).split(' ')

    common_words = (sum(case((Movie.unaccented_name.ilike(f'%{word}%'), 1), else_=0) for word in prompt_words)).label(
        'common_words'
    )
    found_movies = (
        db.session.query(Movie).add_columns(common_words).where(common_words > 0).order_by(common_words.desc()).all()
    )

    return render_template('movies/search.html', prompt=prompt, movies=found_movies)
