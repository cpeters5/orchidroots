from django.urls import path, re_path
from . import views

app_name = 'core'
urlpatterns = [
    # Top level
    path('family/', views.family, name='family'),
    path('subfamily/', views.subfamily, name='subfamily'),
    path('tribe/', views.tribe, name='tribe'),
    path('subtribe/', views.subtribe, name='subtribe'),
]
