from django.urls import path, re_path
from django.views.generic.base import RedirectView
from . import views

app_name = 'display'
urlpatterns = [
    path('summary/<str:app>/<int:pid>/', views.summary, name='summary'),
    path('summary/<int:pid>/', views.summary_tmp, name='summary_tmp'),
    path('photos/<str:app>/<int:pid>/', views.gallery, name='gallery'),
    path('photos/<int:pid>/', views.photos, name='photos'),
    path('videos/<int:pid>/', views.videos, name='videos'),

    # old path structure (no app present),
    path('information/<int:pid>/', views.information, name='information'),

]
