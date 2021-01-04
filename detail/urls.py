from django.urls import path
from . import views

# TODO: Add a new page: Compare two species/hybrids
# TODO: Add feature search page - search by color, features
# TODO: Add search by ancestors pair.
# TODO: Add search by location

app_name = 'detail'
urlpatterns = [
    # detail
    # path('selectspecies/<int:pid>/', views.selectspecies, name='selectspecies'),
    # path('nav/', views.nav, name='nav'),
    path('species/', views.information, name='information'),
    path('species/<int:pid>/', views.information, name='information'),
    path('hybrid/', views.information, name='information'),
    path('hybrid/<int:pid>/', views.information, name='information'),
    path('<int:pid>/species/', views.information, name='information'),
    path('<int:pid>/species_detail/', views.information, name='information'),
    path('<int:pid>/hybrid/', views.information, name='information'),
    path('<int:pid>/hybrid_detail/', views.information, name='information'),
    path('compare/<int:pid>/', views.compare, name='compare'),
    path('compare/', views.compare, name='compare'),
    path('createhybrid/', views.createhybrid, name='createhybrid'),
    path('information/<int:pid>/', views.information, name='information'),
    path('information/', views.information, name='information'),

    path('ancestor/', views.ancestor, name='ancestor'),
    path('ancestor/<int:pid>/', views.ancestor, name='ancestor'),
    path('ancestrytree/<int:pid>/', views.ancestrytree, name='ancestrytree'),
    path('ancestrytree/', views.ancestrytree, name='ancestrytree'),
    path('progeny/<int:pid>/', views.progeny, name='progeny'),
    path('progenyimg/<int:pid>/', views.progenyimg, name='progenyimg'),

    path('comment/', views.comment, name='comment'),
    path('comments/', views.comments, name='comments'),
    path('myphoto/<int:pid>/', views.myphoto, name='myphoto'),
    path('myphoto/', views.myphoto, name='myphoto'),
    path('myphoto_browse_spc/', views.myphoto_browse_spc, name='myphoto_browse_spc'),
    path('myphoto_browse_hyb/', views.myphoto_browse_hyb, name='myphoto_browse_hyb'),
    path('curate/<int:pid>/', views.curate, name='curate'),
    path('<int:pid>/photos/', views.photos, name='photos'),
    path('photos/<int:pid>/', views.photos, name='photos'),
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
    path('deletephoto/<int:orid>/', views.deletephoto, name='deletephoto'),
    path('deletewebphoto/<int:pid>/', views.deletewebphoto, name='deletewebphoto'),
    path('approvemediaphoto/<int:pid>/', views.approvemediaphoto, name='approvemediaphoto'),
]
