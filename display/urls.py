from django.urls import path, re_path
from django.views.generic.base import RedirectView
from . import views

app_name = 'display'
urlpatterns = [
    path('summary/<str:app>/<int:pid>/', views.summary, name='summary'),
    path('summary/<int:pid>/', views.summary, name='summary_with_pid'),
    path('summary/<str:app>/', views.summary, name='summary_with_app'),
    path('summary/', views.summary, name='summary_with_nothing'),

    path('photos/<str:app>/<int:pid>/', views.photos, name='photos'),
    path('photos/<int:pid>/', views.photos, name='photos_with_pid'),
    path('photos/', views.photos, name='photos_no_pid'),
    path("photos/<int:pid>/flag/", views.flag_image, name="flag_image"), # Currently orchidaceae only

    path('videos/<int:pid>/', views.videos, name='videos'),

    # Legacy url
    path('information/<int:pid>/', views.summary, name='information_with_pid'),

]
