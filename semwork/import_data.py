"""Module importing movies dataset."""

import csv

from semwork.models.movie import Movie


def load_dataset(db, file_name):
    """Import movies dataset and import to database."""

    with open(file_name, encoding='utf-8') as dataset:
        reader = csv.DictReader(dataset)
        lines_read = 0
        for row in reader:
            new_movie = Movie(
                name=row['Series_Title'],
                poster_link=row['Poster_Link'],
                release_year=row['Released_Year'],
                runtime=row['Runtime'],
                genre=row['Genre'],
                imdb_rating=row['IMDB_Rating'],
                summary=row['Overview'],
                director=row['Director'],
                star1=row['Star1'],
                star2=row['Star2'],
                star3=row['Star3'],
                star4=row['Star4'],
                no_of_votes=row['No_of_Votes'],
            )
            if row['Certificate']:
                new_movie.certificate = row['Certificate']
            if row['Meta_score']:
                new_movie.meta_score = row['Meta_score']
            if row['Gross']:
                new_movie.gross_earned = row['Gross'].replace(',', '').replace('\"', '')
            db.session.add(new_movie)
            db.session.commit()
            lines_read += 1
        print(f'Movies added: {lines_read}')
