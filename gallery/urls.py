# from django.conf.urls import url, include
from django.urls import path
from . import views

app_name = 'gallery'
urlpatterns = [
    path('index/', views.index, name='index'),
    # path('result/', views.result, name='result'),

]
