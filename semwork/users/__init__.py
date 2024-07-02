"""Users module init file."""

from flask import Blueprint

bp = Blueprint('users', __name__)

# according to official documentation this is intended
from semwork.users import routes  # pylint: disable=C0413; # noqa
