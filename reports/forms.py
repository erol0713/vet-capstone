from django import forms

from .models import Report

BAYAWAN_BARANGAYS = [
    'Suba',
    'Ubogon',
    'Pagatban',
    'Bangandawe',
    'Bal-os',
    'Maninihon',
    'Nakahilo',
    'Villareal',
    'San Jose',
    'Malabugas',
    'Narra',
    'Bangkaya',
    'Bitao',
    'Mandug',
    'Monlaque',
    'Casi',
    'Poblacion',
    'Kalumboyan',
    'Luz',
    'Bugay',
    'Manghulyawon',
    'San Isidro',
    'San Miguel',
    'San Sebastian',
    'Santo Rosario',
    'Talaptap',
    'Tayawan',
    'Telabastagan',
]


class PublicReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('report_type', 'location', 'description', 'contact_name', 'contact_phone', 'photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'location' in self.fields:
            self.fields['location'] = forms.ChoiceField(
                choices=[('', 'Select barangay')] + [(b, b) for b in BAYAWAN_BARANGAYS],
                required=True,
                widget=forms.Select(attrs={'class': 'form-select'}),
            )
        for field in self.fields.values():
            css = 'form-control'
            widget_type = getattr(field.widget, 'input_type', None)
            if widget_type == 'select' or field.widget.__class__.__name__.lower().startswith('select'):
                css = 'form-select'
            field.widget.attrs.setdefault('class', css)
        if 'description' in self.fields:
            self.fields['description'].widget.attrs.setdefault('rows', 4)


class StaffReportUpdateForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('status', 'notes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-control'
            widget_type = getattr(field.widget, 'input_type', None)
            if widget_type == 'select' or field.widget.__class__.__name__.lower().startswith('select'):
                css = 'form-select'
            field.widget.attrs.setdefault('class', css)
