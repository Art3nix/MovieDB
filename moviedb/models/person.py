"""Module defining SQLAlchemy model of Person."""

from sqlalchemy import String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from moviedb.extensions import db


class Person(db.Model):
    """Class representing a person (actor, director, writer)."""

    id: Mapped[int] = mapped_column(primary_key=True)
    imdb_id: Mapped[str | None] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_year: Mapped[int | None] = mapped_column(SmallInteger)
    death_year: Mapped[int | None] = mapped_column(SmallInteger)

    cast_roles = relationship('MovieCast', back_populates='person')
    crew_roles = relationship('MovieCrew', back_populates='person')

    def __repr__(self):
        return f'<Person {self.id}: {self.name}>'
