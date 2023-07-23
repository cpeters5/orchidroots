from django import forms
from django.forms import ModelForm, Textarea, TextInput, ValidationError, CheckboxInput, ModelChoiceField, HiddenInput
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget
from django.core.validators import URLValidator

from .models import City, Gallery, Artwork, Artist, Medium, Genre

CHOICES = (
              ('0', '0 Private'),
              ('1', '1 best'),
              ('2', '2 better'),
              ('3', '3 fine'),
              ('4', '4 student'),
              ('5', '5 Practice'),
)
STATUS_CHOICES = (('NFS','not for sale'),('AV','available'),('PUR','price upon request'))

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
        required=True,
        widget=Select2Widget
    )
    genre = ModelChoiceField(
        queryset=Genre.objects.order_by('genre'),
        required=True,
        widget=Select2Widget
    )

    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.fields['status'].choices = STATUS_CHOICES
        # Making UploadForm required
        # self.fields['rank'].choices = CHOICES
        # self.fields['image_file'].required = True
        # self.fields['artist'].required = True
        # self.fields['medium'].required = True
        # role = forms.CharField(required=True)

    class Meta:
        model = Artwork
        status = forms.CharField(initial='NFS')
        # rank = forms.IntegerField(initial=5)
        # fields = ('artist', 'name', 'image_file', 'medium', 'genre', 'status', 'hashtag', 'description', 'price')
        fields = ('artist', 'name', 'image_file', 'medium', 'genre', 'status', 'hashtag', 'description', 'price', 'source_url', 'support')

        labels = {
            'artist': 'Artist',
            'name': 'Title',
            'medium': 'medium',
            'genre': 'style',
            'price': 'price',
            'status': 'status',
            'source_url': 'source url',
            'support': 'e.g. canvas, water color paper 300g',
            'hashtag': 'comma separated hashtags',
            # 'image_file': 'upload file',
            # 'date': 'If author is not in the list, enter a name to be used for credit attribution here',
            'description': 'description',
        }
        widgets = {
            # 'role': forms.HiddenInput(),
            'name': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', 'autocomplete': 'off', }),
            'artist': TextInput(attrs={'size': 37, 'style': 'font-size: 13px', }),
            'medium': forms.Select(attrs={'class', 'form_control'}),
            'genre': forms.Select(attrs={'class', 'form_control' }),
            # 'price': forms.IntegerField(attrs={'class', 'form_control' }),
            # 'status': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', 'autocomplete': 'off', }),
            'source_url': TextInput(attrs={'size': 120, 'style': 'font-size: 13px', }),
            'support': TextInput(attrs={'size': 37, 'style': 'font-size: 13px', }),
            'hashtag': TextInput(attrs={'size': 120, 'style': 'font-size: 13px', }),
            # 'date': Textarea(attrs={'cols': 37, 'rows': 4, 'style': 'font-size: 13px', }),
            # 'source_url': forms.URLField(
            #         label='URL Field',
            #         required=False,
            #         max_length=200,
            #         validators=[URLValidator(schemes=['http', 'https'])]
            # ),
            'description': Textarea(attrs={'cols': 37, 'rows': 4, 'style': 'font-size: 13px', }),
        }
        choices = {
            'status': STATUS_CHOICES,
            # 'quality': QUALITY,
            # 'is_private':PRIVATE,
        }
        help_texts = {
                # 'medium': 'e.g. Charcoal, clay, acrylic, oil, glass, metal, fabric,...',
                # 'genre': 'e.g. realism, abstract, cubism, impressionism, minimalism,...',
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
            genre = Genre.objects.get(pk='NA')
        return genre

    def clean_name(self):
        name = self.cleaned_data['name']
        if not name:
            name = ""
        return name

    def clean_support(self):
        support = self.cleaned_data['support']
        if not support:
            support = ""
        return support

    def clean_price(self):
        price = self.cleaned_data['price']
        if type(price) is not int:
            raise forms.ValidationError("Price must be an integer")
        return price

    def clean_source_url(self):
        source_url = self.cleaned_data.get('source_url')
        if source_url and not source_url.lower().startswith("http"):
            source_url = ''

        return source_url


class UpdateFileForm(forms.ModelForm):
    # artist = ModelChoiceField(
    #     queryset=Artist.objects.order_by('artist'),
    #     required=True,
    #     widget=Select2Widget
    # )
    medium = ModelChoiceField(
        queryset=Medium.objects.order_by('medium'),
        required=True,
        widget=Select2Widget
    )
    genre = ModelChoiceField(
        queryset=Genre.objects.order_by('genre'),
        required=True,
        widget=Select2Widget
    )

    def __init__(self, *args, **kwargs):
        super(UpdateFileForm, self).__init__(*args, **kwargs)
        # Making UploadForm required
        # self.fields['image_file'].required = True
        # self.fields['artist'].required = True
        # self.fields['medium'].required = True
        # role = forms.CharField(required=True)

    class Meta:
        model = Artwork
        # fields = ('name', 'medium', 'genre', 'hashtag', 'description', 'rank', 'price', 'status')
        fields = ('name', 'medium', 'genre', 'hashtag', 'description', 'rank', 'price', 'status', 'source_url', 'support')

        labels = {
            'name': "Title",
            # 'date': 'date',
            'medium': 'medium',
            'genre': 'style',
            'hashtag': 'comma separated hashtags',
            'description': 'description',
            'rank': 'rank',
            'source_url': 'source url',
            'support': 'e.g. canvas, water color paper 300g',
            # 'date': 'If author is not in the list, enter a name to be used for credit attribution here',
            'price': 'price',
            'status': 'status',
        }
        widgets = {
            'medium': forms.Select(attrs={'class', 'form_control'}),
            'genre': forms.Select(attrs={'class', 'form_control' }),
            'hashtag': TextInput(attrs={'size': 120, 'style': 'font-size: 13px', }),
            'source_url': TextInput(attrs={'size': 120, 'style': 'font-size: 13px', }),
            'support': TextInput(attrs={'size': 37, 'style': 'font-size: 13px', }),
            'description': Textarea(attrs={'cols': 37, 'rows': 4, 'style': 'font-size: 13px', }),
        }
        help_texts = {
                # 'medium': 'e.g. Charcoal, clay, acrylic, oil, glass, metal, fabric,...',
                # 'genre': 'e.g. realism, abstract, cubism, impressionism, minimalism,...',
        }
        error_messages = {
            'image_file': {
                'required': _("Please select a file to upload."),
            },
        }

    def clean_status(self):
        status = self.cleaned_data['status']
        if not status:
            print("bad status")
            status = "Invalid"
        return status

    def clean_support(self):
        support = self.cleaned_data['support']
        if not support:
            support = ""
        return support

    def clean_name(self):
        name = self.cleaned_data['name']
        if not name:
            print("bad name")
            name = "Invalid name"
        return name

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

    def clean_source_url(self):
        source_url = self.cleaned_data['source_url']
        if source_url and not source_url.lower().startswith("http"):
            source_url = ''

        return source_url


