from django import forms
from django.forms import ModelForm, ModelChoiceField, TextInput
from django_select2.forms import Select2Widget
from gallery.models import City

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

