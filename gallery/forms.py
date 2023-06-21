from django import forms
from django.forms import ModelForm, Textarea, TextInput, ValidationError, CheckboxInput, ModelChoiceField, HiddenInput
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from .models import City, Gallery, Artwork, Artist, Medium, Genre

class CityForm(ModelForm):
    mycity = ModelChoiceField(
        queryset=City.objects.values_list('city', flat=True).order_by('city'),
        required=True,
        widget=Select2Widget
    )

    def __init__(self, *args, **kwargs):
        super(CityForm, self).__init__(*args, **kwargs)
        self.fields['mycity'].required = True


    class Meta:
        model = City
        fields = ('mycity',)
        labels = {
            'mycity': "City or region",
        }
        widgets = {
            'mycity': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', 'autocomplete': 'off', }),
        }
        error_messages = {
             # 'city': {
             #     'required': ("Please select a city."),
             # },
        }

    def clean_city(self):
        city = self.cleaned_data['city'].strip()
        # print("a. author = ", self.cleaned_data['author'])
        if not city:
            return None
        return city


class UploadFileForm(forms.ModelForm):
    artist = ModelChoiceField(
        queryset=Artist.objects.order_by('artist'),
        required=True,
        widget=Select2Widget
    )
    medium = ModelChoiceField(
        queryset=Medium.objects.order_by('medium'),
        required=False,
        widget=Select2Widget
    )
    genre = ModelChoiceField(
        queryset=Genre.objects.order_by('genre'),
        required=False,
        widget=Select2Widget
    )

    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        # Making UploadForm required
        # self.fields['image_file'].required = True
        # self.fields['artist'].required = True
        # self.fields['medium'].required = True
        # role = forms.CharField(required=True)

    class Meta:
        model = Artwork
        fields = ('title', 'artist', 'medium', 'genre', 'hashtag', 'style', 'description', 'image_file')

        labels = {
            'title': "Title",
            'artist': 'Artist',
            'medium': 'medium',
            'genre': 'genre',
            'hashtag': 'comma separated hashtags',
            'style': 'style',
            'image_file': 'upload file',
            # 'date': 'If author is not in the list, enter a name to be used for credit attribution here',
            'description': 'description',
        }
        widgets = {
            # 'role': forms.HiddenInput(),
            # 'title': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', 'autocomplete': 'off', }),
            # 'artist': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            # 'medium': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            # 'genre': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'hashtag': TextInput(attrs={'size': 120, 'style': 'font-size: 13px', }),
            # 'style': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            # 'date': Textarea(attrs={'cols': 37, 'rows': 4, 'style': 'font-size: 13px', }),
            'description': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
        }
        help_texts = {
                'medium': 'e.g. Charcoal, clay, acrylic, oil, glass, metal, fabric,...',
                'genre': 'e.g. realism, abstract, cubism, impressionism, minimalism,...',
        }
        error_messages = {
            'image_file': {
                'required': _("Please select a file to upload."),
            },
        }

    def clean_image_file(self):
        image_file = self.cleaned_data['image_file']
        if not image_file:
            raise forms.ValidationError('You must select a valid image file')
        return image_file

    def clean_artist(self):
        artist = self.cleaned_data['artist']
        if not artist:
            raise forms.ValidationError("artist's name must be provided")
        return artist

    def clean_medium(self):
        medium = self.cleaned_data['medium']
        if not medium:
            medium = Medium.objects.get(pk=' NA')
        return medium

    def clean_genre(self):
        genre = self.cleaned_data['genre']
        if not genre:
            genre = Genre.objects.get(pk=' NA')
        return genre