import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from reviews.models import GenreTitle, Category, Genre, Title, Review, Comment


User = get_user_model()


FILE_MODEL_FIELDS = [
    ('category.csv',
     Category,
     ['id', 'name', 'slug']),
    ('genre.csv',
     Genre,
     ['id', 'name', 'slug']),
    ('users.csv',
     User,
     ['id', 'username', 'email', 'role', 'bio', 'first_name', 'last_name']),
    ('titles.csv',
     Title,
     ['id', 'name', 'year', 'category_id']),
    ('genre_title.csv',
     GenreTitle,
     ['id', 'title_id', 'genre_id']),
    ('review.csv',
     Review,
     ['id', 'title_id', 'text', 'author_id', 'score', 'pub_date']),
    ('comments.csv',
     Comment,
     ['id', 'review_id', 'text', 'author_id', 'pub_date']),
]


def populate_model(reader, model, fields):
    items = []
    for row in reader:
        items.append(model(**dict(zip(fields, row))))
    model.objects.bulk_create(items)


class Command(BaseCommand):
    help = 'Имортировать файлы .csv из папки ./static/data/ в базу данных.'

    def handle(self, *args, **options):
        for file_name, model, fields in FILE_MODEL_FIELDS:
            path = './static/data/{}'.format(file_name)
            reader = csv.reader(open(path, 'r', encoding='utf-8'))
            next(reader)
            populate_model(reader, model, fields)
