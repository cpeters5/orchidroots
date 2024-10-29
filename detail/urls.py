from django.urls import path
from . import views
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

    # Legacy urls
    path('information/', views.information, name='redirect_information'),
    path('photos/', views.photos, name='redirect_photos'),
    path('ancestor/', views.ancestor, name='redirect_ancestor'),
    path('ancestrytree/', views.ancestrytree, name='redirect_ancestrytree'),

]
