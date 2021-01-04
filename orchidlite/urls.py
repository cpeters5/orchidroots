from django.urls import path
from . import views

app_name = 'orchidlite'
urlpatterns = [
    # path('comment/', views.comment, name='comment'),
    path('', views.orchidlite_home, name='orchidlite_home'),

    path('genera/', views.genera, name='genera'),  # -- All genera
    path('species/', views.all_species, name='species'),  # -- All species

    path('search/', views.search, name='search'),
    path('species_detail/<int:pid>/', views.species, name='species_detail'),
    path('<int:pid>/species_detail/', views.species, name='species_detail'),
  	path('hybrid_detail/<int:pid>/', views.hybrids, name='hybrid_detail'),
  	path('<int:pid>/hybrid_detail/', views.hybrids, name='hybrid_detail'),

]

