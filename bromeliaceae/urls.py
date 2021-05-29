# from django.conf.urls import url, include
from django.urls import path
from . import views

# TODO: Add a new page: Compare two species/hybrids
# TODO: Add feature search page - search by color, features
# TODO: Add search by ancestors pair.
# TODO: Add search by location

app_name = 'bromeliaceae'
urlpatterns = [
    path('compare/<int:pid>/', views.compare, name='compare'),
    # path('createhybrid/', views.createhybrid, name='createhybrid'),
    path('curateinfospc/<int:pid>/', views.curateinfospc, name='curateinfospc'),
    path('curateinfospc/', views.curateinfospc, name='curateinfospc'),
    path('curateinfohyb/<int:pid>/', views.curateinfohyb, name='curateinfohyb'),
    path('curateinfohyb/', views.curateinfohyb, name='curateinfohyb'),
    path('curate_newupload/', views.curate_newupload, name='curate_newupload'),
    path('curate_pending/', views.curate_pending, name='curate_pending'),
    path('curate_newapproved/', views.curate_newapproved, name='curate_newapproved'),
    path('reidentify/<int:orid>/<int:pid>/', views.reidentify, name='reidentify'),
    path('uploadfile/<int:pid>/', views.uploadfile, name='uploadfile'),
    path('uploadweb/<int:pid>/', views.uploadweb, name='uploadweb'),
    path('uploadweb/<int:pid>/<int:orid>/', views.uploadweb, name='uploadweb'),

]
