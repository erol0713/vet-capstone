from django import forms
from django.utils import timezone

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
            'vaccination_status',
            'vaccination_proof',
            'vaccination_request',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-control'
            widget_type = getattr(field.widget, 'input_type', None)
            if widget_type in ('checkbox', 'radio'):
                css = 'form-check-input'
            elif widget_type == 'select' or field.widget.__class__.__name__.lower().startswith('select'):
                css = 'form-select'
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
        if 'vaccination_proof' in self.fields:
            self.fields['vaccination_proof'].widget.attrs.setdefault('accept', 'image/*,application/pdf')

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
            'vaccination_status',
            'vaccination_proof',
            'vaccination_request',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-control'
            widget_type = getattr(field.widget, 'input_type', None)
            if widget_type in ('checkbox', 'radio'):
                css = 'form-check-input'
            elif widget_type == 'select':
                css = 'form-select'
            field.widget.attrs.setdefault('class', css)
        self.fields['barangay'] = forms.ChoiceField(
            choices=[('', 'Select barangay')] + [(b, b) for b in BAYAWAN_BARANGAYS],
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        if 'photo' in self.fields:
            self.fields['photo'].widget.attrs.setdefault('accept', 'image/*')
        if 'vaccination_status' in self.fields:
            self.fields['vaccination_status'].required = True
            self.fields['vaccination_status'].choices = [
                ('', 'Select vaccination status'),
                (Dog.VaccinationStatus.VACCINATED, 'Vaccinated'),
                (Dog.VaccinationStatus.UNVACCINATED, 'Unvaccinated'),
            ]
        if 'vaccination_proof' in self.fields:
            self.fields['vaccination_proof'].widget.attrs.setdefault('accept', 'image/*,application/pdf')

    def clean(self):
        cleaned = super().clean()
        vaccination_status = cleaned.get('vaccination_status')
        vaccination_proof = cleaned.get('vaccination_proof')
        vaccination_request = cleaned.get('vaccination_request')

        if not vaccination_status:
            self.add_error('vaccination_status', 'Select vaccinated or unvaccinated.')
            return cleaned

        if vaccination_status == Dog.VaccinationStatus.UNVACCINATED:
            if not vaccination_request:
                self.add_error(
                    'vaccination_request',
                    'Unvaccinated dogs must request a vaccination appointment.',
                )
            if vaccination_proof:
                self.add_error(
                    'vaccination_proof',
                    'Vaccination proof is only required for vaccinated dogs.',
                )
        elif vaccination_status == Dog.VaccinationStatus.VACCINATED:
            if not vaccination_proof:
                self.add_error(
                    'vaccination_proof',
                    'Please upload proof of vaccination.',
                )
            if vaccination_request:
                self.add_error(
                    'vaccination_request',
                    'Vaccination request is only for unvaccinated dogs.',
                )

        return cleaned


class VaccinationScheduleForm(forms.Form):
    appointment_date = forms.DateField(required=True)
    appointment_time = forms.TimeField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['appointment_date'].widget = forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        )
        self.fields['appointment_time'].widget = forms.TimeInput(
            attrs={'class': 'form-control', 'type': 'time'}
        )

    def clean(self):
        cleaned = super().clean()
        date_value = cleaned.get('appointment_date')
        time_value = cleaned.get('appointment_time')
        if not date_value or not time_value:
            return cleaned
        if not hasattr(time_value, 'hour'):
            raise forms.ValidationError('Select a valid appointment time.')
        hours = time_value.hour
        minutes = time_value.minute
        appointment_dt = timezone.make_aware(
            timezone.datetime.combine(date_value, timezone.datetime.min.time())
        ) + timezone.timedelta(hours=hours, minutes=minutes)
        cleaned['vaccination_schedule'] = appointment_dt
        return cleaned
