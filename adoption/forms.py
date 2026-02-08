from django import forms
from django.utils import timezone

from .models import AdoptionReservation, ReclaimRequest


class AdoptionReservationForm(forms.ModelForm):
    class Meta:
        model = AdoptionReservation
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AdoptionScheduleForm(forms.Form):
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
        appointment_dt = timezone.make_aware(
            timezone.datetime.combine(date_value, timezone.datetime.min.time())
        ) + timezone.timedelta(hours=time_value.hour, minutes=time_value.minute)
        cleaned['appointment_schedule'] = appointment_dt
        return cleaned


class ReclaimRequestForm(forms.ModelForm):
    class Meta:
        model = ReclaimRequest
        fields = ('ownership_proof',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        proof_field = self.fields['ownership_proof']
        proof_field.required = True
        proof_field.widget.attrs.setdefault('class', 'form-control')
        proof_field.widget.attrs.setdefault('accept', 'image/*,application/pdf')
