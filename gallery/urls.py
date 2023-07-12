# from django.conf.urls import url, include
from django.urls import path
from . import views

app_name = 'gallery'
urlpatterns = [
    path('index/', views.index, name='index'),
    path('browse_gallery/', views.browse_gallery, name='browse_gallery'),
    path('my_gallery/', views.my_gallery, name='my_gallery'),
    path('browse_artist/', views.browse_artist, name='browse_artist'),
    path('photos/', views.photos, name='photos'),
    path('uploadfile/', views.uploadfile, name='uploadfile'),

]
