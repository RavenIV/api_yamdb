import csv
import sqlite3

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from reviews.models import Category, Genre, Title, Review, Comment


User = get_user_model()


FILE_MODEL_TABLE_FIELDS = [
    ('category.csv',
     Category,
     False,
     ['id', 'name', 'slug']),
    ('genre.csv',
     Genre,
     False,
     ['id', 'name', 'slug']),
    ('users.csv',
     User,
     False,
     ['id', 'username', 'email', 'role', 'bio', 'first_name', 'last_name']),
    ('titles.csv',
     Title,
     False,
     ['id', 'name', 'year', 'category_id']),
    ('genre_title.csv',
     'reviews_title_genre',
     True,
     ['id', 'title_id', 'genre_id']),
    ('review.csv',
     Review,
     False,
     ['id', 'title_id', 'text', 'author_id', 'score', 'pub_date']),
    ('comments.csv',
     Comment,
     False,
     ['id', 'review_id', 'text', 'author_id', 'pub_date']),
]


def populate_model(reader, model, fields):
    items = []
    for row in reader:
        items.append(model(**dict(zip(fields, row))))
    model.objects.bulk_create(items)


def populate_table(reader, table, fields):
    con = sqlite3.connect('db.sqlite3')
    cur = con.cursor()
    values = ', '.join(['?' for i in range(len(fields))])
    fields = ', '.join(fields)
    cur.executemany(
        f'INSERT INTO {table}({fields}) VALUES({values});',
        [row for row in reader]
    )
    con.commit()
    con.close()


class Command(BaseCommand):
    help = 'Имортировать CSV-файлы из папки ./static/data/ в базу данных.'


    def handle(self, *args, **options):
        for file, name, is_table, fields in FILE_MODEL_TABLE_FIELDS:
            path = './static/data/{}'.format(file)
            reader = csv.reader(open(path, 'r', encoding='utf-8'))
            next(reader)
            if is_table:
                populate_table(reader, name, fields)
            else:
                populate_model(reader, name, fields)
