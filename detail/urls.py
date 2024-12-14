from django.urls import path
from django.contrib.auth.decorators import login_required
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
    path('createhybrid/', login_required(views.createhybrid), name='createhybrid'),
    path('comment/', login_required(views.comment), name='comment'),
    path('comments/', login_required(views.comments), name='comments'),
    path('curateinfospc/<int:pid>/', login_required(views.curateinfospc), name='curateinfospc'),
    path('curateinfospc/', login_required(views.curateinfospc), name='curateinfospc'),
    path('curateinfohyb/<int:pid>/', login_required(views.curateinfohyb), name='curateinfohyb'),
    path('curateinfohyb/', login_required(views.curateinfohyb), name='curateinfohyb'),
    path('reidentify/<int:orid>/<int:pid>/', login_required(views.reidentify), name='reidentify'),
    path('uploadweb/<int:pid>/', login_required(views.uploadweb), name='uploadweb'),
    path('uploadweb/<int:pid>/<int:orid>/', login_required(views.uploadweb), name='uploadweb'),
    path('uploadfile/<int:pid>/', login_required(views.uploadfile), name='uploadfile'),

    # Legacy urls
    path('information/', views.information, name='redirect_information'),
    path('photos/', views.photos, name='redirect_photos'),
    path('ancestor/', login_required(views.ancestor), name='redirect_ancestor'),
    path('ancestrytree/', login_required(views.ancestrytree), name='redirect_ancestrytree'),

]
