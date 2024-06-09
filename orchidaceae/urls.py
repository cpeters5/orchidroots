from django.urls import path, re_path
from . import views
from display.views import photos as display_photos, information as display_information
from detail.views import reidentify, uploadfile, uploadweb, curateinfospc, curateinfohyb, \
    compare, createhybrid, approvemediaphoto


app_name = 'orchidaceae'
urlpatterns = [
    # Top level
    path('', views.genera, name='genera'),
    path('genera/', views.genera, name='genera'),
    path('species/', views.species, name='species'),
    path('hybrid/', views.hybrid, name='hybrid'),
    path('ancestor/', views.ancestor, name='ancestor'),
    path('ancestor/<int:pid>/', views.ancestor, name='ancestor'),
    path('ancestrytree/<int:pid>/', views.ancestrytree, name='ancestrytree'),
    path('progeny/<int:pid>/', views.progeny, name='progeny'),
    path('progenyimg/<int:pid>/', views.progenyimg, name='progenyimg'),
    path('subgenus/', views.subgenus, name='subgenus'),
    path('section/', views.section, name='section'),
    path('subsection/', views.subsection, name='subsection'),
    path('series/', views.series, name='series'),

]
