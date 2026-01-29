"""Importer for hugging face dataset containing movie details from TMDb."""

import os
import requests
from dotenv import load_dotenv

from moviedb.extensions import db
from moviedb.models.movie import Movie
from moviedb.models.company import Company
from moviedb.models.movie_production import MovieProduction
from .utils import tsv_rows_hf, preload_map

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

def import_movie_details_hf(path: str):

    session = db.session
    session.autoflush = False

    # preload maps for fast lookup
    movie_map = preload_map(Movie, Movie.imdb_id, Movie.id)
    company_map = preload_map(Company, Company.name, Company.id)

    updates = []
    productions_batch = []

    seen = set()
    i = 0

    for row in tsv_rows_hf(path):
        i += 1
        if (i % 50000 == 0):
            print(f"Processed: {i}")
        if len(row) != 29:
            print(row)
        (
            tmdb_id,
            title,
            vote_average,
            vote_count,
            status,
            release_date,
            revenue,
            runtime,
            adult,
            backdrop_path,
            budget,
            homepage,
            imdb_id,            # tconst
            original_language,
            original_title,
            overview,
            popularity,
            poster_path,
            tagline,
            genres,
            production_companies,
            production_countries,
            spoken_languages,
            keywords,
            directors,
            writers,
            average_rating,
            num_votes,
            cast
        ) = row

        movie_id = movie_map.get(imdb_id)
        if not movie_id:
            continue

        if movie_id in seen:
            print(f"Seen {movie_id}")
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
            params = {"api_key": API_KEY}
            try:
                r = requests.get(url, params=params, timeout=5)
                if r.status_code != 200:
                    continue
            except Exception:
                continue

        # -----------------
        # Movie updates
        # -----------------
        updates.append({
            "id": movie_id,
            "tmdb_id": int(tmdb_id) if tmdb_id else None,
            "backdrop_path": backdrop_path or "",
            "language": original_language or "",
            "summary": overview or "",
            "poster_path": poster_path or "",
            "tagline": tagline or "",
        })

        # -----------------
        # Production companies
        # -----------------
        if production_companies and movie_id not in seen:
            companies = { c.strip() for c in production_companies.split(",") if c.strip() }

            for name in companies:
                company_id = company_map.get(name)

                if not company_id:
                    company = Company(name=name)
                    session.add(company)
                    session.flush()  # get id without commit
                    company_id = company.id
                    company_map[name] = company_id

                productions_batch.append(
                    MovieProduction(
                        movie_id=movie_id,
                        company_id=company_id
                    )
                )
                seen.add(movie_id)

        # -----------------
        # Batch flush
        # -----------------
        if len(updates) >= 5000:
            session.bulk_update_mappings(Movie, updates)
            updates.clear()

        if len(productions_batch) >= 5000:
            session.bulk_save_objects(productions_batch)
            productions_batch.clear()

    # -----------------
    # Final commit
    # -----------------
    if updates:
        session.bulk_update_mappings(Movie, updates)

    if productions_batch:
        session.bulk_save_objects(productions_batch)

    session.commit()
