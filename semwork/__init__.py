"""App init file."""

from flask import Flask
from config import Config

from semwork.extensions import db, bcrypt, login_manager, migrate
from semwork.models.movie import Movie
from semwork.models.user import User
from semwork.import_data import load_dataset

from semwork.home import bp as home_bp
from semwork.users import bp as users_bp
from semwork.movies import bp as movies_bp


def create_app(config_class=Config):
    """Create and initialize instance of the app."""
    app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')
    app.config.from_object(config_class)

    # Initialize db
    db.init_app(app)

    # Initialize migration
    migrate.init_app(app, db)

    # Initialize Bcrypt
    bcrypt.init_app(app)

    # Initialize LoginManager
    login_manager.login_view = 'users.login'
    login_manager.init_app(app)

    # Import movies from given dataset
    with app.app_context():
        db.create_all()
        if db.session.query(Movie).count() == 0:
            load_dataset(db, 'imdb_top_1000.csv')

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(movies_bp, url_prefix='/movies')

    return app
