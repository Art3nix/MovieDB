"""Business logic of the home sites."""

from datetime import datetime, timedelta
from sqlalchemy import func
from flask_login import current_user

from moviedb.extensions import db
from moviedb.models import Movie, WatchHistory, MovieCast, MovieGenre, MovieCrew


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

    recommendations = find_and_calculate_recommendations(recent_wh)

    # return given maximum of movies
    return recommendations.limit(maximum).all()


def find_and_calculate_recommendations(recent_movies_query):

    # recent movie ids
    recent_ids = recent_movies_query.with_entities(Movie.id).statement


    # genre counts
    recent_genres = (
        db.session.query(
            MovieGenre.genre_id.label("genre_id"),
            func.count().label("cnt")
        )
        .filter(MovieGenre.movie_id.in_(recent_ids))
        .group_by(MovieGenre.genre_id)
        .subquery()
    )

    # cast counts
    recent_cast = (
        db.session.query(
            MovieCast.person_id.label("person_id"),
            func.count().label("cnt")
        )
        .filter(MovieCast.movie_id.in_(recent_ids))
        .group_by(MovieCast.person_id)
        .subquery()
    )

    # director counts
    recent_directors = (
        db.session.query(
            MovieCrew.person_id.label("person_id"),
            func.count().label("cnt")
        )
        .filter(MovieCrew.movie_id.in_(recent_ids))
        .filter(MovieCrew.role == "director")
        .group_by(MovieCrew.person_id)
        .subquery()
    )

    # calculate scores
    genre_score = func.coalesce(func.sum(recent_genres.c.cnt), 0)
    cast_score = func.coalesce(func.sum(recent_cast.c.cnt), 0)
    director_score = func.coalesce(func.sum(recent_directors.c.cnt), 0)
    rating_score = func.coalesce(Movie.imdb_rating, 0)
    total_score = (
        genre_score * 3 +
        cast_score  * 4 +
        director_score * 6 +
        rating_score / 2
    )

    # ---- Main query ----
    recommendations = (
        db.session.query(
            Movie,
            genre_score.label("g"),
            cast_score.label("c"),
            director_score.label("d"),
            rating_score.label("r"),
            total_score.label("score")
        )
        # genres
        .outerjoin(MovieGenre, Movie.id == MovieGenre.movie_id)
        .outerjoin(recent_genres, MovieGenre.genre_id == recent_genres.c.genre_id)
        # cast
        .outerjoin(MovieCast, Movie.id == MovieCast.movie_id)
        .outerjoin(recent_cast, MovieCast.person_id == recent_cast.c.person_id)
        # directors
        .outerjoin(MovieCrew, Movie.id == MovieCrew.movie_id)
        .outerjoin(
            recent_directors,
            MovieCrew.person_id == recent_directors.c.person_id
        )
        .filter(~Movie.id.in_(recent_ids))
        .group_by(Movie.id)
        .having(total_score > 0)
        # at least 2 same genres, 1 director or some cast
        .having(
            (genre_score + cast_score + director_score) >= 2
        )
        .order_by(total_score.desc())
    )

    return recommendations.with_entities(Movie)


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
