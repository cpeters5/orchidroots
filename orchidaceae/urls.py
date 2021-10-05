from django.urls import path, re_path
from . import views
from display.views import photos as display_photos, information as display_information
from detail.views import reidentify as detail_reidentify, uploadfile as detail_uploadfile, \
    uploadweb as detail_uploadweb, curateinfospc as detail_curateinfospc, curateinfohyb as detail_curateinfohyb, \
    compare as detail_compare, createhybrid as detail_createhybrid


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
    path('progeny_old/<int:pid>/', views.progeny_old, name='progeny_old'),
    # path('progeny/', views.progeny, name='progeny'),
    path('progenyimg/<int:pid>/', views.progenyimg, name='progenyimg'),
    path('progenyimg/', views.progenyimg, name='progenyimg'),
    path('subgenus/', views.subgenus, name='subgenus'),
    path('section/', views.section, name='section'),
    path('subsection/', views.subsection, name='subsection'),
    path('series/', views.series, name='series'),
    # path('browsegen/', views.browsegen, name='browsegen'),

    # Redirect to display
    path('information/', display_information, name='information'),
    path('information/<int:pid>/', display_information, name='information'),
    path('photos/', display_photos, name='photos'),
    path('photos/<int:pid>/', display_photos, name='photos'),

    # Redirect to detail
    path('reidentify/<int:orid>/<int:pid>/', detail_reidentify, name='reidentify'),
    path('uploadfile/<int:pid>/', detail_uploadfile, name='uploadfile'),
    path('uploadweb/<int:pid>/', detail_uploadweb, name='uploadweb'),
    path('uploadweb/<int:pid>/<int:orid>/', detail_uploadweb, name='uploadweb'),
    path('curateinfospc/<int:pid>/', detail_curateinfospc, name='curateinfospc'),
    path('curateinfohyb/<int:pid>/', detail_curateinfohyb, name='curateinfohyb'),
    path('compare/<int:pid>/', detail_compare, name='compare'),
    path('createhybrid/', detail_createhybrid, name='createhybrid'),

]
