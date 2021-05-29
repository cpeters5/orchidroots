from django.urls import path
from . import views

# Documentations

app_name = 'documents'
urlpatterns = [
    # path('about/', views.about, name='about'),
    path('articles/', views.articles, name='articles'),
    path('bylaws/', views.bylaws, name='bylaws'),
    path('changes/', views.changes, name='changes'),
    path('contact/', views.contact, name='contact'),
    path('curator/', views.curator, name='curator'),
    path('development/', views.development, name='development'),
    path('datamodel/', views.datamodel, name='datamodel'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('faq/', views.faq, name='faq'),
    path('future_development/', views.future_development, name='future_development'),
    path('greetings/', views.greetings, name='greetings'),
    path('help/', views.help, name='help'),
    path('identinstruction/', views.identinstruction, name='identinstruction'),
    # path('instructionupload_curate/', views.instructionupload_curate, name='instructionupload_curate'),
    # path('instructionupload_private/', views.instructionupload_private, name='instructionupload_private'),
    # path('instructionupload_file/', views.instructionupload_file, name='instructionupload_file'),
    path('instructionupload/', views.instructionupload, name='instructionupload'),
    path('list/', views.list, name='list'),
    path('migration/', views.migration, name='migration'),
    path('maintenance/', views.maintenance, name='maintenance'),
    path('navigation/', views.navigation, name='navigation'),
    path('photosubmissionguideline/', views.photosubmissionguideline, name='photosubmissionguideline'),
    path('photoacquisionguideline/', views.photoacquisionguideline, name='photoacquisionguideline'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('req501c3/', views.req501c3, name='req501c3'),
    path('releasenote_v4/', views.releasenote_v4, name='releasenote_v4'),
    path('termsofuse/', views.termsofuse, name='termsofuse'),
    path('whoweare/', views.whoweare, name='whoweare'),

    # path('assets/$', views.assets, name='assets'),
    # path('copyright/', views.copyright, name='copyright'),
    # path('newrelease/', views.newrelease, name='newrelease'),
    # path('personnel/', views.personnel, name='personnel'),
    # path('project/', views.project, name='project'),
    # path('statistics/', views.statistics, name='statistics'),
    # path('submission/', views.photo_submission, name='submission'),
    # path('rvolunteer/', views.volunteer, name='volunteer'),
]
