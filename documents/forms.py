from django import forms
from django.forms import ModelForm, Textarea, TextInput, ValidationError, CheckboxInput, ModelChoiceField, HiddenInput
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget
from orchidaceae.models import UploadFile, Species, Accepted, Hybrid, SpcImages, HybImages, Genus
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
    ('0','NO'),
    ('1','YES'),
)

# List of all genus - not used
class GenusForm(ModelForm):
    def __init__(self,*args,**kwargs):
        super(GenusField, self).__init__(*args, **kwargs)
        self.fields['genus'].queryset = Genus.objects.exclude(status='synonym').order_by('genus')

    class Meta:
        model = Genus
        fields = ('genus','pid',)

# used in reidentify. New species must already exists
class SpeciesForm(ModelForm):
    def __init__(self,*args,**kwargs):
        super(SpeciesForm, self).__init__(*args, **kwargs)
        self.fields['genus'].required = True
        self.fields['species'].required = True
        self.fields['infraspr'].required = False
        self.fields['infraspe'].required = False
        self.fields['year'].required = False

    class Meta:
        model = Species
        fields = ('genus','species','infraspr','infraspe','year')
        labels = {
            'genus':'Genus',
            'species':'Species',
            'infraspr':'infraspr',
            'infraspe':'infraspe',
            'year':'year',
        }
        widgets = {
            # 'pid': forms.HiddenInput(),
            'genus': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'species': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'infraspr': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'infraspe': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'year': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
        }

    def clean_genus(self):
        try:
            data = self.cleaned_data['genus'].strip()
            genus = Genus.objects.get(genus=data)
        except:
            raise forms.ValidationError(self['genus'].value() + ' is not a valid Genus')
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
        print("1. genus = ",new_genus)

        species_obj = Species.objects.filter(genus=new_genus).filter(species=new_species).exclude(status='synonym')
        if not self['infraspr'].value():
            print("2. no infraspr")
            species_obj = species_obj.exclude(infraspr__isnull=False)
        else:
            print("3. has infraspr")
            species_obj = species_obj.filter(infraspe=self['infraspe'].value()).filter(infraspr=self['infraspr'].value())

        if not self['infraspe'].value():
            print("4. no infraspe")
            species_obj = species_obj.exclude(infraspe__isnull=False)
        else:
            print("5. has infraspe")
            species_obj = species_obj.filter(infraspe=self['infraspe'].value())

        if self['year'].value():
            species_obj = species_obj.filter(year=self['year'].value())
        # print("6. ",species_obj[0].pid)


        if not species_obj:
            if self['infraspe'].value():
                message = new_genus + ' ' + self['species'].value() + ' ' + self['infraspr'].value() + ' ' + self['infraspe'].value() + ' is not a valid species'
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
    def __init__(self,*args,**kwargs):
        super(RenameSpeciesForm, self).__init__(*args, **kwargs)
        self.fields['genus'].required = True
        self.fields['species'].required = True
        self.fields['infraspr'].required = False
        self.fields['infraspe'].required = False
        self.fields['year'].required = False

    class Meta:
        model = Species
        fields = ('genus','species','infraspr','infraspe','year')
        labels = {
            'genus':'Genus',
            'species':'Species',
            'infraspr':'infraspr',
            'infraspe':'infraspe',
            'year':'year',
        }
        widgets = {
            # 'pid': forms.HiddenInput(),
            'genus': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'species': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'infraspr': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'infraspe': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'year': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
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
        fields = ('description', 'comment', 'history','etymology','culture',
                  # 'seed_genus','seed_species','seed_id','pollen_genus','pollen_species','pollen_id',
                  # 'ref_url',
                  )
        labels = {
            'description':'Description',
            'comment':'Comment',
            'history':'History',
            'etymology':'Etymology',
            'culture':'Culture',
        }
        widgets = {
            'description': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px',}),
            'comment': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px',}),
            'history': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px',}),
            'etymology': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px',}),
            'culture': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px',}),
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

    def save(self,commit=True):
        return super(HybridInfoForm,self).save(commit=commit)


class ReidentifySpeciesForm(forms.ModelForm):
    gen = ModelChoiceField(
        queryset=Genus.objects.filter(num_hybrid__gt=0).values_list('pid', 'genus'),
        required=True,
        widget=Select2Widget
    )
    # gen = forms.ChoiceField(required=True,
    #                           choices=Genus.objects.filter(num_hybrid__gt=0).values_list('pid', 'genus'))
    pid = forms.ChoiceField(required=True,
                              choices=Accepted.objects.values_list('pid'))
    def __init__(self,*args,**kwargs):
        super(ReidentifySpeciesForm, self).__init__(*args, **kwargs)
        # self.fields['gen'].required = True
        # self.fields['pid'].required = True
        # self.fields['pid'].queryset = Accepted.objects.none()
        # self.fields['gen'].queryset = Genus.objects.filter(num_hybrid__gt=0)
        if 'gen' in self.data:
            try:
                gen = int(self.data.get('gen'))
                self.fields['pid'].queryset = Accepted.objects.filter(gen=gen).order_by('species')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            self.fields['pid'].queryset = self.instance.gen.pid_set  #.order_by('name')

    class Meta:
        model = SpcImages
        fields = ('gen','pid')
        labels = {
            'gen':'Genus',
            'pid':'Species',
        }
        widgets = {
            # 'pid': forms.HiddenInput(),
            # 'gen': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'species': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'infraspr': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'infraspe': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
        }


class AcceptedInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AcceptedInfoForm, self).__init__(*args, **kwargs)
        # self.fields['subgenus'] = forms.ModelChoiceField(queryset=Subgenus.objects.all())        # Making UploadForm required
        # self.fields['image_file_path'].required = True

    class Meta:
        model = Accepted
        fields = ('description', 'comment', 'history','etymology','culture','url','url_name',
                  'common_name','local_name','bloom_month','fragrance','altitude'
                  )
        labels = {
            'description':'Description',
            'comment':'Comment',
            'history':'History',
            'etymology':'Etymology',
            'culture':'Culture',
            'url':'Link to an online publication',
            'url_name':'Name of source',
            'common_name':'Common name',
            'local_name':'Local name',
            'bloom_month':'Bloom month',
            'fragrance':'Fragrance',
            'altitude':'Altitude',
        }
        widgets = {
            'common_name': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'local_name': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'bloom_month': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
            'fragrance': TextInput(attrs={'size': 50, 'style': 'font-size: 13px'}),
            'altitude': TextInput(attrs={'size': 50, 'style': 'font-size: 13px'}),
            'description': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
            'comment': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
            'history': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
            'etymology': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
            'culture': Textarea(attrs={'cols': 52, 'rows': 3, 'style': 'font-size: 13px'}),
            'url': TextInput(attrs={'size': 50, 'style': 'font-size: 13px'}),
            'url_name': TextInput(attrs={'size': 50, 'style': 'font-size: 13px',}),
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


class UploadFileForm(forms.ModelForm):
    author = ModelChoiceField(
        queryset=Photographer.objects.order_by('fullname'),
        required=False,
        widget=Select2Widget
    )
    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        # Making UploadForm required
        # self.fields['image_file_path'].required = True
        self.fields['author'].required = True
        # self.fields['author'].queryset = Photographer.objects.all().order_by('fullname')
        # self.fields['is_private'].initial = False
    # is_private = forms.BooleanField(initial=True)
    class Meta:
        model = UploadFile
        # widgets = {'author': Select2Widget}
        fields = ('image_file_path','author','name','awards','variation','forma','originator','description','text_data','location','image_file',)

        labels = {
            'author':"Name that has been used to credit your photos. Warning: Your account will be removed if you select a name that is not yours!",
            'image_file_path':'Select image file',
            # 'source_url':'Photo URL',
            # 'source_file_name':'Alternate name',
            'name':'Clonal name',
            'awards':'Awards',
            'variation':'Varieties',
            'forma':'Form',
            'originator':'Name to be used for credit attribution',
            'description':'Tags',
            'text_data':'Comment',
            'location':'Location',
        }
        widgets = {
            # 'source_url':TextInput(attrs={'size': 45}),
            # 'source_file_name': TextInput(attrs={'size': 45}),
            'name': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'awards': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'variation': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'forma': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'originator': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'description': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'text_data': Textarea(attrs={'cols': 37, 'rows': 4, 'style': 'font-size: 13px',}),
            'location': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
        }
        help_texts = {
        #     # 'source_url': 'The URL where the photo is uploaded from, eg Facebook post',
        #     # 'source_file_name': 'Identified name if differs from the accepted name for the species, e.g. a synonym or undescribed/unpublished or unregistered name. (Put infra specific if exists in Variety box below.',
        #     'name': 'Clonal name of the plant',
        #     'awards': 'Awards received, comma separated',
        #     'variation': 'Informal variations (unpublished), or infra specific of synonym.',
        #     'forma': 'E.g. color forms, peloric, region...',
        #     'originator': 'e.g. hybridizer, cultivator, vender',
            'description': 'Comma separated terms used for search',
        #     'text_data': 'Any comment you may have about this photo. When, where or month it was taken, history of this plant, etc.',
        #     'location': 'Geolocation where this plant was originated from',
        #     'image_file_path': _('Only JPG files are accepted, and file name MUST not have a leading undescore.'),
        }
        error_messages = {
            'image_file_path': {
                'required': _("Please select a file to upload."),
            },
        }


class UploadSpcWebForm(forms.ModelForm):
    author = ModelChoiceField(
        queryset=Photographer.objects.order_by('fullname'),
        required=False,
        widget=Select2Widget
    )
    def __init__(self, *args, **kwargs):
        super(UploadSpcWebForm, self).__init__(*args, **kwargs)
        self.fields['rank'].choices = CHOICES
        self.fields['quality'].choices = QUALITY
        self.fields['image_url'].required = True
        # self.fields['author'].required = True
        # self.fields['author'].queryset = Photographer.objects.all().order_by('fullname')
        self.fields['author'].widget.is_localized=True
        self.fields['is_private'].initial = False

    class Meta:
        model = SpcImages
        rank = forms.IntegerField(initial=5)
        fields = ('author','source_url','image_url','source_file_name','name','awards','variation','form','text_data','description','certainty','rank','credit_to','is_private','image_file','quality')
        labels = {
            'author':"Name that has been used to credit your photos. Warning: Your account will be removed if you select a name that is not yours!",
            # 'author':'Your name for credit: select a name, if not exists, see next box',
            'source_url':'Link to source',
            'credit_to':'or, credit name. Enter only when author does not exist in the dropdown list.',
            'image_url':'Image URL',
            'source_file_name':'Alternate name, e.g. a synonym',
            'name':'Clonal name',
            'awards':'Awards',
            'quality':'Quality',
            'variation':'Varieties',
            'form':'Form',
            'certainty':'Certainty',
            'rank':'Rank',
            'text_data':'Comment',
            'description':'Tags',
            'is_private':'Private photo',
        }
        widgets = {
            'source_url':TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'credit_to':TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'image_url':TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'source_file_name': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'name': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'awards': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'variation': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'form': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'text_data': Textarea(attrs={'cols': 37, 'rows': 4}),
            'description': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            'certainty': TextInput(attrs={'size': 35, 'style': 'font-size: 13px',}),
            # 'is_private': CheckboxInput(attrs={'class': 'required checkbox form-control'}),
        }
        choices = {
            'rank': CHOICES,
            'quality': QUALITY,
            'is_private':PRIVATE,
        }
        # help_texts = {
        #     # 'author': 'The name for credit attribution',
        #     'credit_to': 'Enter the photo owner neme here if it is not listed under author',
        #     'source_url': 'The URL where the photo is uploaded from, eg Facebook post',
        #     'image_url': "Right click on the image and select 'copy image address'",
        #     'source_file_name': 'Identified name if differs from the accepted name for the species, e.g. a synonym or undescribed/unpublished or unregistered name. (Put infra specific if exists in Variety box below.',
        #     'name': 'Clonal name of the plant',
        #     'awards': 'Awards received, comma separated',
        #     'variation': 'Informal variations (unpublished), or infra specific of synonym.',
        #     'form': 'E.g. color forms, peloric, region...',
        #     'text_data': 'Any comment you may have about this photo. When, where or month it was taken, history of this plant, etc.',
        #     'description': 'Short description of the plant. E.g. aroma, color, pattern, shape...',
        #     'certainty': 'Put one or more ? to show level of certainty',
        #     'rank': 'Range from 9 (highest quality to 1 (lowest).  Set rank = 0 if you reject the identity of the photo',
        # }
        error_messages = {
            # 'author': {
                # 'required': _("Please select a name for credit attribution."),
            # },
            'image_url': {
                'required': _("Please enter, the url of the image (right click and select 'copy image address'."),
            },
        }

    # def clean_author(self):
    #     author = self.cleaned_data['author']
    #     if not Photographer.objects.get(pk=author):
    #         if not clean_credit_to['credit_to']:
    #             raise forms.ValidationError('You must enter an author, or a new credit name')
    #     return author

    def clean_credit_to(self):
        credit_to = self.cleaned_data['credit_to']
        # print("a. author = ", self.cleaned_data['author'])
        if not credit_to:
            return None
        return credit_to

    def clean_image_url(self):
        import re
        """ Validation of image_url specifically """
        image_url = self.cleaned_data['image_url']
        if not re.search('jpg',image_url) and not re.search('png',image_url):
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
    author = ModelChoiceField(
        queryset=Photographer.objects.order_by('fullname'),
        required=True,
        widget=Select2Widget
    )
    def __init__(self, *args, **kwargs):
        super(UploadHybWebForm, self).__init__(*args, **kwargs)
        self.fields['image_url'].required = True
        # self.fields['author'].required = True
        # self.fields['author'].queryset = Photographer.objects.all().order_by('fullname')
        # self.fields['author'].queryset = Photographer.objects.all().values_list('fullname','displayname').order_by('fullname')
        self.fields['rank'].choices = CHOICES
        self.fields['quality'].choices = QUALITY
        self.fields['is_private'].initial = False

    class Meta:
        model = HybImages
        rank = forms.IntegerField(initial=5)
        fields = ('author','source_url','image_url','source_file_name','name','awards','variation','form','text_data','description','certainty','rank','credit_to','is_private','image_file','quality')
        labels = {
            'author':"Name that has been used to credit your photos. Warning: Your account will be removed if you select a name that is not yours!",
            'credit_to':'or credit name. Enter only when name does not exist in Author list',
            'source_url':'Link to source',
            'image_url':'Image URL',
            'source_file_name':'Alternate name, e.g. a synonym',
            'name':'Clonal name',
            'awards':'Awards',
            'quality':'Quality',
            'variation':'Varieties',
            'form':'Form',
            'certainty':'Certainty',
            'rank':'Rank',
            'text_data':'Comment',
            'description':'Tags',
            'is_private': 'Private photo',
        }
        widgets = {
            # 'author':TextInput(attrs={'size': 35}),
            'source_url':TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            'credit_to':TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            'image_url':TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            'source_file_name': TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            'name': TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            'awards': TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            'variation': TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            'certainty': TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            'form': TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            'text_data': Textarea(attrs={'cols': 47, 'rows': 4, 'style': 'font-size: 13px',}),
            'description': TextInput(attrs={'size': 45, 'style': 'font-size: 13px',}),
            # 'is_private': CheckboxInput(attrs={'class': 'required checkbox form-control'}),
        }
        choices = {
            'rank': CHOICES,
            'quality': QUALITY,
            'is_private': PRIVATE,
        }
        # help_texts = {
        #     # 'author': 'The name for credit attribution',
        #     'credit_to': 'Enter the photo owner neme here if it is not listed under author',
        #     'source_url': 'The URL from address bar of the browser',
        #     'image_url': "Right click on the image and select 'copy image address'",
        #     'source_file_name': 'The name you prefer, if different from accepted name for the species, e.g. a synonym, an undescribed or unregistered name. (Place infraspecific in Variety box below.',
        #     'name': 'Clonal name of the plant',
        #     'awards': 'Awards received, comma separated',
        #     'variation': 'Informal variations (unpublished), or infra specific of synonym.',
        #     'certainty': 'Put one or more ? to show level of certainty',
        #     'form': 'E.g. color forms, peloric, region...',
        #     'text_data': 'Any comment you may have about this photo. When, where or month it was taken, history of this plant, etc.',
        #     'description': 'Short description of the plant. E.g. aroma, color, pattern, shape...',
        #     'rank': 'Range from 9 (highest quality to 1 (lowest).  Set rank = 0 if you reject the identity of the photo',
        # }
        error_messages = {
            # 'author': {
            #     'required': _("Please select a name for credit attribution."),
            # },
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

        def clean_author(self):
            data = self.cleaned_data['author']
            if not Photographer.objects.filter(pk=data):
                raise forms.ValidationError('Invalid Author')
            return data

    def clean_image_url(self):
        import re
        """ Validation of image_url specifically """
        image_url = self.cleaned_data['image_url']
        if not re.search('jpg',image_url) and not re.search('png',image_url):
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

# # class xUpdateForm(forms.Form):
# class ChangeSpeciesForm(forms.Form):
#     genus          = forms.CharField(label='Genus', required=True)
#     species        = forms.CharField(label='Species', required=True)
#     infraspr       = forms.CharField(label='Infraspr', required=False)
#     infraspe       = forms.CharField(label='Infraspe', required=False)
#
#     def clean_genus(self):
#         data = self.cleaned_data['genus']
#         if not Genus.objects.get(genus=data):
#             raise forms.ValidationError('Not a valid Genus')
#         return data
#
#     def clean_pid(self):
#         new_species = self.cleaned_data['species']
#         new_genus = self.clean_genus['genus']
#         species_obj = Species.objects.filter(genus=new_genus).filter(species=new_species)
#         if self.infraspr:
#             species_obj = species_obj.filter(infraspr=self.infraspr)
#         if self.infraspe:
#             species_obj = species_obj.filter(infraspe=self.infraspe)
#
#         if not species_obj:
#             raise forms.ValidationError('Not a valid species')
#         # return data + ' ' + self.cleaned_data['infraspr'] + ' ' + self.cleaned_data['infraspe']
#         return species_obj.pid_id


