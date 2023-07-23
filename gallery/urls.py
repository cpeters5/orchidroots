# from django.conf.urls import url, include
from django.urls import path
from . import views

app_name = 'gallery'
urlpatterns = [
    path('', views.index, name='index'),
    path('browse_gallery/', views.browse_gallery, name='browse_gallery'),
    path('my_gallery/', views.my_gallery, name='my_gallery'),
    path('browse_artist/', views.browse_artist, name='browse_artist'),
    # path('photos/', views.photos, name='photos'),
    path('detail/<int:id>/', views.detail, name='detail'),
    path('uploadfile/', views.uploadfile, name='uploadfile'),
    path('updatefile/<int:id>/', views.updatefile, name='updatefile'),
    path('deletephoto/<int:id>/', views.deletephoto, name='deletephoto'),

]
