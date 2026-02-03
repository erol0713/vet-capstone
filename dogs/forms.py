from django import forms

from .models import Dog

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


class DogForm(forms.ModelForm):
    class Meta:
        model = Dog
        fields = (
            'name',
            'status',
            'owner',
            'capture_datetime',
            'surrender_datetime',
            'barangay',
            'sex',
            'age_estimate',
            'color',
            'photo',
            'notes',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-control'
            widget_type = getattr(field.widget, 'input_type', None)
            if widget_type in ('checkbox', 'radio'):
                css = 'form-check-input'
            field.widget.attrs.setdefault('class', css)
        self.fields['barangay'] = forms.ChoiceField(
            choices=[('', 'Select barangay')] + [(b, b) for b in BAYAWAN_BARANGAYS],
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        self.fields['capture_datetime'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'}
        )
        self.fields['surrender_datetime'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'}
        )
        if 'photo' in self.fields:
            self.fields['photo'].widget.attrs.setdefault('accept', 'image/*')

    def clean(self):
        cleaned = super().clean()
        capture_dt = cleaned.get('capture_datetime')
        surrender_dt = cleaned.get('surrender_datetime')
        owner = cleaned.get('owner')

        if capture_dt and surrender_dt:
            raise forms.ValidationError('Choose either capture or surrender datetime, not both.')

        if capture_dt and owner:
            self.add_error('owner', 'Captured dogs should not have an owner.')

        if surrender_dt and not owner:
            self.add_error('owner', 'Surrendered dogs must have an owner.')

        return cleaned


class UserDogRegistrationForm(forms.ModelForm):
    class Meta:
        model = Dog
        fields = (
            'name',
            'sex',
            'age_estimate',
            'color',
            'barangay',
            'photo',
            'notes',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-control'
            widget_type = getattr(field.widget, 'input_type', None)
            if widget_type == 'select':
                css = 'form-select'
            field.widget.attrs.setdefault('class', css)
        self.fields['barangay'] = forms.ChoiceField(
            choices=[('', 'Select barangay')] + [(b, b) for b in BAYAWAN_BARANGAYS],
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        if 'photo' in self.fields:
            self.fields['photo'].widget.attrs.setdefault('accept', 'image/*')
