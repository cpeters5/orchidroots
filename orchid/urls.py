from django.urls import path
from . import views

app_name = 'orchid'
urlpatterns = [
    path('', views.orchid_home, name='orchid_home'),
    path('genera/', views.genera, name='genera'),  # -- All genera
    path('species/', views.all_species, name='species'),  # -- All species
    path('species_detail/<int:pid>/', views.species, name='species_detail'),
    path('hybrid_detail/<int:pid>/', views.hybrids, name='hybrid_detail'),
    path('<int:pid>/species_detail/', views.species, name='species_detail'),
    path('<int:pid>/hybrid_detail/', views.hybrids, name='hybrid_detail'),
    path('<int:pid>/family_tree/', views.family_tree, name='family_tree'),
    path('ancestor/', views.ancestor, name='ancestor'),
    path('progeny/', views.progeny, name='progeny'),
    path('search_match/', views.search_match, name='search_match'),
    path('browse/', views.browse, name='browse'),
]
