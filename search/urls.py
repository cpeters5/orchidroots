from django.urls import path, re_path
from . import views
app_name = 'search'
urlpatterns = [
    # If family is given,  find list of genera
    # If application is given, find list of families --> list of genera
    # then redirect to local search
    path('search/', views.search, name='search'),
    path('search_species/', views.search_species, name='search_species'),
    path('search_name/', views.search_name, name='search_name'),
    path('search_test/', views.search_test, name='search_test'),
    path('search_orchidaceae/', views.search_orchidaceae, name='search_orchidaceae'),

    # If neither family nor application, nor genus is given, then search across all tables for matching species

]
