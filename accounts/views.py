from allauth.account.utils import complete_signup
from allauth.account.adapter import get_adapter
from allauth.account import signals
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, FormView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.http import is_safe_url, url_has_allowed_host_and_scheme
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from allauth.account.views import _ajax_response, PasswordChangeView, PasswordResetFromKeyView, app_settings, signals
from allauth.account.forms import UserTokenForm, SetPasswordForm
from django.conf import settings
from datetime import datetime
from utils.views import write_output, getRole

from .forms import LoginForm, RegisterForm, GuestForm, ProfileForm, AddEmailForm 
from .models import User, Profile, Photographer

from allauth.account.utils import perform_login

import logging
logger = logging.getLogger(__name__)

INTERNAL_RESET_URL_KEY = "set-password"
INTERNAL_RESET_SESSION_KEY = "_password_reset_key"


@login_required
def logout_page(request):
    logout(request)
    return HttpResponseRedirect(reverse('/'))


# Will be replaced by the classbase LoginView when the bug is fixed
def login_page(request):
    form = LoginForm(request.POST or None)
    context = {
        "form": form,
        # 'site_key': settings.RECAPTCHA_SITE_KEY,
    }
    next_ = request.GET.get('next')
    next_post = request.POST.get('next')
    redirect_path = next_ or next_post or None

    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            logging.error(">>> " + request.get_host() + " - user " + str(request.user))
            try:
                del request.session['guest_email_id']
            except:
                pass
            # update the redirect_path here
            if user.is_active:
                if user.email:
                    return perform_login(request, user, email_verification=settings.ACCOUNT_EMAIL_VERIFICATION,
                                         redirect_url=redirect_path)
                else:
                    request.session['email_user'] = user.id
                    return redirect('set_email')

            if is_safe_url(redirect_path, request.get_host()):
            # if url_has_allowed_host_and_scheme(redirect_path, request.get_host()):
            #     return redirect("/detail/myphoto_browse_spc/?role=" + role + "&display=checked")
                return redirect(redirect_path + "?role=pri")
            else:
                return redirect("/?role=pri")
        else:
            message = "LOGIN FAIL:  Username: {} / password: {}".format(username, password)
            logger.error(message)
            form.add_error(None, 'invalid username or password')
            context['form'] = form
            return render(request, "accounts/login.html", context)
    else:
        return render(request, "accounts/login.html", context)


def register_page(request):
    if request.method == "POST":
        user_form = RegisterForm(request.POST or None)
        profile_form = ProfileForm(request.POST or None)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.created_date = timezone.now()
            # if 'profile_pic' in request.FILES:
            #     profile.profile_pic = request.FILES['profile_pic']
            profile.save()
            write_output(request)
            return complete_signup(
                request, user,
                settings.ACCOUNT_EMAIL_VERIFICATION,
                reverse_lazy('login'))
        else:
            print(user_form.errors, profile_form.errors)

    else:
        user_form = RegisterForm()
        profile_form = ProfileForm()

    context = {
        "user_form": user_form, "profile_form": profile_form,
    }
    return render(request, "accounts/register.html", context)


def update_user_details(request):
    user = request.user
    new_email = request.POST.get('new_email')
    user.custom_user.add_email_address(request, new_email)


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form,
    })


class SetEmailView(FormView):
    template_name = 'account/set_email.html'
    form_class = AddEmailForm
    success_url = reverse_lazy('account_email_verification_sent')

    def get_user(self):
        user_id = self.request.session.get('email_user')
        user = User.objects.get(id=user_id)
        return user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.get_user()
        kwargs['user'] = user
        return kwargs

    def form_valid(self, form):
        user = self.get_user()
        email_address = form.save(self.request, user)
        get_adapter(self.request).add_message(
            self.request,
            messages.INFO,
            'account/messages/'
            'email_confirmation_sent.txt',
            {'email': form.cleaned_data["email"]})
        signals.email_added.send(sender=user.__class__,
                                 request=self.request,
                                 user=user,
                                 email_address=email_address)
        return super().form_valid(form)


class ChangeEmailView(FormView):
    template_name = 'account/change_email.html'
    form_class = AddEmailForm
    success_url = reverse_lazy('account_email_verification_sent')

    def get_user(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.get_user()
        kwargs['user'] = user
        return kwargs

    def form_valid(self, form):
        user = self.get_user()
        email_address = form.save(self.request, user)
        get_adapter(self.request).add_message(
            self.request,
            messages.INFO,
            'account/messages/'
            'email_confirmation_sent.txt',
            {'email': form.cleaned_data["email"]})
        signals.email_added.send(sender=user.__class__,
                                 request=self.request,
                                 user=user,
                                 email_address=email_address)
        return super().form_valid(form)


class PasswordChangeRedirect(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy('login')


class UpdateProfileView(LoginRequiredMixin, FormView):
    template_name = "accounts/update_profile.html"
    login_url = '/login/'
    model = Profile
    form_class = ProfileForm
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # this has all the form info
        context.update({})

        return context

    def get_form(self, form_class=None):
        # do not need this one if using UpdateView
        if not form_class:
            form_class = self.get_form_class()
        if self.request.user.profile:

            form = form_class(instance=self.request.user.profile, **self.get_form_kwargs())
        else:
            form = form_class(**self.get_form_kwargs())
        return form

    def form_valid(self, form):
        profile = form.save(commit=False)
        if not profile.user:
            profile.user = self.request.user
        profile.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the error below.')
        return super().form_invalid(form)


class CustomPasswordResetFromKeyView(PasswordResetFromKeyView):
    template_name = "account/password_reset_from_key.html" 
    success_url = reverse_lazy("account_reset_password_from_key_done")

    def dispatch(self, request, uidb36, key, **kwargs):
        self.request = request
        self.key = key
        if self.key == INTERNAL_RESET_URL_KEY:
            self.key = self.request.session.get(INTERNAL_RESET_SESSION_KEY, "")
            # (Ab)using forms here to be able to handle errors in XHR #890
            token_form = UserTokenForm(data={"uidb36": uidb36, "key": self.key})

            if token_form.is_valid():
                self.reset_user = token_form.reset_user

                # In the event someone clicks on a password reset link
                # for one account while logged into another account,
                # logout of the currently logged in account.
                if (
                    self.request.user.is_authenticated
                    and self.request.user.pk != self.reset_user.pk
                ):
                    self.logout()
                    self.request.session[INTERNAL_RESET_SESSION_KEY] = self.key

                self.request.session['reset_user_id'] = self.reset_user.id
                form = SetPasswordForm()
                return render(request, 'account/password_set.html', {"form": form})
        else:
            token_form = UserTokenForm(data={"uidb36": uidb36, "key": self.key})
            if token_form.is_valid():
                # Store the key in the session and redirect to the
                # password reset form at a URL without the key. That
                # avoids the possibility of leaking the key in the
                # HTTP Referer header.
                self.request.session[INTERNAL_RESET_SESSION_KEY] = self.key
                redirect_url = self.request.path.replace(
                    self.key, INTERNAL_RESET_URL_KEY
                )
                return redirect(redirect_url)

        self.reset_user = None
        response = self.render_to_response(self.get_context_data(token_fail=True))
        return _ajax_response(self.request, response, form=token_form)


def user_reset_password(request):
    user_id = request.session.get('reset_user_id', None)
    error = None
    if request.method == 'POST' and user_id is not None:
        form = SetPasswordForm()
        user = User.objects.filter(id=user_id).first()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            error = 'Two password must match with each other'
        if len(password1) < 6:
            error = 'Password must be six characters long' 
        
        if error is not None:
            return render(request, "account/password_set.html", {'form':form, "error":error})
            
        if user:
            user.set_password(password1)
            user.save()

    return redirect('/login')
