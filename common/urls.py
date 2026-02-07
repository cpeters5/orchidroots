from django.urls import path, re_path
from . import views
app_name = 'common'
urlpatterns = [
    # Top level
    path('taxonomy/<str:app>/', views.taxonomy, name='taxonomy'),
    path('taxonomy/', views.taxonomy, name='taxonomy'),
    path('family/<str:app>/', views.family, name='family'),
    path('family/', views.family, name='family'),
    path('genera/<str:app>/', views.genera, name='genera'),
    path('genera/', views.genera, name='genera'),
    path('species/<str:app>/', views.species, name='species'),
    path('species/', views.species, name='species'),
    path('synonym/<str:app>/<int:pid>/', views.synonym, name='synonym'),
    path('distribution/<str:app>/<int:pid>/', views.distribution, name='distribution'),

    # path('distribution/', views.distribution, name='distribution'),
    path('newbrowse/', views.newbrowse, name='newbrowse'),
    path('newbrowse/<str:app>/', views.newbrowse, name='newbrowse'),
    path('compare/<int:pid>/', views.compare, name='compare'),
    path('newcross/<int:pid1>/<int:pid2>/', views.newcross, name='newcross'),

    # Redirect to canonicalurl
    path('hybrid/<str:app>/', views.hybrid, name='hybrid'),

    path('deletephoto/<int:orid>/<int:pid>/', views.deletephoto, name='deletephoto'),
    path('deletephoto/<int:orid>/', views.deletephoto, name='deletephoto'),
    path('refresh/<int:pid>/', views.refresh, name='refresh'),
    path('deletewebphoto/<int:pid>/', views.deletewebphoto, name='deletewebphoto'),
    path('approve_mediaphoto/<str:app>/<int:orid>/<int:pid>/', views.approve_mediaphoto, name='approve_mediaphoto'),
    path('uploadfile/<int:pid>/', views.uploadfile, name='uploadfile'),
    path('get_new_uploads/', views.get_new_uploads, name='get_new_uploads'),

    path('curate_newupload/', views.curate_newupload, name='curate_newupload'),
    path('curate_pending/', views.curate_pending, name='curate_pending'),
    path('curate_newapproved/', views.curate_newapproved, name='curate_newapproved'),

    path('myphoto/<int:pid>/', views.myphoto, name='myphoto'),
    path('myphoto/', views.myphoto, name='myphoto'),
    path('myphoto_list/', views.myphoto_list, name='myphoto_list'),
    path('myphoto_browse_spc/', views.myphoto_browse_spc, name='myphoto_browse_spc'),
    path('myphoto_browse_hyb/', views.myphoto_browse_hyb, name='myphoto_browse_hyb'),

]
