from django.urls import path, re_path
from . import views

app_name = 'orchidaceae'
urlpatterns = [
    # Top level
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
    path('browsegen/', views.browsegen, name='browsegen'),
    path('browse/', views.browse, name='browse'),
    path('browsedist/', views.browsedist, name='browsedist'),
]
