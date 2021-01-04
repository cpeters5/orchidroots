from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm
# from .models import Profile
# from django.apps import apps
# MyProfile = apps.get_model('orchiddb', 'Profile')
# class UserForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ('first_name', 'last_name', 'email')

#
# class ProfileForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ('confirm_email', 'photo_credit_name', 'specialty')
#
# class SignUpForm(UserCreationForm):
#     confirm_email = forms.CharField(help_text=' Format: tiger@hot.com', required=False)
#     photo_credit_name = forms.CharField(help_text=' Format: A.Jack', required=False)
#     specialty = forms.CharField(help_text=' Format: Python', required=False)
#     website = forms.CharField(help_text=' Format: http://www.yahoo.com', required=False)
#     country = forms.CharField(help_text=' Format: Brazil', required=False)
#     approved = forms.BooleanField(help_text=' checked', required=False)
#     # birth_date = forms.DateField(help_text='Required. Format: YYYY-MM-DD')
#
#     class Meta:
#         model = User
#         fields = ('username','first_name','last_name','email','confirm_email','photo_credit_name','specialty', 'password1', 'password2', 'website','country','approved')
