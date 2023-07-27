from django.contrib import admin
from .models import (City, Artist, Medium, Genre, Artwork)
# Register your models here.

admin.autodiscover()
admin.site.enable_nav_sidebar = False

class CityAdmin(admin.ModelAdmin):
    pass
    list_display = ('city',)
    list_filter = ('city',)
    fields = [('city', 'description',)]
    ordering = ['city']
    search_fields = ['city', 'description']

class ArtistAdmin(admin.ModelAdmin):
    pass
    list_display = ('artist', 'user_id', 'media', 'genre')
    list_filter = ('artist', 'media', 'genre',)
    fields = [('artist', 'user_id',), ('address', 'url', 'profile_pic_path',), ('media', 'genre',)]
    ordering = ['artist']
    search_fields = ['artist', 'user_id', 'media', 'genre']


class MediumAdmin(admin.ModelAdmin):
    pass
    list_display = ('medium',)
    list_filter = ('medium',)
    fields = [('medium', 'description',)]
    ordering = ['medium']
    search_fields = ['medium', 'description']


class GenreAdmin(admin.ModelAdmin):
    pass
    list_display = ('genre',)
    list_filter = ('genre',)
    fields = [('genre', 'description',)]
    ordering = ['genre']
    search_fields = ['genre', 'description']

class ArtworkAdmin(admin.ModelAdmin):
    pass
    list_display = ('artist', 'medium', 'genre', 'name', 'support', 'price', 'status', 'rank', )
    list_filter = ('artist','medium', 'genre',)
    fields = [('artist', 'medium', 'genre', 'status', 'rank',), ('name', 'support', 'hashtag', 'style',), ('price', 'source_url', 'date', 'description')]
    ordering = ['artist', 'medium', 'genre']
    search_fields = ['artist', 'medium', 'genre']



admin.site.register(City, CityAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Medium, MediumAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Artwork, ArtworkAdmin)
