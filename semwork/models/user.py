"""Module defining SQLAlchemy model of User."""

from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column

from semwork.extensions import db, bcrypt


class User(UserMixin, db.Model):
    """Class representing table User in database."""

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def __repr__(self):
        return f'<User {self.username}>'
