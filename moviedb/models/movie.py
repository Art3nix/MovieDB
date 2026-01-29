"""Module defining SQLAlchemy model of Movie."""

import unicodedata

from sqlalchemy.orm import Mapped, mapped_column, relationship

from moviedb.extensions import db


class Movie(db.Model):  # pylint: disable=R0902,R0903; # sqlalchemy class used to only store data
    """Class representing table Movie in database."""

    id: Mapped[int] = mapped_column(primary_key=True)
    imdb_id: Mapped[str | None] = mapped_column(unique=True)
    tmdb_id: Mapped[int | None]
    title: Mapped[str]
    unaccented_title: Mapped[str]
    release_year: Mapped[int | None]
    runtime: Mapped[str | None]
    tagline: Mapped[str | None]
    summary: Mapped[str | None]
    keywords: Mapped[str | None]
    poster_path: Mapped[str | None]
    backdrop_path: Mapped[str | None]
    language: Mapped[str | None]
    imdb_rating: Mapped[float | None]
    imdb_votes: Mapped[int | None]
    meta_score: Mapped[int | None]
    certificate: Mapped[str | None]
    gross_earned: Mapped[int | None]

    genres = relationship('MovieGenre', back_populates='movie', cascade='all, delete-orphan')
    cast = relationship('MovieCast', back_populates='movie', cascade='all, delete-orphan')
    crew = relationship('MovieCrew', back_populates='movie', cascade='all, delete-orphan')
    productions = relationship('MovieProduction', back_populates='movie', cascade='all, delete-orphan')


    def __init__(
        self,
        title: str,
        release_year: int,
        runtime: str,
        summary: str,
        poster_path: str,
        imdb_rating: float,
        imdb_votes: int
    ):  # pylint: disable=R0913; # related to previous warnings
        self.title = title
        self.unaccented_title = unicodedata.normalize('NFD', title).encode('ASCII', 'ignore').decode("utf-8")
        self.release_year = release_year
        self.runtime = runtime
        self.summary = summary
        self.poster_path = poster_path
        self.imdb_rating = imdb_rating
        self.imdb_votes = imdb_votes

    def __repr__(self):
        return (
            f'<Movie {self.title}>'
            f' {self.imdb_id}'
            f' {self.tmdb_id}'
            f' {self.unaccented_title}'
            f' {self.release_year}'
            f' {self.runtime}'
            f' {self.summary}'
            f' {self.poster_path}'
            f' {self.imdb_rating}'
            f' {self.imdb_votes}'
        )
