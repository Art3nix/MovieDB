"""Module defining SQLAlchemy model of MovieProduction."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from moviedb.extensions import db


class MovieProduction(db.Model):
    """Table containing production companies."""

    movie_id: Mapped[int] = mapped_column(ForeignKey('movie.id'), primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('company.id'), primary_key=True)

    movie = db.relationship('Movie', back_populates='productions')
    company = db.relationship('Company', back_populates='movies')
