"""Module defining SQLAlchemy model of Movie."""

import unicodedata

from sqlalchemy.orm import Mapped, mapped_column

from semwork.extensions import db


class Movie(db.Model):  # pylint: disable=R0902,R0903; # sqlalchemy class used to only store data
    """Class representing table Movie in database."""

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    unaccented_name: Mapped[str]
    poster_link: Mapped[str]
    release_year: Mapped[int]
    certificate: Mapped[str] = mapped_column(nullable=True)
    runtime: Mapped[str]
    genre: Mapped[str]
    imdb_rating: Mapped[float]
    summary: Mapped[str]
    meta_score: Mapped[int] = mapped_column(nullable=True)
    director: Mapped[str]
    star1: Mapped[str]
    star2: Mapped[str]
    star3: Mapped[str]
    star4: Mapped[str]
    no_of_votes: Mapped[int]
    gross_earned: Mapped[int] = mapped_column(nullable=True)

    def __init__(
        self,
        name: str,
        poster_link: str,
        release_year: int,
        runtime: str,
        genre: str,
        imdb_rating: float,
        summary: str,
        director: str,
        star1: str,
        star2: str,
        star3: str,
        star4: str,
        no_of_votes: int,
    ):  # pylint: disable=R0913; # related to previous warnings
        self.name = name
        self.unaccented_name = unicodedata.normalize('NFD', name).encode('ASCII', 'ignore').decode("utf-8")
        self.poster_link = poster_link
        self.release_year = release_year
        self.runtime = runtime
        self.genre = genre
        self.imdb_rating = imdb_rating
        self.summary = summary
        self.director = director
        self.star1 = star1
        self.star2 = star2
        self.star3 = star3
        self.star4 = star4
        self.no_of_votes = no_of_votes

    def __repr__(self):
        return (
            f'<Movie {self.name}>'
            f' {self.unaccented_name}'
            f' {self.poster_link}'
            f' {self.release_year}'
            f' {self.runtime}'
            f' {self.genre}'
            f' {self.imdb_rating}'
            f' {self.summary}'
            f' {self.director}'
            f' {self.star1}'
            f' {self.star2}'
            f' {self.star3}'
            f' {self.star4}'
            f' {self.no_of_votes}'
        )
