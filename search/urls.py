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

    # Local search: Based on family(families) found, search for matching species
    # path('search_orchid/', views.search_orchid, name='search_orchid'),
    # path('search_other/', views.search_other, name='search_other'),
    # path('search_fungi/', views.search_fungi, name='search_fungi'),
    # path('search_aves/', views.search_aves, name='search_aves'),
    # path('search_animalia/', views.search_animalia, name='search_animalia'),
    path('search_fuzzy/', views.search_fuzzy, name='search_fuzzy'),

    # If neither family nor application, nor genus is given, then search across all tables for matching species

]
