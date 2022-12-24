from django.urls import path, re_path
from . import views
app_name = 'search'
urlpatterns = [
    path('search/', views.search, name='search'),
    # All other domain
    # path('search_species/', views.search_species, name='search_species'),
    # orchid domain only
    path('search_orchid/', views.search_orchid, name='search_orchid'),
    path('search_other/', views.search_other, name='search_other'),
    path('search_fungi/', views.search_fungi, name='search_fungi'),
    path('search_species/', views.search_species, name='search_species'),       # only epithet name is given.
    path('search_fuzzy/', views.search_fuzzy, name='search_fuzzy'),
]
