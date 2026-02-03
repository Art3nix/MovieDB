"""Business logic of the home sites."""

from collections import Counter
from datetime import datetime, timedelta
from sqlalchemy import func, case
from sqlalchemy.orm import joinedload
from flask_login import current_user

from moviedb.extensions import db
from moviedb.models.movie import Movie
from moviedb.models.watch_history import WatchHistory


def get_new_recommendations(maximum: int = 30, recent_limit: int = 20):
    """Get number of new recommended movies
    based on the recent watch history."""

    # get n recently watched movies
    recent_wh = (
        db.session.query(Movie)
        .join(WatchHistory, Movie.id == WatchHistory.movie_id)
        .where(WatchHistory.user_id == current_user.id)
        .order_by(WatchHistory.date_watched.desc())
        .limit(recent_limit)
    )

    if not recent_wh:
        return []

    recommendations = recent_wh#find_and_calculate_recommendations(recent_wh)

    # return given maximum of movies
    return recommendations.limit(maximum).all()


def find_and_calculate_recommendations(recent_movies_query: Movie):
    """Calculate recommend value of each movie
    based on given watch history."""

    recent_movies = recent_movies_query.options(
        joinedload(Movie.genres),
        joinedload(Movie.cast),
        joinedload(Movie.crew)
    ).all()

    if not recent_movies:
        return db.session.query(Movie).filter(False)

    # Aggregate features from recent movies
    genre_counter = Counter()
    cast_counter = Counter()
    director_counter = Counter()

    # TODO include release year

    for movie in recent_movies:
        genre_counter.update([g.genre.name for g in movie.genres])
        cast_counter.update([c.person.id for c in movie.cast])
        director_counter.update([c.person.id for c in movie.crew if c.role == "director"])

    # IDs to exclude (already watched)
    recent_ids = {m.id for m in recent_movies}

    # Base query for candidate movies
    candidate_query = (
        db.session.query(Movie)
        .options(
            joinedload(Movie.genres),
            joinedload(Movie.cast),
            joinedload(Movie.crew)
        )
        .filter(~Movie.id.in_(recent_ids))
    )

    # Compute a simple score for each candidate movie
    scored_movies = []
    for movie in candidate_query.all():
        score = 0
        # Genre match
        score += sum(genre_counter[g.genre.name] for g in movie.genres if g.genre.name in genre_counter)
        # Cast match
        score += sum(cast_counter[c.person.id] for c in movie.cast if c.person.id in cast_counter)
        # Director match
        score += sum(director_counter[c.person.id] for c in movie.crew if c.role == "director" and c.person.id in director_counter)
        # Boost score with IMDb rating if available
        if movie.imdb_rating:
            score += movie.imdb_rating / 2

        if score > 0:
            scored_movies.append((score, movie))

    # Sort by score descending
    scored_movies.sort(key=lambda x: x[0], reverse=True)

    top_ids_ordered = [m.id for _, m in scored_movies]
    if not top_ids_ordered:
        return db.session.query(Movie).filter(False)  # empty query

    # Use CASE to preserve ordering
    ordering = case({id_: index for index, id_ in enumerate(top_ids_ordered)}, value=Movie.id)
    return db.session.query(Movie).filter(Movie.id.in_(top_ids_ordered)).order_by(ordering)


def get_watch_again():
    """Get movies that could be watched again based on watch patterns."""

    # 1. Load watch history, ordered by movie and date
    watch_history = (
        db.session.query(Movie, WatchHistory)
        .join(WatchHistory, Movie.id == WatchHistory.movie_id)
        .filter(WatchHistory.user_id == current_user.id)
        .order_by(Movie.id, WatchHistory.date_watched)
        .all()
    )

    if not watch_history:
        return []

    watch_again = []

    i = 0
    while i < len(watch_history):
        movie, _ = watch_history[i]
        # Collect all dates for this movie
        dates = []
        while i < len(watch_history) and watch_history[i][0].id == movie.id:
            dates.append(watch_history[i][1].date_watched)
            i += 1

        # Only consider movies watched at least twice
        if len(dates) < 2:
            continue

        # Calculate average interval between consecutive watches
        intervals = [(dates[j] - dates[j-1]).days for j in range(1, len(dates))]
        avg_interval_days = sum(intervals) / len(intervals)

        # Predict next watch date
        predicted_next_watch = dates[-1] + timedelta(days=avg_interval_days)

        # If predicted next watch is in the past, recommend it
        if predicted_next_watch < datetime.now():
            # The further in the past it should have been watched, the higher priority
            delay = (datetime.now() - predicted_next_watch).total_seconds()
            watch_again.append((delay, movie))

    # Sort by how overdue the movie is (most overdue first)
    watch_again.sort(key=lambda x: x[0], reverse=True)

    # Return only movies
    return [movie for (_, movie) in watch_again]
