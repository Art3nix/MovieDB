"""Business logic of the home sites."""

from datetime import datetime, timedelta
from sqlalchemy import select, func, desc, outerjoin, case
from sqlalchemy.orm import aliased
from flask_login import current_user

from moviedb.extensions import db
from moviedb.models import Movie, WatchHistory, MovieCast, MovieGenre, MovieCrew


def get_new_recommendations(maximum: int = 30, recent_limit: int = 20):
    """Get number of new recommended movies
    based on the recent watch history."""

    # get n recently watched movies
    recent_ids_cte = (
        select(WatchHistory.movie_id)
        .where(WatchHistory.user_id == current_user.id)
        .order_by(WatchHistory.date_watched.desc())
        .limit(recent_limit)
        .cte(name="recent_ids")
    )

    has_recent = db.session.query(recent_ids_cte.c.movie_id).first()
    if not has_recent:
        return []

    recommendations = find_and_calculate_recommendations(recent_ids_cte, maximum)

    # return given maximum of movies
    return recommendations.all()


def find_and_calculate_recommendations(recent_ids_cte, maximum):

    # genre
    recent_genres = (
        select(
            MovieGenre.genre_id,
            func.count().label("cnt")
        )
        .where(MovieGenre.movie_id.in_(select(recent_ids_cte.c.movie_id)))
        .group_by(MovieGenre.genre_id)
        .cte(name="recent_genres")
    )

    # cast
    recent_cast = (
        select(
            MovieCast.person_id,
            func.count().label("cnt")
        )
        .where(MovieCast.movie_id.in_(select(recent_ids_cte.c.movie_id)))
        .group_by(MovieCast.person_id)
        .cte(name="recent_cast")
    )

    # director
    recent_directors = (
        select(
            MovieCrew.person_id,
            func.count().label("cnt")
        )
        .where(
            (MovieCrew.movie_id.in_(select(recent_ids_cte.c.movie_id))) &
            (MovieCrew.role == "director")
        )
        .group_by(MovieCrew.person_id)
        .cte(name="recent_directors")
    )

    # calculate scores
    genre_scores = (
        select(
            MovieGenre.movie_id,
            func.sum(recent_genres.c.cnt).label("score")
        )
        .join(recent_genres, MovieGenre.genre_id == recent_genres.c.genre_id)
        .where(~MovieGenre.movie_id.in_(select(recent_ids_cte.c.movie_id)))
        .group_by(MovieGenre.movie_id)
        .cte(name="genre_scores")
    )

    cast_scores = (
        select(
            MovieCast.movie_id,
            func.sum(recent_cast.c.cnt).label("score")
        )
        .join(recent_cast, MovieCast.person_id == recent_cast.c.person_id)
        .where(~MovieCast.movie_id.in_(select(recent_ids_cte.c.movie_id)))
        .group_by(MovieCast.movie_id)
        .cte(name="cast_scores")
    )

    director_scores = (
        select(
            MovieCrew.movie_id,
            func.sum(recent_directors.c.cnt).label("score")
        )
        .join(recent_directors, MovieCrew.person_id == recent_directors.c.person_id)
        .where(
            (MovieCrew.role == "director") &
            (~MovieCrew.movie_id.in_(select(recent_ids_cte.c.movie_id)))
        )
        .group_by(MovieCrew.movie_id)
        .cte(name="director_scores")
    )
    g = aliased(genre_scores)
    c = aliased(cast_scores)
    d = aliased(director_scores)
    combined_scores = (
        select(
            func.coalesce(g.c.movie_id, c.c.movie_id).label("movie_id"),
            func.coalesce(g.c.score, 0).label("genre_score"),
            func.coalesce(c.c.score, 0).label("cast_score"),
            func.coalesce(d.c.score, 0).label("director_score"),
        )
        .select_from(
            outerjoin(
                outerjoin(g, c, g.c.movie_id == c.c.movie_id),
                d,
                func.coalesce(g.c.movie_id, c.c.movie_id) == d.c.movie_id,
            )
        )
        .where(
            (func.coalesce(g.c.score, 0) +
            func.coalesce(c.c.score, 0) +
            func.coalesce(d.c.score, 0)) >= 2
        )
        .cte(name="combined_scores")
    )

    # final query
    recommendations = (
        db.session.query(Movie)
        .join(combined_scores, Movie.id == combined_scores.c.movie_id)
        .order_by(desc(
                combined_scores.c.genre_score * 3 +
                combined_scores.c.cast_score * 4 +
                combined_scores.c.director_score * 6 +
                func.coalesce(Movie.imdb_rating, 0) / 2 +
                case((func.abs(Movie.release_year - func.avg(Movie.release_year).over()) <= 5, 2), else_=0)
            ))
        .limit(maximum)
    )

    return recommendations


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
