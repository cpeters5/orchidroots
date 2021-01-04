from django.urls import path
from . import views

app_name = 'natural'
urlpatterns = [
     path('<int:pid>/hyb_species/', views.hyb_species, name='hyb_species'),
     path('<int:pid>/acc_species/', views.acc_species, name='acc_species'),
     path('<int:pid>/species_detail/', views.species, name='species'),
  	 path('<int:pid>/hybrid_detail/', views.species, name='species'),
  	 path('<int:pid>/hybrid_detail/', views.species, name='species'),
  	 path('<int:pid>/family_tree/', views.family_tree, name='family_tree'),
  	 path('browse/', views.browse, name='browse'),

]

