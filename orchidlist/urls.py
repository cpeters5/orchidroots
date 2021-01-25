# from django.conf.urls import url, include
from django.urls import path
from . import views

# TODO: Add a new page: Compare two species/hybrids
# TODO: Add feature search page - search by color, features
# TODO: Add search by ancestors pair.
# TODO: Add search by location

app_name = 'orchidlist'
urlpatterns = [
    # Lists
    path('family/', views.family, name='family'),
    path('subfamily/', views.subfamily, name='subfamily'),
    path('tribe/', views.tribe, name='tribe'),
    path('subtribe/', views.subtribe, name='subtribe'),
    path('genera/', views.genera, name='genera'),
    path('species/', views.species_list, name='species'),
    path('hybrid/', views.hybrid_list, name='hybrid'),
    path('progeny/<int:pid>/', views.progeny, name='progeny'),
    path('progeny/', views.progeny, name='progeny'),
    path('progenyimg/<int:pid>/', views.progenyimg, name='progenyimg'),
    path('progenyimg/', views.progenyimg, name='progenyimg'),
    path('subgenus/', views.subgenus, name='subgenus'),
    path('section/', views.section, name='section'),
    path('subsection/', views.subsection, name='subsection'),
    path('series/', views.series, name='series'),
    path('advanced/', views.advanced, name='advanced'),
    path('browsegen/', views.browsegen, name='browsegen'),
    path('browse/', views.browse, name='browse'),
    path('browsedist/', views.browsedist, name='browsedist'),

    # Legacy urls
]
