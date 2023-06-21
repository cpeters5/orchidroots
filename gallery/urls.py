# from django.conf.urls import url, include
from django.urls import path
from . import views

app_name = 'gallery'
urlpatterns = [
    path('index/', views.index, name='index'),
    path('browse_artist/', views.browse_artist, name='browse_artist'),
    path('photos/', views.photos, name='photos'),
    path('uploadfile/', views.uploadfile, name='uploadfile'),

]
