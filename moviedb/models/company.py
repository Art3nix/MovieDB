"""Module defining SQLAlchemy model of Company."""

from sqlalchemy.orm import Mapped, mapped_column, relationship

from moviedb.extensions import db


class Company(db.Model):
    """Table containing production companies."""

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    movies = relationship('MovieProduction', back_populates='company')

    def __repr__(self):
        return f'<Company {self.name}>'
