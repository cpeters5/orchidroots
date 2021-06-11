from django.urls import path, re_path
from . import views

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
    path('ancestrytree/', views.ancestrytree, name='ancestrytree'),
    path('progeny/<int:pid>/', views.progeny, name='progeny'),
    # path('progeny/', views.progeny, name='progeny'),
    path('progenyimg/<int:pid>/', views.progenyimg, name='progenyimg'),
    path('progenyimg/', views.progenyimg, name='progenyimg'),
    path('subgenus/', views.subgenus, name='subgenus'),
    path('section/', views.section, name='section'),
    path('subsection/', views.subsection, name='subsection'),
    path('series/', views.series, name='series'),
    # path('browsegen/', views.browsegen, name='browsegen'),

    # Redirect to detail
    path('information/<int:pid>/', views.information, name='information'),
    path('photos/<int:pid>/', views.photos, name='photos'),
    path('reidentify/<int:orid>/<int:pid>/', views.reidentify, name='reidentify'),
    path('uploadfile/<int:pid>/', views.uploadfile, name='uploadfile'),
    path('uploadweb/<int:pid>/', views.uploadweb, name='uploadweb'),
    path('uploadweb/<int:pid>/<int:orid>/', views.uploadweb, name='uploadweb'),
    path('curateinfospc/<int:pid>/', views.curateinfospc, name='curateinfospc'),
    path('curateinfohyb/<int:pid>/', views.curateinfohyb, name='curateinfohyb'),
    path('compare/<int:pid>/', views.compare, name='compare'),
    path('createhybrid/', views.createhybrid, name='createhybrid'),

]
