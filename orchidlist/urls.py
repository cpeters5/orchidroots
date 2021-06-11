from django.urls import path
from . import views

# TODO: Add a new page: Compare two species/hybrids
# TODO: Add feature search page - search by color, features
# TODO: Add search by ancestors pair.
# TODO: Add search by location

app_name = 'orchidlist'
urlpatterns = [
    path('species/', views.information, name='information'),
    path('hybrid/', views.information, name='information'),
    path('browse/', views.browse, name='browse'),
]
