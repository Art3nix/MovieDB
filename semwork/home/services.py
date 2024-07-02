"""Business logic of the home sites."""

from collections import Counter
from datetime import datetime
from sqlalchemy import func, case
from flask_login import current_user

from semwork.extensions import db
from semwork.models.movie import Movie
from semwork.models.watch_list import WatchList


def get_new_recommendations(maximum: int = 30, recent_limit: int = 10):
    """Get number of new recommended movies
    based on the recent watch history."""

    # get n recently watched movies
    recent_wh = (
        db.session.query(Movie)
        .join(WatchList, Movie.id == WatchList.movie_id)
        .where(WatchList.user_id == current_user.id)
        .order_by(WatchList.date_watched.desc())
        .limit(recent_limit)
    )

    if recent_wh.count() == 0:
        return []

    recommendations = find_and_calculate_recommendations(recent_wh)

    # return given maximum of movies
    return recommendations.limit(maximum).all()


def find_and_calculate_recommendations(watch_history: Movie):
    """Calculate recommend value of each movie
    based on given watch history."""

    common_genres = 3

    # genres
    recent_genres = [genre for entry in watch_history for genre in entry.genre.split(', ')]
    c = Counter(recent_genres)
    recent_genres = c.most_common(common_genres)
    if len(recent_genres) == 1:
        recent_genres.append(recent_genres[0])
        recent_genres.append(recent_genres[0])
    elif len(recent_genres) == 2:
        recent_genres.append(recent_genres[1])

    # years
    release_years = [entry.release_year for entry in watch_history]
    avg_released = sum(release_years) / len(release_years)

    # directors
    directors = [entry.director for entry in watch_history]

    # actors
    actors = (
        [entry.star1 for entry in watch_history]
        + [entry.star2 for entry in watch_history]
        + [entry.star3 for entry in watch_history]
        + [entry.star4 for entry in watch_history]
    )

    # recommend_value = genre1 * 100 + genre2 * 50 + genre3 * 20 - yearDist * 0.25 + director * 20 + star1 * 5 + star2 * 5 + star3 * 5 + star4 * 5
    recommend_value_col = (
        case((Movie.genre.contains(recent_genres[0][0]), 1), else_=0) * 100
        + case((Movie.genre.contains(recent_genres[1][0]), 1), else_=0) * 50
        + case((Movie.genre.contains(recent_genres[2][0]), 1), else_=0) * 20
        - func.abs(Movie.release_year - avg_released) * 0.25
        + case((Movie.director.in_(directors), 1), else_=0) * 20
        + (
            case((Movie.star1.in_(actors), 1), else_=0)
            + case((Movie.star2.in_(actors), 1), else_=0)
            + case((Movie.star3.in_(actors), 1), else_=0)
            + case((Movie.star4.in_(actors), 1), else_=0)
        )
        * 5
    ).label('recommend_value')
    watched_ids = (
        db.session.query(Movie.id)
        .join(WatchList, Movie.id == WatchList.movie_id)
        .where(WatchList.user_id == current_user.id)
    )
    recommendations = (
        db.session.query(Movie)
        .add_columns(recommend_value_col)
        .where(Movie.id.not_in(watched_ids))
        .order_by(recommend_value_col.desc())
    )

    return recommendations


def get_watch_again():
    """Get movies that could be watched again."""

    # order watch history by movies and then by date watched in ascending order
    watch_history = (
        db.session.query(Movie, WatchList)
        .join(WatchList, Movie.id == WatchList.movie_id)
        .where(WatchList.user_id == current_user.id)
        .order_by(Movie.id)
        .order_by(WatchList.date_watched)
        .all()
    )

    if len(watch_history) == 0:
        return []

    watch_again = []

    i = 1
    dates = [watch_history[0][1].date_watched]
    while i < len(watch_history):
        # go through whole watch history
        movie = watch_history[i]

        if movie[0].id == watch_history[i - 1][0].id:
            # same movies as previous one
            dates.append(movie[1].date_watched)
        elif len(dates) > 1:
            # different movie and previous movie id has been more than once in wh
            diff = dates[-1] - dates[-2]
            if dates[-1] + diff < datetime.now():
                # since last time watched the interval between dates watched has passed
                watch_again.append((dates[-1] + diff - datetime.now(), watch_history[i - 1][0]))
            dates = [movie[1].date_watched]
        i += 1

    # check last movie
    if len(dates) > 1:
        diff = dates[-1] - dates[-2]
        if dates[-1] + diff < datetime.now():
            watch_again.append((datetime.now() - (dates[-1] + diff), watch_history[i - 1][0]))
        dates = [movie[1].date_watched]

    watch_again = sorted(watch_again, key=lambda i: i[0], reverse=True)

    return [movie for (_, movie) in watch_again]
