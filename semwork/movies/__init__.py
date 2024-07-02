"""Movies module init file."""

from flask import Blueprint

bp = Blueprint('movies', __name__)

# according to official documentation this is intended
from semwork.movies import routes  # pylint: disable=C0413; # noqa
