from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.sitemaps.views import sitemap, index
# from django.contrib.sitemaps.views import index as sitemap_index
from django.views.generic import TemplateView
from django.views.generic.base import TemplateView, RedirectView
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import  user_reset_password, login_page, register_page, UpdateProfileView, SetEmailView,\
    ChangeEmailView, PasswordChangeRedirect, CustomPasswordResetFromKeyView
from common.views import home
from . import views
from myproject.views import robots_txt
from sitemap.views import sitemap_index, sitemap_section

urlpatterns = [
    # admin & sitemaps
    path('admin/', admin.site.urls),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),
    path('sitemap.xml', sitemap_index, name='sitemap_index'),
    path('sitemap-<int:section>.xml', sitemap_section, name='sitemap_section'),

    # home
    path('', home, name='home'),

    # User accounts
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('set_email/', SetEmailView.as_view(), name='set_email'),
    path('change_email/', ChangeEmailView.as_view(), name='change_email'),
    path('update_profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('logout/', LogoutView.as_view(), {'next_page': '//'}, name='logout'),
    path('accounts/', include('allauth.urls')),
    path('accounts/password/change/', PasswordChangeRedirect.as_view(), name="account_password_change"),
    path('accounts/password/user_reset_password/', user_reset_password, name="user_account_reset_password"),
    re_path(
        r"accounts/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        CustomPasswordResetFromKeyView.as_view(),
        name="account_reset_password_from_key",
    ),

    # my applications
    path('donation/', include(('donation.urls', 'donation'), namespace='donation')),
    path('documents/', include(('documents.urls', 'documents'), namespace='documents')),

    # Common applications
    path('search/', include(('search.urls', 'search'), namespace='search')),
    path('common/', include(('common.urls', 'common'), namespace='common')),
    path('display/', include(('display.urls', 'display'), namespace='display')),

    # Family specific
    path('animalia/', include(('animalia.urls', 'animalia'), namespace='animalia')),
    path('aves/', include(('aves.urls', 'aves'), namespace='aves')),
    path('fungi/', include(('fungi.urls', 'fungi'), namespace='fungi')),
    path('other/', include(('other.urls', 'other'), namespace='other')),
    path('orchidaceae/', include(('orchidaceae.urls', 'orchidaceae'), namespace='orchidaceae')),
    path('detail/', include(('detail.urls', 'detail'), namespace='detail')),

    # REDIRECTIONS: Remove this in a year or so. @2024
    # redirections (in the process of merging detail with orchidaceae)
    path('detail/ancestor/<int:pid>/', RedirectView.as_view(url='/orchidaceae/ancestor/%(pid)s/', permanent=True)),
    path('detail/ancestor/', RedirectView.as_view(url='/orchidaceae/ancestor/', permanent=True)),
    path('detail/ancestrytree/<int:pid>/', RedirectView.as_view(url='/orchidaceae/ancestrytree/%(pid)s/', permanent=True)),
    path('detail/ancestrytree/', RedirectView.as_view(url='/orchidaceae/ancestrytree/', permanent=True)),
    path('detail/progeny/<int:pid>/', RedirectView.as_view(url='/orchidaceae/progeny/%(pid)s/', permanent=True)),
    path('detail/progenyimg/<int:pid>/', RedirectView.as_view(url='/orchidaceae/progenyimg/%(pid)s/', permanent=True)),

    # path('detail/information/<int:pid>/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('information/<int:pid>/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/information/', RedirectView.as_view(url='/display/summary/', permanent=True)),
    path('orchidaceae/information/<int:pid>/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/photos/<int:pid>/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/photos/', RedirectView.as_view(url='/display/photos/orchidaceae/', permanent=True)),
    path('orchidaceae/photos/<int:pid>/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/species/<int:pid>/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/hybrid/<int:pid>/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/<int:pid>/hybrid/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/<int:pid>/species/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/species_detail/<int:pid>/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/hybrid_detail/<int:pid>/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/<int:pid>/species_detail/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('detail/<int:pid>/hybrid_detail/', RedirectView.as_view(url='/display/summary/orchidaceae/%(pid)s/', permanent=True)),
    path('search/search_match/', RedirectView.as_view(url='/search/search_orchidaceae/', permanent=True)),

    # Decommissioned applications
    path('natural/', include(('detail.urls', 'detail'), namespace='natural')),
    path('orchidlite/', include(('display.urls', 'display'), namespace='orchidlite')),
    path('orchid/', include(('orchidaceae.urls', 'orchidaceae'), namespace='orchid')),
    path('orchidlist/', include(('orchidaceae.urls', 'orchidaceae'), namespace='orchidlist')),
    # re_path(r'^natural/(?P<path>.*)$', RedirectView.as_view(url='/detail/%(path)s', permanent=True)),
    # path('natural/', include('detail.urls'), namespace='natural'),
    # re_path(r'^orchidlite/(?P<path>.*)$', RedirectView.as_view(url='/display/%(path)s', permanent=True)),
    # path('orchidlite/', include('display.urls'), namespace='orchidlite'),
    # re_path(r'^orchid/(?P<path>.*)$', RedirectView.as_view(url='/orchidaceae/%(path)s', permanent=True)),
    # path('orchid/', include('orchidaceae.urls'), namespace='orchid'),
    # re_path(r'^orchidlist/(?P<path>.*)$', RedirectView.as_view(url='/orchidaceae/%(path)s', permanent=True)),
    # path('orchidlist/', include('orchidaceae.urls'), namespace='orchidlist'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
