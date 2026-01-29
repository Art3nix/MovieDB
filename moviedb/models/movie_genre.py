"""Module defining SQLAlchemy model of MovieGenre."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from moviedb.extensions import db


class MovieGenre(db.Model):
    """Association table between movies and genres."""

    movie_id: Mapped[int] = mapped_column(ForeignKey('movie.id'), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey('genre.id'), primary_key=True)

    movie = db.relationship('Movie', back_populates='genres')
    genre = db.relationship('Genre', back_populates='movies')
