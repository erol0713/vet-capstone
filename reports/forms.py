from django import forms

from .models import Report

BAYAWAN_BARANGAYS = [
    'Ali-is',
    'Banaybanay',
    'Banga',
    'Boyco',
    'Bugay',
    'Cansumalig',
    'Dawis',
    'Kalamtukan',
    'Kalumboyan',
    'Malabugas',
    'Mandu-ao',
    'Maninihon',
    'Minaba',
    'Nangka',
    'Narra',
    'Pagatban',
    'Poblacion',
    'San Isidro',
    'San Jose',
    'San Miguel',
    'San Roque',
    'Suba (Poblacion)',
    'Tabuan',
    'Tayawan',
    'Tinago (Poblacion)',
    'Ubos (Poblacion)',
    'Villareal',
    'Villasol (Bato)',
]


class PublicReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('report_type', 'location', 'description', 'contact_name', 'contact_phone', 'contact_email', 'photo')

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
        if 'contact_name' in self.fields:
            self.fields['contact_name'].required = True
        if 'contact_phone' in self.fields:
            self.fields['contact_phone'].required = True


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
        if 'status' in self.fields:
            self.fields['status'].label = 'Status'
            self.fields['status'].help_text = 'Set the current processing stage for this report.'
        if 'notes' in self.fields:
            self.fields['notes'].label = 'Internal Notes'
            self.fields['notes'].required = False
            self.fields['notes'].widget.attrs.setdefault(
                'placeholder',
                'Add concise staff-only notes for turnover or audit trail.',
            )
            self.fields['notes'].widget.attrs.setdefault('rows', 5)
            self.fields['notes'].help_text = (
                'These notes are visible to staff and admins only.'
            )
