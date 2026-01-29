"""App init file."""

from flask import Flask
from dotenv import load_dotenv
from config import Config

from moviedb.extensions import db, bcrypt, login_manager, migrate
from moviedb.models.movie import Movie
from moviedb.models.user import User
from moviedb.import_data import load_dataset
from moviedb.cli import import_imdb, import_tmdb, import_tmdb_hf

from moviedb.utils.filters import tmdb_image

from moviedb.home import bp as home_bp
from moviedb.users import bp as users_bp
from moviedb.movies import bp as movies_bp

load_dotenv()

def create_app(config_class=Config):
    """Create and initialize instance of the app."""

    app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')
    app.config.from_object(config_class)

    # Register CLI
    app.cli.add_command(import_imdb)
    app.cli.add_command(import_tmdb)
    app.cli.add_command(import_tmdb_hf)

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
            pass #load_dataset(db, 'imdb_top_1000.csv')

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register filters
    app.add_template_filter(tmdb_image)

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(movies_bp, url_prefix='/movies')

    return app
