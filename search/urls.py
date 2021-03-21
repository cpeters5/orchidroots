from django.urls import path, re_path
from . import views

app_name = 'search'
urlpatterns = [
    # Top level
    path('taxonomy/', views.taxonomy, name='taxonomy'),
    path('advanced/', views.advanced, name='advanced'),
    path('search_genus/', views.search_genus, name='search_genus'),
    path('search_match/', views.search_match, name='search_match'),
    path('search_fuzzy/', views.search_fuzzy, name='search_fuzzy'),
]
