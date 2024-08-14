from django.urls import path, re_path
from . import views

app_name = 'display'
urlpatterns = [
    path('<int:pid>/', views.information, name='information'),
    path('information/<int:pid>/', views.information, name='information'),
    path('information/', views.information, name='information'),
    path('photos/<int:pid>/', views.photos, name='photos'),
    path('photos/', views.photos, name='photos'),
    path('videos/<int:pid>/', views.videos, name='videos'),
]
