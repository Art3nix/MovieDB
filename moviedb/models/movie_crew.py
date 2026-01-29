"""Module defining SQLAlchemy model of MovieCrew."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from moviedb.extensions import db


class MovieCrew(db.Model):
    """Crew members of a movie."""

    movie_id: Mapped[int] = mapped_column(ForeignKey('movie.id'), primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey('person.id'), primary_key=True)
    role: Mapped[str] = mapped_column(String(50), primary_key=True)
    # examples: director, writer, producer

    movie = db.relationship('Movie', back_populates='crew')
    person = db.relationship('Person', back_populates='crew_roles')
