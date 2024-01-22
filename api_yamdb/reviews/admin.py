from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User, Category, Genre, Title, Review, Comment
)

UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('bio', 'role')}),
)
admin.site.register(User, UserAdmin)
admin.site.register(Category)
admin.site.register(Genre)
admin.site.register(Title)
admin.site.register(Review)
admin.site.register(Comment)
