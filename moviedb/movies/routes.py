"""Module providing routes for /movies sites."""

import re
from sqlalchemy import select, func, cast, Text, case
from flask import request, render_template, redirect, url_for
from flask_login import login_required, current_user
from unidecode import unidecode

from moviedb.extensions import db
from moviedb.movies import bp  # pylint: disable=R0401; # noqa
from moviedb.movies.services import refresh_tmdb_data
from moviedb.movies.filters import movie_name_to_url
from moviedb.models.movie import Movie
from moviedb.models.watch_history import WatchHistory
from moviedb.models.watch_later import WatchLater


@bp.route('/browse')
def browse():
    """Route to the browse movies page."""

    page = request.args.get('page', 1, type=int)
    query = select(Movie).order_by(Movie.id)
    pagination = db.paginate(query, page=page, per_page=24)

    # Lazy refresh TMDb data
    #for movie in pagination.items:
    #    if not movie.tmdb_id or not movie.poster_path or not movie.summary:
    #        refresh_tmdb_data(movie)
    #db.session.commit()

    return render_template('movies/browse.html', pagination=pagination)


@bp.route('/movie/<int:movie_id>-<string:name>')
def movie(movie_id, name):
    """Route to the specific movie page."""

    queried_movie = db.session.query(Movie).filter_by(id=movie_id).first()
    if queried_movie is None:
        # incorrect id
        return redirect(url_for('movies.not_found'))

    url_name = movie_name_to_url(queried_movie.title)
    if url_name != name.lower():
        # incorrect name
        return redirect(url_for('movies.not_found'))
    
    # lazy refresh TMDb data
    if not queried_movie.tmdb_id or not queried_movie.poster_path or not queried_movie.summary:
        refresh_tmdb_data(queried_movie)

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
        Movie.query.join(WatchHistory)
        .add_columns(WatchHistory.id, WatchHistory.date_watched)
        .where(WatchHistory.user_id == current_user.id)
        .order_by(WatchHistory.date_watched)
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
    name = movie_name_to_url(queried_movie.title)

    if not date_watched:
        return redirect(url_for('movies.movie', movie_id=queried_movie.id, name=name, error='Select the date'))

    db.session.add(WatchHistory(user_id=current_user.id, movie_id=movie_id, date_watched=date_watched))
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

    watched_movie = db.session.query(WatchHistory).filter_by(id=movie_id).first()
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
    name = movie_name_to_url(queried_movie.title)

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
    name = movie_name_to_url(queried_movie.title)

    if watch_later_movie is None:
        return redirect(url_for('movies.movie', movie_id=movie_id, name=name))

    db.session.delete(watch_later_movie)
    db.session.commit()
    return redirect(url_for('movies.movie', movie_id=movie_id, name=name))


@bp.route('search-movie', methods=['GET', 'POST'])
def search_movie():
    """Route to the page with search results."""

    # POST request
    if request.method == 'POST':
        prompt = request.form.get('search', '').strip()
        if not prompt:
            return redirect(url_for('movies.browse'))

        # Normalize and encode for URL
        prompt_param = unidecode(prompt).lower()
        return redirect(url_for('movies.search_movie', q=prompt_param))

    # GET request
    prompt = request.args.get('q', '').strip()
    if not prompt:
        return redirect(url_for('movies.browse'))

    page = request.args.get('page', 1, type=int)

    # normalize
    normalized_prompt = unidecode(prompt.lower())
    normalized_prompt = re.sub(r'^(the |a |an )', '', normalized_prompt)
    normalized_title = func.regexp_replace(
        func.lower(Movie.unaccented_title), r'^(the |a |an )', '', 'i'
    )
    # calculate similarities
    similarity_score = func.similarity(normalized_title, cast(normalized_prompt, Text))
    exact_match = case((normalized_title.ilike(f"%{normalized_prompt}%"), 5), else_=0)
    startswith = case((normalized_title.ilike(f"{normalized_prompt}%"), 3), else_=0)
    total_score = similarity_score + exact_match + startswith

    found_movies = (
        db.session.query(Movie)
        .filter(normalized_title.op('%')(cast(normalized_prompt, Text)))  # trigram similarity filter
        .add_columns(total_score.label('score'))
        .order_by(total_score.desc())
    )
    pagination = db.paginate(found_movies, page=page, per_page=24)

    # Lazy refresh TMDb data
    #for movie in pagination.items:
    #    if not movie.tmdb_id or not movie.poster_path or not movie.summary:
    #        refresh_tmdb_data(movie)
    #db.session.commit()

    return render_template('movies/search.html', prompt=prompt, pagination=pagination)
