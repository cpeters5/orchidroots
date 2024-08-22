from django.urls import path, re_path
from django.views.generic.base import RedirectView
from . import views

app_name = 'display'
urlpatterns = [
    path('summary/<str:application>/<int:pid>/', views.summary, name='summary'),
    path('information/<str:application>/<int:pid>/', RedirectView.as_view(pattern_name='display:summary', permanent=True)),
    # path('information/<str:application>/<int:pid>/', views.information_tmp, name='information_tmp'),

    path('information/<int:pid>/', RedirectView.as_view(pattern_name='display:photos', permanent=True)),
    path('photos/<int:pid>/', views.photos, name='photos'),

    path('videos/<int:pid>/', views.videos, name='videos'),
    # path('<int:pid>/', views.information_tmp1, name='information_tmp1'),

]
