from django.urls import path, re_path
from . import views
from display.views import photos as display_photos, information as display_information
app_name = 'common'
urlpatterns = [
    # Top level
    path('family/<str:app>/', views.family, name='family'),
    # path('genera_orig/', views.genera_orig, name='genera_orig'),
    path('genera/<str:app>/', views.genera, name='genera'),
    path('species/<str:app>/', views.species, name='species'),
    path('distribution/', views.distribution, name='distribution'),
    path('newbrowse/<str:app>/', views.newbrowse, name='newbrowse'),
    path('newbrowse/', views.newbrowse, name='newbrowse'),
    path('taxonomy/<str:app>/', views.taxonomy, name='taxonomy'),

    # Redirect to display
    path('information/', display_information, name='information'),
    path('information/<int:pid>/', display_information, name='information'),
    path('photos/', display_photos, name='photos'),
    path('photos/<int:pid>/', display_photos, name='photos'),
    path('compare/<int:pid>/', views.compare, name='compare'),

    path('deletephoto/<int:orid>/<int:pid>/', views.deletephoto, name='deletephoto'),
    path('deletephoto/<int:orid>/', views.deletephoto, name='deletephoto'),
    path('deletewebphoto/<int:pid>/', views.deletewebphoto, name='deletewebphoto'),
    path('approvemediaphoto/<int:pid>/', views.approvemediaphoto, name='approvemediaphoto'),
    path('approvemediaphoto/', views.approvemediaphoto, name='approvemediaphoto'),
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
