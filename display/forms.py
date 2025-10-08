# In your app's forms.py (create if it doesn't exist)
from django import forms
from orchidaceae.models import ImageFlag  # Adjust import based on your app structure

class ImageFlagForm(forms.ModelForm):
    class Meta:
        model = ImageFlag
        fields = ['title', 'description', 'name', 'email']
        widgets = {
            'title': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Provide details about why you are flagging this image...'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name (required if not logged in)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email (optional)'}),
        }
        labels = {
            'title': 'Reason for Flagging',
            'description': 'Details',
            'name': 'Name',
            'email': 'Email',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Pass request.user when initializing
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            # Hide name/email fields if user is authenticated
            self.fields['name'].widget = forms.HiddenInput()
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['name'].required = False  # Optional for auth users
        else:
            self.fields['name'].required = True  # Make name required for anonymous

    def clean(self):
        cleaned_data = super().clean()
        if not (self.user and self.user.is_authenticated):
            if not cleaned_data.get('name'):
                self.add_error('name', 'Name is required if you are not logged in.')
        return cleaned_data