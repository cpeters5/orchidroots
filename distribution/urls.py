from django.urls import path
from . import views

app_name = 'distribution'
urlpatterns = [
    path('search/', views.search_distribution, name='search_distribution'),
    path('ajax/get_subregions/', views.get_subregions, name='get_subregions'),
]
