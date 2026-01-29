"""Module defining SQLAlchemy model of UserRating."""

from sqlalchemy import ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from moviedb.extensions import db


class UserRating(db.Model):
    """User's personal movie rating."""

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey('movie.id'), primary_key=True)
    rating: Mapped[int] = mapped_column(SmallInteger)  # 1–10
