from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import perform_login
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest
from django import forms
from accounts.models import User, Profile
from django.conf import settings
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.core.mail import EmailMessage, EmailMultiAlternatives
import logging
logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def get_login_redirect_url(self, request):
        """
        """
        if request.user.is_authenticated:
            return settings.LOGIN_REDIRECT_URL
        else:
            return "/"


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def pre_social_login(self, request, sociallogin):
        try:
            email = sociallogin.account.extra_data['email']
            user = User.objects.get(email=email)
            # diff between accounts
            if not user.socialaccount_set.filter().exists():
                sociallogin.connect(request, user)
            perform_login(request, user, email_verification='none')
            raise ImmediateHttpResponse(redirect(settings.LOGIN_REDIRECT_URL))
        except Exception as e:
            logger.error("PRE SOCIAL LOGIN FAIL " + str(request.user))
            pass

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=None)
        if not getattr(user, 'profile', None):
            Profile.objects.create(user=user)

        preferred_avatar_size_pixels = 256
        if sociallogin.account.provider == 'facebook':
            picture_url = "http://graph.facebook.com/{0}/picture?width={1}&height={1}".format(
                sociallogin.account.uid, preferred_avatar_size_pixels)
            if getattr(user, 'profile', None):
                user.profile.profile_pic_url = picture_url
        user.profile.save()
        logger.error("SAVE USER " + str(request.user))
        return user

    def populate_user(self,
                      request,
                      sociallogin,
                      data):
        user = super().populate_user(request, sociallogin, data)
        user.fullname = data.get('name', '')
        logger.error("POPULATE USER " + str(request.user))
        return user



