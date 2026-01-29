import tempfile
import click
from flask.cli import with_appcontext
from moviedb.extensions import db
from moviedb.importers import (
    import_genres,
    import_movies,
    import_people,
    import_movie_genres,
    import_ratings,
    import_crew,
    import_cast,
    import_certificates,
    import_movie_details,
    import_movie_details_hf
)
from moviedb.importers.utils import download_and_extract, cleanup
from moviedb.utils.ds_to_tsv import download_hf_to_tsv, remove_tsv



@click.command('import-imdb')
@click.option('--path', required=False, help='Path to IMDb TSV files')
@with_appcontext
def import_imdb(path):
    """Import IMDb datasets into the database."""
    click.echo('Creating tables...')
    db.create_all()

    download = False
    if not path:
        download = True
        tmp_dir = tempfile.mkdtemp()
        print(f"Temp dir: {tmp_dir}")
        path = tmp_dir

    # title.basics
    if download:
        click.echo("Downloading title.basics...")
        basics_path = download_and_extract("title.basics.tsv.gz", path)
    click.echo('Importing genres...')
    import_genres(path)
    click.echo('Importing movies...')
    import_movies(path)
    click.echo('Importing movie-genres...')
    import_movie_genres(path)
    if download:
        cleanup(basics_path)

    # name.basics
    # title.principals
    # title.crew
    if download:
        click.echo("Downloading name.basics...")
        people_path = download_and_extract("name.basics.tsv.gz", path)
        click.echo("Downloading title.principals...")
        cast_path = download_and_extract("title.principals.tsv.gz", path)
        click.echo("Downloading title.crew...")
        crew_path = download_and_extract("title.crew.tsv.gz", path)
    click.echo('Importing people...')
    import_people(path)
    click.echo('Importing cast...')
    import_cast(path)
    click.echo('Importing crew...')
    import_crew(path)
    if download:
        cleanup(people_path)
        cleanup(cast_path)
        cleanup(crew_path)

    # title.ratings
    if download:
        click.echo("Downloading title.ratings...")
        ratings_path = download_and_extract("title.ratings.tsv.gz", path)
    click.echo('Importing ratings...')
    import_ratings(path)
    if download:
        cleanup(ratings_path)

    #  title.akas
    if download:
        click.echo("Downloading title.akas...")
        cert_path = download_and_extract("title.akas.tsv.gz", path)
    click.echo('Importing certificates...')
    import_certificates(path)
    if download:
        cleanup(cert_path)

    click.echo('IMDb import complete')


@click.command('import-tmdb')
@click.option('--path', required=True, help='Path to TMDb TSV files')
@with_appcontext
def import_tmdb(path):
    """Import TMDb datasets into the database."""
    click.echo('Importing TMDb details...')
    import_movie_details(path)

    click.echo('TMDb import complete')


@click.command('import-tmdb-hf')
@click.option('--path', required=False, help='Path to TMDb TSV files')
@with_appcontext
def import_tmdb_hf(path):
    """Import TMDb datasets from Hugging face into the database."""

    download = False
    if not path:
        download = True
        tsv_path = download_hf_to_tsv()
        path = tsv_path
    click.echo('Importing TMDb details using HF...')
    import_movie_details_hf(path)
    if download:
        click.echo("Cleaning up TSV...")
        remove_tsv(path)

    click.echo('TMDb import complete')
