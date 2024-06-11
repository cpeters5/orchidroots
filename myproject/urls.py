"""myproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.views.generic.base import TemplateView, RedirectView
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import  user_reset_password, login_page, register_page, UpdateProfileView, SetEmailView,\
    ChangeEmailView, PasswordChangeRedirect, CustomPasswordResetFromKeyView
from common.views import home
# from other.sitemaps import SpeciesSitemap# from myproject.views import robots_txt
from . import views

# sitemaps = {
#     'photos':SpeciesSitemap
# }

urlpatterns = [
    # Home page
    path('admin/', admin.site.urls),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),

    # User accounts
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('set_email/', SetEmailView.as_view(), name='set_email'),
    path('change_email/', ChangeEmailView.as_view(), name='change_email'),
    path('update_profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('logout/', LogoutView.as_view(), {'next_page': '//'}, name='logout'),
    path('donation/', include('donation.urls')),
    path('accounts/password/change/', PasswordChangeRedirect.as_view(), name="account_password_change"),
    path('accounts/password/user_reset_password/', user_reset_password, name="user_account_reset_password"),
    re_path(
        r"accounts/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        CustomPasswordResetFromKeyView.as_view(),
        name="account_reset_password_from_key",
    ),
    path('accounts/', include('allauth.urls')),

    # Landing
    path('', home, name='home'),
    path('documents/', include('documents.urls')),

    # Common to all apps
    path('search/', include('search.urls')),
    path('common/', include('common.urls')),
    path('display/', include('display.urls')),

    # Family specific
    path('animalia/', include('animalia.urls')),
    path('aves/', include('aves.urls')),
    path('fungi/', include('fungi.urls')),
    path('other/', include('other.urls')),
    path('orchidaceae/', include('orchidaceae.urls')),
    path('detail/', include('detail.urls')),

    # New dev
    path('gallery/', include('gallery.urls')),

    # REDIRECTIONS: Remove this in a year or so. @2024
    # redirections (in the process of merging detail with orchidaceae)
    path('detail/ancestor/<int:pid>/', RedirectView.as_view(url='/orchidaceae/ancestor/%(pid)s/', permanent=True)),
    path('detail/ancestor/', RedirectView.as_view(url='/orchidaceae/ancestor/', permanent=True)),
    path('detail/ancestrytree/<int:pid>/', RedirectView.as_view(url='/orchidaceae/ancestrytree/%(pid)s/', permanent=True)),
    path('detail/ancestrytree/', RedirectView.as_view(url='/orchidaceae/ancestrytree/', permanent=True)),
    path('detail/progeny/<int:pid>/', RedirectView.as_view(url='/orchidaceae/progeny/%(pid)s/', permanent=True)),
    path('detail/progenyimg/<int:pid>/', RedirectView.as_view(url='/orchidaceae/progenyimg/%(pid)s/', permanent=True)),
    path('detail/information/<int:pid>/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('detail/photos/<int:pid>/', RedirectView.as_view(url='/display/photos/%(pid)s/', permanent=True)),
    path('detail/species/<int:pid>/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('detail/hybrid/<int:pid>/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('detail/<int:pid>/hybrid/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('detail/<int:pid>/species/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('detail/species_detail/<int:pid>/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('detail/hybrid_detail/<int:pid>/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('detail/<int:pid>/species_detail/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('detail/<int:pid>/hybrid_detail/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('orchidaceae/information/<int:pid>/', RedirectView.as_view(url='/display/information/%(pid)s/', permanent=True)),
    path('orchidaceae/photos/<int:pid>/', RedirectView.as_view(url='/display/photos/%(pid)s/', permanent=True)),

    # Decommissioned applications
    re_path(r'^natural/(?P<path>.*)$', RedirectView.as_view(url='/detail/%(path)s', permanent=True)),
    path('natural/', include('detail.urls')),
    re_path(r'^orchidlite/(?P<path>.*)$', RedirectView.as_view(url='/display/%(path)s', permanent=True)),
    path('orchidlite/', include('display.urls')),
    re_path(r'^orchid/(?P<path>.*)$', RedirectView.as_view(url='/orchidaceae/%(path)s', permanent=True)),
    path('orchid/', include('orchidaceae.urls')),
    re_path(r'^orchidlist/(?P<path>.*)$', RedirectView.as_view(url='/orchidaceae/%(path)s', permanent=True)),
    path('orchidlist/', include('orchidaceae.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
