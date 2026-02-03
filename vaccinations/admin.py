from django.contrib import admin

from .models import VaccinationRecord


@admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'dog', 'vaccine_type', 'vaccinated_date', 'expiration_date')
    list_filter = ('vaccine_type',)
