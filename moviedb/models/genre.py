"""Module defining SQLAlchemy model of Genre."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from moviedb.extensions import db


class Genre(db.Model):
    """Class representing movie genre."""

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies = relationship('MovieGenre', back_populates='genre')

    def __repr__(self):
        return f'<Genre {self.name}>'
