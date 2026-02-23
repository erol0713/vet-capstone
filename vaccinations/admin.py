from django.contrib import admin

from .models import VaccinationRecord


@admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dog',
        'vaccine_type',
        'vaccinated_date',
        'expiration_date',
        'from_owner_proof',
    )
    list_filter = ('vaccine_type', 'from_owner_proof')
