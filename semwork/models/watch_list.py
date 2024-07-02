"""Module defining SQLAlchemy model of WatchList."""

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from semwork.extensions import db


class WatchList(db.Model):  # pylint: disable=R0903; # sqlalchemy class used to only store data
    """Class representing table WatchList in database."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey('movie.id'), primary_key=True)
    date_watched: Mapped[datetime] = mapped_column(nullable=False)

    def __init__(self, user_id: int, movie_id: int, date_watched: datetime):
        self.user_id = user_id
        self.movie_id = movie_id
        self.date_watched = date_watched

    def __repr__(self):
        return (
            f'<Watchlist {self.id}>'
            f' User: {self.user_id}'
            f' Movie: {self.movie_id}'
            f' Date watched: {self.date_watched}'
        )
