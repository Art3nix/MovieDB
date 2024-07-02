"""Home module init file."""

from flask import Blueprint

bp = Blueprint('home', __name__)

# according to official documentation this is intended
from semwork.home import routes  # pylint: disable=C0413; # noqa
