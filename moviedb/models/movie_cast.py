"""Module defining SQLAlchemy model of MovieCast."""

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from moviedb.extensions import db


class MovieCast(db.Model):
    """Actors appearing in a movie."""

    movie_id: Mapped[int] = mapped_column(ForeignKey('movie.id'), primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey('person.id'), primary_key=True)
    billing: Mapped[int] = mapped_column(SmallInteger)  # 1 = lead actor
    character: Mapped[str | None] = mapped_column(String(255))

    movie = db.relationship('Movie', back_populates='cast')
    person = db.relationship('Person', back_populates='cast_roles')
