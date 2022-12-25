from django.urls import path, re_path
from . import views
from display.views import photos as display_photos, information as display_information
app_name = 'common'
urlpatterns = [
    # Top level
    # path('taxonomy/', views.taxonomy, name='taxonomy'),
    path('genera/', views.genera, name='genera'),
    path('species/', views.species, name='species'),
    path('hybrid/', views.hybrid, name='hybrid'),
    # path('commonname/', views.commonname, name='commonname'),
    path('distribution/', views.distribution, name='distribution'),
    path('browsegen/', views.browsegen, name='browsegen'),
    path('browse/', views.browse, name='browse'),
    path('taxonomy/', views.taxonomy, name='taxonomy'),

    # Redirect to display
    path('information/', display_information, name='information'),
    path('information/<int:pid>/', display_information, name='information'),
    path('photos/', display_photos, name='photos'),
    path('photos/<int:pid>/', display_photos, name='photos'),

    # path('search/', views.search, name='search'),
    path('research/', views.research, name='research'),

    path('deletephoto/<int:orid>/<int:pid>/', views.deletephoto, name='deletephoto'),
    path('deletewebphoto/<int:pid>/', views.deletewebphoto, name='deletewebphoto'),
    path('approvemediaphoto/<int:pid>/', views.approvemediaphoto, name='approvemediaphoto'),

    path('curate_newupload/', views.curate_newupload, name='curate_newupload'),
    path('curate_pending/', views.curate_pending, name='curate_pending'),
    path('curate_newapproved/', views.curate_newapproved, name='curate_newapproved'),

    # Only works for orchidaceae.
    path('uploadfile/<int:pid>/', views.uploadfile, name='uploadfile'),

    # upload from web threw error (species is not an instance)
    path('uploadcommonweb/<int:pid>/', views.uploadcommonweb, name='uploadcommonweb'),
    path('uploadcommonweb/<int:pid>/<int:orid>/', views.uploadcommonweb, name='uploadcommonweb'),

    path('myphoto/<int:pid>/', views.myphoto, name='myphoto'),
    path('myphoto/', views.myphoto, name='myphoto'),
    path('myphoto_list/', views.myphoto_list, name='myphoto_list'),
    path('myphoto_browse_spc/', views.myphoto_browse_spc, name='myphoto_browse_spc'),
    path('myphoto_browse_hyb/', views.myphoto_browse_hyb, name='myphoto_browse_hyb'),

]
