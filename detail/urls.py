from django.urls import path
from . import views
from display.views import photos as display_photos, information as display_information
from orchidaceae.views import ancestor as orchidaceae_ancestor, ancestrytree as orchidaceae_ancestrytree, \
    progeny as orchidaceae_progeny, progenyimg as orchidaceae_progenyimg


# TODO: Add a new page: Compare two species/hybrids
# TODO: Add feature search page - search by color, features
# TODO: Add search by ancestors pair.
# TODO: Add search by location

app_name = 'detail'
urlpatterns = [
    # detail
    path('compare/<int:pid>/', views.compare, name='compare'),
    path('compare/', views.compare, name='compare'),
    path('createhybrid/', views.createhybrid, name='createhybrid'),
    path('comment/', views.comment, name='comment'),
    path('comments/', views.comments, name='comments'),
    path('curateinfospc/<int:pid>/', views.curateinfospc, name='curateinfospc'),
    path('curateinfospc/', views.curateinfospc, name='curateinfospc'),
    path('curateinfohyb/<int:pid>/', views.curateinfohyb, name='curateinfohyb'),
    path('curateinfohyb/', views.curateinfohyb, name='curateinfohyb'),
    path('reidentify/<int:orid>/<int:pid>/', views.reidentify, name='reidentify'),
    path('uploadweb/<int:pid>/', views.uploadweb, name='uploadweb'),
    path('uploadweb/<int:pid>/<int:orid>/', views.uploadweb, name='uploadweb'),
    path('uploadfile/<int:pid>/', views.uploadfile, name='uploadfile'),
    path('approvemediaphoto/<int:pid>/', views.approvemediaphoto, name='approvemediaphoto'),

    # Redirect to orchidaceae
    path('ancestor/<int:pid>/', orchidaceae_ancestor, name='ancestor'),
    path('ancestor/', orchidaceae_ancestor, name='ancestor'),
    path('ancestrytree/<int:pid>/', orchidaceae_ancestrytree, name='ancestrytree'),
    path('ancestrytree/', orchidaceae_ancestrytree, name='ancestrytree'),
    path('progeny/<int:pid>/', orchidaceae_progeny, name='progeny'),
    path('progenyimg/<int:pid>/', orchidaceae_progenyimg, name='progenyimg'),

    # Redirect to display
    path('information/', display_information, name='information'),
    path('information/<int:pid>/', display_information, name='information'),
    path('photos/', display_photos, name='photos'),
    path('photos/<int:pid>/', display_photos, name='photos'),
    path('species/<int:pid>/', display_information, name='information'),
    path('hybrid/<int:pid>/', display_information, name='information'),
    path('<int:pid>/hybrid/', display_information, name='information'),
    path('<int:pid>/species/', display_information, name='information'),
    path('species_detail/<int:pid>/', display_information, name='information'),
    path('hybrid_detail/<int:pid>/', display_information, name='information'),
    path('<int:pid>/species_detail/', display_information, name='information'),
    path('<int:pid>/hybrid_detail/', display_information, name='information'),
]
