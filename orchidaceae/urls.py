from django.urls import path, re_path
from django.contrib.auth.decorators import login_required
from . import views
from detail.views import (reidentify as detail_reidentify, uploadfile as detail_uploadfile, \
    uploadweb as detail_uploadweb, curateinfospc as detail_curateinfospc, curateinfohyb as detail_curateinfohyb, \
    compare as detail_compare, createhybrid as detail_createhybrid)
#, approvemediaphoto as detail_approvemediaphoto)


app_name = 'orchidaceae'
urlpatterns = [
    # Top level
    path('', views.genera, name='genera'),
    path('genera/', views.genera, name='genera'),
    path('species/', login_required(views.species), name='species'),
    path('hybrid/', login_required(views.hybrid), name='hybrid'),
    path('ancestor/', login_required(views.ancestor), name='ancestor'),
    path('ancestor/<int:pid>/', login_required(views.ancestor), name='ancestor'),
    path('ancestrytree/<int:pid>/', login_required(views.ancestrytree), name='ancestrytree'),
    path('ancestrytree/', login_required(views.ancestrytree), name='ancestrytree'),
    path('distribution/<int:pid>/', views.distribution, name='distribution'),
    path('progeny/<int:pid>/', login_required(views.progeny), name='progeny'),
    path('progenyimg/<int:pid>/', login_required(views.progenyimg), name='progenyimg'),
    path('progenyimg/', login_required(views.progenyimg), name='progenyimg'),
    path('subgenus/', views.subgenus, name='subgenus'),
    path('section/', views.section, name='section'),
    path('subsection/', views.subsection, name='subsection'),
    path('series/', views.series, name='series'),
    # path('synonym/<int:pid>/', views.synonym, name='synonym'),  # moved to common
    # path('browsegen/', views.browsegen, name='browsegen'),

    # Redirect to detail
    path('reidentify/<int:orid>/<int:pid>/', login_required(detail_reidentify), name='reidentify'),
    path('uploadweb/<int:pid>/', login_required(detail_uploadweb), name='uploadweb'),
    path('uploadweb/<int:pid>/<int:orid>/', login_required(detail_uploadweb), name='uploadweb'),
    path('uploadfile/<int:pid>/', login_required(detail_uploadfile), name='uploadfile'),
    # path('approvemediaphoto/<int:pid>/', detail_approvemediaphoto, name='approvemediaphoto'),

    path('curateinfospc/<int:pid>/', login_required(detail_curateinfospc), name='curateinfospc'),
    path('curateinfohyb/<int:pid>/', login_required(detail_curateinfohyb), name='curateinfohyb'),
    path('compare/<int:pid>/', detail_compare, name='compare'),
    path('createhybrid/', login_required(detail_createhybrid), name='createhybrid'),

]
