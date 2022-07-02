from django.urls import path, re_path
from . import views
app_name = 'search'
urlpatterns = [
    # All other domain
    path('search_species/', views.search_species, name='search_species'),
    # orchid domain only
    path('search_orchid/', views.search_orchid, name='search_orchid'),
    path('search_fuzzy/', views.search_fuzzy, name='search_fuzzy'),
]
