"""Module defining SQLAlchemy model of Rating."""

from typing_extensions import Annotated
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from semwork.extensions import db

IntPk = Annotated[int, mapped_column(primary_key=True)]


class Rating(db.Model):  # pylint: disable=R0903; # sqlalchemy class used to only store data
    """Class representing table Rating in database.
    Currently unused.
    """

    user_id: Mapped[IntPk] = mapped_column(ForeignKey('user.id'))
    movie_id: Mapped[IntPk] = mapped_column(ForeignKey('movie.id'))
    value: Mapped[float]

    def __repr__(self):
        return f'<Rating {self.value}>'
