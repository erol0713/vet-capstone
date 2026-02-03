from django import forms

from .models import AdoptionReservation, ReclaimRequest


class AdoptionReservationForm(forms.ModelForm):
    class Meta:
        model = AdoptionReservation
        fields = ('reservation_date',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
            field.widget.attrs.setdefault('type', 'date')


class ReclaimRequestForm(forms.ModelForm):
    class Meta:
        model = ReclaimRequest
        fields = ('reclaim_date',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
            field.widget.attrs.setdefault('type', 'date')
