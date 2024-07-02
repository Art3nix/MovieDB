"""Module defining SQLAlchemy model of WatchLater."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from semwork.extensions import db


class WatchLater(db.Model):  # pylint: disable=R0903; # sqlalchemy class used to only store data
    """Class representing table WatchLater in database."""

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey('movie.id'), primary_key=True)

    def __init__(self, user_id: int, movie_id: int):
        self.user_id = user_id
        self.movie_id = movie_id

    def __repr__(self):
        return f'<Watchlater {self.id}>' f' User: {self.user_id}' f' Movie: {self.movie_id}'
