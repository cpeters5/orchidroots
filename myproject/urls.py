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
from django.views.generic import TemplateView
from django.views.generic.base import TemplateView, RedirectView
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import  user_reset_password, login_page, register_page, UpdateProfileView, SetEmailView,\
    ChangeEmailView, PasswordChangeRedirect, CustomPasswordResetFromKeyView
from common.views import orchid_home, ode
from utils.views import robots_txt

urlpatterns = [
    # Home page
    path('admin/', admin.site.urls),
    path("robots.txt", robots_txt),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),
    # path('dispatch', dispatch, name='dispatch'),
    path('documents/', include('documents.urls')),
    # path('index/', index, name='index'),
    # path('ads/', include('ads.urls')),
    # path("ads.txt", RedirectView.as_view(url=staticfiles_storage.url("ads.txt")),),

    # User accounts
    path('accounts/', include('allauth.urls')),
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
        r"^accounts/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        CustomPasswordResetFromKeyView.as_view(),
        name="account_reset_password_from_key",
    ),

    # Landing
    path('', orchid_home, name='orchid_home'),
    # path('', ode, name='ode'),

    path('search/', include('search.urls')),

    # Family specific
    path('core/', include('core.urls')),
    path('common/', include('common.urls')),
    path('display/', include('display.urls')),
    path('other/', include('other.urls')),
    path('orchidaceae/', include('orchidaceae.urls')),
    path('detail/', include('detail.urls')),

                  # legacy applications
    path('natural/', include('detail.urls')),
    path('orchid/', include('orchidaceae.urls')),
    path('orchidlite/', include('detail.urls')),
    # path('orchidlist/', include('orchidlist.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
