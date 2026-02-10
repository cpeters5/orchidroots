from django import forms
from django.forms import ModelForm, Textarea, TextInput, ValidationError, CheckboxInput, ModelChoiceField, HiddenInput
from django_select2.forms import Select2Widget
from django.utils.translation import gettext_lazy as _
from orchidaceae.models import UploadFile, Species, Accepted, Hybrid, SpcImages, Genus
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

        # if species_obj[0].status == 'synonym':
        #     acc = species_obj[0].getAccepted().name()
        #     message = new_genus + ' ' + self['species'].value() + ' ' + self['infraspr'].value() + ' ' + self[
        #         'infraspe'].value() + ' is a synonym of ' + acc
        #     raise forms.ValidationError(message)

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
        fields = ('description', 'comment', 'history', 'etymology', 'culture',
                  # 'seed_genus','seed_species','seed_id','pollen_genus','pollen_species','pollen_id',
                  # 'ref_url',
                  )
        labels = {
            'description': 'Description',
            'comment': 'Comment',
            'history': 'History',
            'etymology': 'Etymology',
            'culture': 'Culture',
        }
        widgets = {
            'description': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px', }),
            'comment': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px', }),
            'history': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px', }),
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
        #     'history':'History',
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
        fields = ('description', 'comment', 'history', 'etymology', 'culture', 'url', 'url_name',
                  'common_name', 'local_name', 'bloom_month', 'fragrance', 'altitude'
                  )
        labels = {
            'description': 'Description',
            'comment': 'Comment',
            'history': 'History',
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
            'history': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
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
        #     'history':'History',
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


