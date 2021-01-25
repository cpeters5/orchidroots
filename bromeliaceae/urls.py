# from django.conf.urls import url, include
from django.urls import path
from . import views

# TODO: Add a new page: Compare two species/hybrids
# TODO: Add feature search page - search by color, features
# TODO: Add search by ancestors pair.
# TODO: Add search by location

app_name = 'bromeliaceae'
urlpatterns = [
    # Lists
    path('advanced/', views.advanced, name='advanced'),
    path('genera/', views.genera, name='genera'),
    path('species/', views.species_list, name='species'),
    path('hybrid/', views.hybrid_list, name='hybrid'),
    # path('browsegen/', views.browsegen, name='browsegen'),
    # path('browse/', views.browse, name='browse'),
    # path('browsedist/', views.browsedist, name='browsedist'),
    # path('search_match/', views.search_match, name='search_match'),
    # path('search_fuzzy/', views.search_fuzzy, name='search_fuzzy'),
    # path('species/', views.information, name='information'),
    # path('hybrid/', views.information, name='information'),
    # path('photos/', views.photos, name='photos'),
    # path('myphoto/', views.myphoto, name='myphoto'),
    # path('myphoto_browse_spc/', views.myphoto_browse_spc, name='myphoto_browse_spc'),
    # path('uploadfile/<int:pid>/', views.uploadfile, name='uploadfile'),
    # path('uploadweb/<int:pid>/', views.uploadweb, name='uploadweb'),
    # path('uploadweb/<int:pid>/<int:orid>/', views.uploadweb, name='uploadweb'),
    # path('deletephoto/<int:orid>/', views.deletephoto, name='deletephoto'),
    # path('deletewebphoto/<int:pid>/', views.deletewebphoto, name='deletewebphoto'),
    # path('approvemediaphoto/<int:pid>/', views.approvemediaphoto, name='approvemediaphoto'),

]
