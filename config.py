"""App configuration module."""

import os

rootdir = os.path.abspath(os.path.dirname(__file__))


class Config: # pylint: disable=R0903; # flask config class used to only store data
    """Class representing app configuration."""

    SECRET_KEY = 'very_secret_key'
    SQLALCHEMY_DATABASE_URI = (
        'postgresql+psycopg2://admin_user:admin_pass@db:5432/admin_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DockerTestingConfig(Config): # pylint: disable=R0903; # flask config class used to only store data
    """Class representing app testing configuration for testing in Docker container."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        'postgresql+psycopg2://admin_user:admin_pass@db:5432/admin_db'
    )

class LocalTestingConfig(Config): # pylint: disable=R0903; # flask config class used to only store data
    """Class representing app testing configuration for testing using virtual env."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        'postgresql+psycopg2://admin_user:admin_pass@0.0.0.0:5432/admin_db'
    )
