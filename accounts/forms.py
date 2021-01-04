from allauth.account.utils import perform_login
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from allauth.account.utils import filter_users_by_email
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.utils import import_attribute
from allauth.socialaccount.forms import SignupForm, BaseSignupForm
from allauth.account.forms import SetPasswordField, PasswordField
from allauth.account import app_settings
from allauth.account.utils import user_field, user_email, user_username
from django.utils.translation import ugettext_lazy as _

from .models import User, Profile, Photographer, Country

class GuestForm(forms.Form):
    email    = forms.EmailField()


class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['current_credit_name'].queryset = Photographer.objects.all().order_by('displayname')
        self.fields['country'].queryset = Country.objects.all().order_by('country')

    class Meta:
        model = Profile
        exclude = ('user',)
        fields = ('photo_credit_name', 'specialty','country','current_credit_name',)
        labels = {
            'photo_credit_name': 'The name you prefer to use for credit attribution',
            'current_credit_name': 'The name currently used for credit attribution in OrchidRoots. Leave blank if you do not see your name iin the list.<br>WARNING: your account will be removed if you selected name that is not yours.',
            'specialty':'Orchid related Interest. List genera or alliances of your interest',
            'country':'Country',
        }
        help_texts = {
            # 'specialty': 'List genera or alliances of orchids of your interest',
            # 'photo_credit_name': 'This is the name you prefer to use for credit attribution',
            # 'current_credit_name': 'This is the name used for credit attribution in OrchidRoots',
        }
    def clean_current_credit_name(self):
        current_credit_name = self.cleaned_data.get('current_credit_name')

        # if current_credit_name and Profile.objects.filter(current_credit_name=current_credit_name).count():
        #     raise forms.ValidationError('This credit name has already been taken!')
        return current_credit_name


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        return username.lower()


class AddEmailForm(forms.Form):

    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(
            attrs={"type": "email",
                   "size": "30",
                   "placeholder": _('E-mail address')}))

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):

        if not self.user:
            raise forms.ValidationError('Cannot add email to this user, try login in first')

        value = self.cleaned_data["email"]
        value = get_adapter().clean_email(value)
        errors = {
            "this_account": _("This e-mail address is already associated"
                              " with this account."),
            "different_account": _("This e-mail address is already associated"
                                   "with another account."),
        }
        users = filter_users_by_email(value)
        on_this_account = [u for u in users if u.pk == self.user.pk]
        on_diff_account = [u for u in users if u.pk != self.user.pk]

        if on_this_account:
            raise forms.ValidationError(errors["this_account"])
        if on_diff_account and settings.ACCOUNT_UNIQUE_EMAIL:
            raise forms.ValidationError(errors["different_account"])
        return value

    def save(self, request, user):
        return EmailAddress.objects.add_email(request, user, self.cleaned_data["email"], confirm=True)



class RegisterForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username','email','fullname',)
        labels = {
            'username':'User name',
            'email':'Email address',
            'fullname':'Full name',
        }
        help_texts = {
            'specialty': 'Orchid genera or alliances that you are interested in',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This emails address is already taken")

        return email


    def clean_password2(self):
        # Check that the two password entries match
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')

        if (' ' in username):
            raise forms.ValidationError('username must not contain blank space!')

        if username and User.objects.filter(username__iexact=username).count():
            raise forms.ValidationError('This username ' + username + ' has already been taken!')
        return username


    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # user.active = False     #email confirmation before activate
        if commit:
            user.save()
        return user


class UserAdminCreationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username','email')
        # fields = ('username','email','fullname','specialty')

    def clean_password2(self):
        # Check that the two password entries match
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserAdminCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()
    class Meta:
        model = User
        # fields = ('username','email', 'password', 'active', 'admin')
        fields = ('username','email', 'password')

    def clean_password(self):
        return self.initial["password"]

class SocialPasswordForm(BaseSignupForm):
    password1 = SetPasswordField(label=_("Password"))
    password2 = SetPasswordField(label=_("Confirm Password"))

    def __init__(self, *args, **kwargs):
        self.sociallogin = kwargs.pop('sociallogin')
        user = self.sociallogin.user
        initial = {'email': user_email(user) or '',
                   'username': user_username(user) or user_email(user).split('@')[0],
                   'first_name': user_field(user, 'first_name') or '',
                   'last_name': user_field(user, 'last_name') or ''}
        kwargs.update({
            'initial': initial,
            'email_required': kwargs.get('email_required',
                                         app_settings.EMAIL_REQUIRED)})


        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs = {'class':'form-control'}
        self.fields['password2'].widget.attrs = {'class': 'form-control'}
        self.fields['email'].widget = forms.HiddenInput()
        self.fields['username'].widget = forms.HiddenInput()


    def save(self, request):
        adapter = self.get_adapter(request)
        user = adapter.save_user(request, self.sociallogin, form=self)
        self.custom_signup(request, user)
        return user

    def clean(self):
        super().clean()
        if "password1" in self.cleaned_data \
                and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] \
                    != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password"
                                              " each time."))

    def raise_duplicate_email_error(self):
        raise forms.ValidationError(
            _("An account already exists with this e-mail address."
              " Please sign in to that account first, then connect"
              " your %s account.")
            % self.sociallogin.account.get_provider().name)

    def get_adapter(self, request):
        return import_attribute(settings.SOCIALACCOUNT_ADAPTER)(request)

    def custom_signup(self, request, user):
        password = self.cleaned_data['password1']
        user.set_password(password)
        user.save()



# TODO: Couldn't get this to work
# class SetPasswordForm(forms.Form):
#     """
#     A form that lets a user change set their password without entering the old
#     password
#     """
#     error_messages = {
#         'password_mismatch': _("The two password fields didn't match."),
#     }
#     new_password1 = forms.CharField(label=_("New password"),
#                                     widget=forms.PasswordInput)
#     new_password2 = forms.CharField(label=_("New password confirmation"),
#                                     widget=forms.PasswordInput)
#
#     def __init__(self, user, *args, **kwargs):
#         self.user = user
#         super(SetPasswordForm, self).__init__(*args, **kwargs)
#
#     def clean_new_password2(self):
#         password1 = self.cleaned_data.get('new_password1')
#         password2 = self.cleaned_data.get('new_password2')
#         if password1 and password2:
#             if password1 != password2:
#                 raise forms.ValidationError(
#                     self.error_messages['password_mismatch'],
#                     code='password_mismatch',
#                 )
#         return password2
#
#     def save(self, commit=True):
#         self.user.set_password(self.cleaned_data['new_password1'])
#         if commit:
#             self.user.save()
#         return self.user