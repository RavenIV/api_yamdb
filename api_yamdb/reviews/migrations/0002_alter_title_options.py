# Generated by Django 3.2 on 2024-01-19 14:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='title',
            options={'default_related_name': 'titles', 'ordering': ('year',), 'verbose_name': 'Произведение', 'verbose_name_plural': 'Произведения'},
        ),
    ]