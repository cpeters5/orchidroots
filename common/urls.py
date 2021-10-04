from django.urls import path, re_path
from . import views

app_name = 'common'
urlpatterns = [
    # Top level
    # path('', orchid_home, name='orchid_home'),
    # path('ode/<str:author>/', views.ode, name='ode'),

    # path('taxonomy/', views.taxonomy, name='taxonomy'),
    path('genera/', views.genera, name='genera'),
    path('species/', views.species, name='species'),
    path('hybrid/', views.hybrid, name='hybrid'),
    path('information/<int:pid>/', views.information, name='information'),
    path('photos/<int:pid>/', views.photos, name='photos'),
    path('photos/', views.photos, name='photos'),
    path('browse/', views.browse, name='browse'),

    path('search_gen/', views.search_gen, name='search_gen'),
    path('search_spc/', views.search_spc, name='search_spc'),
    path('search_hyb/', views.search, name='search_hyb'),
    path('search_species/', views.search_species, name='search_species'),
    path('search_orchid/', views.search_orchid, name='search_orchid'),
    path('search_fuzzy/', views.search_fuzzy, name='search_fuzzy'),
    path('search_match/', views.search_match, name='search_match'),
    path('search/', views.search, name='search'),

    path('deletephoto/<int:orid>/<int:pid>/', views.deletephoto, name='deletephoto'),
    path('deletewebphoto/<int:pid>/', views.deletewebphoto, name='deletewebphoto'),
    path('approvemediaphoto/<int:pid>/', views.approvemediaphoto, name='approvemediaphoto'),

    path('curate_newupload/', views.curate_newupload, name='curate_newupload'),
    path('curate_pending/', views.curate_pending, name='curate_pending'),
    path('curate_newapproved/', views.curate_newapproved, name='curate_newapproved'),

    path('myphoto/<int:pid>/', views.myphoto, name='myphoto'),
    path('myphoto/', views.myphoto, name='myphoto'),
    path('myphoto_list/', views.myphoto_list, name='myphoto_list'),
    path('myphoto_browse_spc/', views.myphoto_browse_spc, name='myphoto_browse_spc'),
    path('myphoto_browse_hyb/', views.myphoto_browse_hyb, name='myphoto_browse_hyb'),

]
