from django import forms
from django.forms import ModelForm, Textarea, TextInput, ValidationError, CheckboxInput, ModelChoiceField, HiddenInput
from django_select2.forms import Select2Widget
from django.utils.translation import gettext_lazy as _
from other.models import UploadFile, Species, Accepted, Hybrid, SpcImages, Genus
from accounts.models import Photographer
import copy

CHOICES = (
    ('0', '0 Private'),
    ('1', '1 Habitat'),
    ('2', '2 Plant'),
    ('3', '3 Inflorescences'),
    ('4', '4 Group of Flowers'),
    ('5', '5 Single Fl.'),
    # ('6', '6 Selected'),
    ('7', '7 Closed up'),
    ('8', '8 Information'),
)

QUALITY = (
    (1, 'Top'),
    (2, 'High'),
    (3, 'Average'),
    (4, 'Low'),
    # (5, 'Challenged'),
)

PRIVATE = (
    ('0', 'NO'),
    ('1', 'YES'),
)


# List of all genus - not used
class GenusForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(GenusField, self).__init__(*args, **kwargs)
        self.fields['genus'].queryset = Genus.objects.exclude(status='synonym').order_by('genus')

    class Meta:
        model = Genus
        fields = ('genus', 'pid',)


# used in reidentify. New species must already exists
class SpeciesForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SpeciesForm, self).__init__(*args, **kwargs)
        self.fields['genus'].required = True
        self.fields['species'].required = True
        self.fields['infraspr'].required = False
        self.fields['infraspe'].required = False
        self.fields['year'].required = False

    class Meta:
        model = Species
        fields = ('genus', 'species', 'infraspr', 'infraspe', 'year')
        labels = {
            'genus': 'Genus',
            'species': 'Species',
            'infraspr': 'infraspecific rank (e.g. var.)',
            'infraspe': 'infraspecific value (e.g. alba)',
            'year': 'year',
        }
        widgets = {
            # 'pid': forms.HiddenInput(),
            'genus': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'species': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'infraspr': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'infraspe': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'year': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
        }

    def clean_genus(self):
        try:
            data = self.cleaned_data['genus'].strip()
            genus = Genus.objects.get(genus=data)
        except:
            raise forms.ValidationError(self['genus'].value() + ' is not a valid Genus for this family')
        return data

    # def clean_infraspr(self):
    #     try:
    #         data = self.cleaned_data['infraspr']
    #     except:
    #         raise forms.ValidationError(_('Invalid infraspecific: %(infraspr)s'),
    #                                     params={'infraspr': self['infraspr'].value()},
    #                                     )
    #     return data
    #
    # def clean_infraspe(self):
    #     try:
    #         data = self.cleaned_data['infraspe']
    #     except:
    #         raise forms.ValidationError(_('Invalid infraspecific: %(infraspe)s'),
    #                                     params={'infraspe': self['infraspe'].value()},
    #                                     )
    #     return data

    def clean_species(self):
        new_species = self.cleaned_data['species'].strip()
        new_genus = self.clean_genus()

        species_obj = Species.objects.filter(genus=new_genus).filter(species=new_species).exclude(status='synonym')
        if not self['infraspr'].value():
            species_obj = species_obj.exclude(infraspr__isnull=False)
        else:
            species_obj = species_obj.filter(infraspe=self['infraspe'].value()).filter(
                infraspr=self['infraspr'].value())

        if not self['infraspe'].value():
            species_obj = species_obj.exclude(infraspe__isnull=False)
        else:
            species_obj = species_obj.filter(infraspe=self['infraspe'].value())

        if self['year'].value():
            species_obj = species_obj.filter(year=self['year'].value())

        if not species_obj:
            if self['infraspe'].value():
                message = new_genus + ' ' + self['species'].value() + ' ' + self['infraspr'].value() + ' ' + self[
                    'infraspe'].value() + ' is not a valid species'
            else:
                message = self['genus'].value() + ' ' + self['species'].value() + ' Not a valid species'
            # raise forms.ValidationError(_('invalid species'), code='invalid')
            raise forms.ValidationError(message)

        if species_obj.count() == 0:
            raise forms.ValidationError('Species does not exist')
        elif species_obj.count() > 1:
            raise forms.ValidationError('Query returns multiple values')

        if species_obj[0].status == 'synonym':
            acc = species_obj[0].getAccepted().name()
            message = new_genus + ' ' + self['species'].value() + ' ' + self['infraspr'].value() + ' ' + self[
                'infraspe'].value() + ' is a synonym of ' + acc
            raise forms.ValidationError(message)

        return species_obj[0].pid


# use in curateinfohyb and curateinfospc to rename species.  New genus must already exist.
class RenameSpeciesForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(RenameSpeciesForm, self).__init__(*args, **kwargs)
        self.fields['genus'].required = True
        self.fields['species'].required = True
        self.fields['infraspr'].required = False
        self.fields['infraspe'].required = False
        self.fields['year'].required = False

    class Meta:
        model = Species
        fields = ('genus', 'species', 'infraspr', 'infraspe', 'year')
        labels = {
            'genus': 'Genus',
            'species': 'Species',
            'infraspr': 'infraspr',
            'infraspe': 'infraspe',
            'year': 'year',
        }
        widgets = {
            # 'pid': forms.HiddenInput(),
            'genus': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'species': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'infraspr': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'infraspe': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'year': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
        }

    def clean_genus(self):
        try:
            data = self.cleaned_data['genus'].strip()
            genus = Genus.objects.get(genus=data)
        except:
            raise forms.ValidationError(self['genus'].value() + ' is not a valid Genus')
        return data


class HybridInfoForm(forms.ModelForm):
    # ref_url = forms.URLField(label='Reference URL',help_text=' web address of the cvomment, if exists', required=False)

    def __init__(self, *args, **kwargs):
        super(HybridInfoForm, self).__init__(*args, **kwargs)
        # self.fields['subgenus'] = forms.ModelChoiceField(queryset=Subgenus.objects.all())        # Making UploadForm required
        # self.fields['image_file_path'].required = True

    class Meta:
        model = Hybrid
        fields = ('description', 'comment', 'etymology', 'culture',
                  # 'seed_genus','seed_species','seed_id','pollen_genus','pollen_species','pollen_id',
                  # 'ref_url',
                  )
        labels = {
            'description': 'Description',
            'comment': 'Comment',
            'etymology': 'Etymology',
            'culture': 'Culture',
        }
        widgets = {
            'description': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px', }),
            'comment': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px', }),
            'etymology': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px', }),
            'culture': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px', }),
            # 'seed_genus': HiddenInput(),
            # 'seed_species': HiddenInput(),
            # 'seed_id': HiddenInput(),
            # 'pollen_genus': HiddenInput(),
            # 'pollen_species': HiddenInput(),
            # 'pollen_id': HiddenInput(),
        }
        # help_texts = {
        #     'description':'Description',
        #     'comment':'Additional comment related to this species',
        #     'etymology':'Ethymology',
        #     'culture':'Culture',
        # }
        error_messages = {
        }

    def save(self, commit=True):
        return super(HybridInfoForm, self).save(commit=commit)


class AcceptedInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AcceptedInfoForm, self).__init__(*args, **kwargs)
        # self.fields['subgenus'] = forms.ModelChoiceField(queryset=Subgenus.objects.all())        # Making UploadForm required
        # self.fields['image_file_path'].required = True

    class Meta:
        model = Accepted
        fields = ('description', 'comment', 'etymology', 'culture', 'url', 'url_name',
                  'common_name', 'local_name', 'bloom_month', 'fragrance', 'altitude'
                  )
        labels = {
            'description': 'Description',
            'comment': 'Comment',
            'etymology': 'Etymology',
            'culture': 'Culture',
            'url': 'Link to an online publication',
            'url_name': 'Name of source',
            'common_name': 'Common name',
            'local_name': 'Local name',
            'bloom_month': 'Bloom month',
            'fragrance': 'Fragrance',
            'altitude': 'Altitude',
        }
        widgets = {
            'common_name': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'local_name': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'bloom_month': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
            'fragrance': TextInput(attrs={'size': 50, 'style': 'font-size: 13px'}),
            'altitude': TextInput(attrs={'size': 50, 'style': 'font-size: 13px'}),
            'description': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
            'comment': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
            'etymology': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
            'culture': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
            'url': TextInput(attrs={'size': 50, 'style': 'font-size: 13px'}),
            'url_name': TextInput(attrs={'size': 50, 'style': 'font-size: 13px', }),
        }
        # help_texts = {
        #     'common_name': 'Common name',
        #     'local_name': 'Native name',
        #     'bloom_month': 'Months bloomed in the wild, comma separated',
        #     'fragrance': 'Fragrance',
        #     'altitude':'Altitude above sea level in feet',
        #     'description':'Description',
        #     'comment':'Any comment related to this species',
        #     'etymology':'Etymology',
        #     'url':'Link to a useful information',
        #     'urlname':'Name of URL',
        #     'culture':'Culture and growing condition, light level, temperature, relative huimidity, winter rest, etc',
        # }
        error_messages = {
        }

    def clean_description(self):
        description = self.cleaned_data.get("description")
        return description.replace("\"", "\'\'")


class UploadSpcWebForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UploadSpcWebForm, self).__init__(*args, **kwargs)
        self.fields['rank'].choices = CHOICES
        self.fields['quality'].choices = QUALITY
        self.fields['image_url'].required = True

    class Meta:
        model = SpcImages
        rank = forms.IntegerField(initial=5)
        fields = (
        'source_url', 'image_url', 'source_file_name', 'name', 'variation', 'form', 'text_data',
        'description', 'certainty', 'rank', 'credit_to', 'image_file', 'quality')
        labels = {
            'source_url': 'Link to source',
            'credit_to': 'Credit allocation name',
            'image_url': 'Image URL',
            'source_file_name': 'Alternate name, e.g. a synonym',
            'name': 'Clonal name',
            'quality': 'Quality',
            'variation': 'Varieties',
            'form': 'Form',
            'certainty': 'Certainty',
            'rank': 'Rank',
            'text_data': 'Comment',
            'description': 'Tags',
        }
        widgets = {
            'source_url': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', 'autocomplete': 'off', }),
            'credit_to': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'image_url': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', 'autocomplete': 'off', }),
            'source_file_name': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'name': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'variation': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'form': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'text_data': Textarea(attrs={'cols': 37, 'rows': 4}),
            'description': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'certainty': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
        }
        choices = {
            'rank': CHOICES,
            'quality': QUALITY,
        }
        # help_texts = {
        #     'credit_to': 'Enter the photo owner neme here if it is not listed under author',
        #     'source_url': 'The URL where the photo is uploaded from, eg Facebook post',
        #     'image_url': "Right click on the image and select 'copy image address'",
        #     'source_file_name': 'Identified name if differs from the accepted name for the species, e.g. a synonym or undescribed/unpublished or unregistered name. (Put infra specific if exists in Variety box below.',
        #     'name': 'Clonal name of the plant',
        #     'variation': 'Informal variations (unpublished), or infra specific of synonym.',
        #     'form': 'E.g. color forms, peloric, region...',
        #     'text_data': 'Any comment you may have about this photo. When, where or month it was taken, history of this plant, etc.',
        #     'description': 'Short description of the plant. E.g. aroma, color, pattern, shape...',
        #     'certainty': 'Put one or more ? to show level of certainty',
        #     'rank': 'Range from 9 (highest quality to 1 (lowest).  Set rank = 0 if you reject the identity of the photo',
        # }
        error_messages = {
            'image_url': {
                'required': _("Please enter, the url of the image (right click and select 'copy image address'."),
            },
        }

    def clean_credit_to(self):
        credit_to = self.cleaned_data['credit_to']
        if not credit_to:
            return None
        return credit_to

    def clean_image_url(self):
        import re
        """ Validation of image_url specifically """
        image_url = self.cleaned_data['image_url']
        if not re.search('jpg', image_url) and not re.search('png', image_url):
            raise ValidationError(
                _('Not a valid image URL'),
                params={'image_url': image_url},
            )
        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return image_url

    def clean_image_file(self):
        return self.cleaned_data['image_file']


class UploadHybWebForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UploadHybWebForm, self).__init__(*args, **kwargs)
        self.fields['image_url'].required = True
        self.fields['rank'].choices = CHOICES
        self.fields['quality'].choices = QUALITY

    class Meta:
        model = SpcImages
        rank = forms.IntegerField(initial=5)
        fields = (
        'source_url', 'image_url', 'source_file_name', 'name', 'variation', 'form', 'text_data',
        'description', 'certainty', 'rank', 'credit_to', 'image_file', 'quality')
        labels = {
            'credit_to': 'Credit allocation name',
            'source_url': 'Link to source',
            'image_url': 'Image URL',
            'source_file_name': 'Alternate name, e.g. a synonym',
            'name': 'Clonal name',
            'quality': 'Quality',
            'variation': 'Varieties',
            'form': 'Form',
            'certainty': 'Certainty',
            'rank': 'Rank',
            'text_data': 'Comment',
            'description': 'Tags',
        }
        widgets = {
            'source_url': TextInput(attrs={'size': 45, 'style': 'font-size: 13px', 'autocomplete': 'off', }),
            'credit_to': TextInput(attrs={'size': 45, 'style': 'font-size: 13px', }),
            'image_url': TextInput(attrs={'size': 45, 'style': 'font-size: 13px', 'autocomplete': 'off', }),
            'source_file_name': TextInput(attrs={'size': 45, 'style': 'font-size: 13px', }),
            'name': TextInput(attrs={'size': 45, 'style': 'font-size: 13px', }),
            'variation': TextInput(attrs={'size': 45, 'style': 'font-size: 13px', }),
            'certainty': TextInput(attrs={'size': 45, 'style': 'font-size: 13px', }),
            'form': TextInput(attrs={'size': 45, 'style': 'font-size: 13px', }),
            'text_data': Textarea(attrs={'cols': 47, 'rows': 4, 'style': 'font-size: 13px', }),
            'description': TextInput(attrs={'size': 45, 'style': 'font-size: 13px', }),
        }
        choices = {
            'rank': CHOICES,
            'quality': QUALITY,
        }
        # help_texts = {
        #     # 'author': 'The name for credit attribution',
        #     'credit_to': 'Enter the photo owner neme here if it is not listed under author',
        #     'source_url': 'The URL from address bar of the browser',
        #     'image_url': "Right click on the image and select 'copy image address'",
        #     'source_file_name': 'The name you prefer, if different from accepted name for the species, e.g. a synonym, an undescribed or unregistered name. (Place infraspecific in Variety box below.',
        #     'name': 'Clonal name of the plant',
        #     'variation': 'Informal variations (unpublished), or infra specific of synonym.',
        #     'certainty': 'Put one or more ? to show level of certainty',
        #     'form': 'E.g. color forms, peloric, region...',
        #     'text_data': 'Any comment you may have about this photo. When, where or month it was taken, history of this plant, etc.',
        #     'description': 'Short description of the plant. E.g. aroma, color, pattern, shape...',
        #     'rank': 'Range from 9 (highest quality to 1 (lowest).  Set rank = 0 if you reject the identity of the photo',
        # }
        error_messages = {
            'image_url': {
                'required': _("Please enter, the url of the image (right click and select 'copy image address'."),
            },
        }

        # A work around for non curator user.  Form will post empty rank.
        def clean_rank(self):
            data = self.cleaned_data['rank']
            if not data:
                return 5
            return data

    def clean_image_url(self):
        import re
        """ Validation of image_url specifically """
        image_url = self.cleaned_data['image_url']
        if not re.search('jpg', image_url) and not re.search('png', image_url):
            raise ValidationError(
                _('Not a valid image URL'),
                params={'image_url': image_url},
            )
        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return image_url

    def clean_image_file(self):
        return self.cleaned_data['image_file']

    # def __init__(self, data, **kwargs):
    #     initial = kwargs.get('initial', {})
    #     data = {**initial, **data}
    #     super().__init__(data, **kwargs)


class UploadFileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        # Making UploadForm required
        # self.fields['image_file_path'].required = True
        # self.fields['author'].required = True
        # role = forms.CharField(required=True)

    class Meta:
        model = UploadFile
        fields = (
        'image_file_path', 'source_url', 'name', 'variation', 'forma', 'credit_to', 'description',
        'text_data', 'location', 'binomial')

        labels = {
            'source_url': 'Link to source',
            'image_file_path': 'Select image file',
            'name': 'Common names or local names',
            'binomial':'Scientific name or registered hybrid name (if different from the title, otherwise, leave it blank)',
            'variation': 'Varieties',
            'forma': 'Form',
            'credit_to': 'or a name for credit attribution',
            'description': 'Tags. Comma separated keywords to help in searching',
            'text_data': 'Please share any details about this photo, e.g. its parentage, or anything else to help us organize it properly.',
            'location': 'Location',
        }
        widgets = {
            # 'role': forms.HiddenInput(),
            'source_url': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', 'autocomplete': 'off', }),
            'name': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'variation': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'forma': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'credit_to': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'description': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'text_data': Textarea(attrs={'cols': 37, 'rows': 4, 'style': 'font-size: 13px', }),
            'location': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
            'binomial': TextInput(attrs={'size': 35, 'style': 'font-size: 13px', }),
        }
        help_texts = {
            # 'name': '',
            #     'variation': 'Informal variations (unpublished), or infra specific of synonym.',
            #     'forma': 'E.g. color forms, peloric, region...',
            #     'credit_to': 'e.g. hybridizer, cultivator, vender',
            #     'description': 'Comma separated terms used for search',
            #     'text_data': 'Any comment you may have about this photo. When, where or month it was taken, history of this plant, etc.',
            #     'location': 'Geolocation where this plant was originated from',
            #     'image_file_path': _('Only JPG files are accepted, and file name MUST not have a leading undescore.'),
        }
        error_messages = {
            'image_file_path': {
                'required': _("Please select a file to upload."),
            },
        }

    def clean_image_file_path(self):
        image_file_path = self.cleaned_data['image_file_path']
        if not image_file_path:
            raise forms.ValidationError('You must select a valid image file')
        return image_file_path
