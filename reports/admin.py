from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'report_type',
        'status',
        'location_method',
        'reported_by',
        'contact_name',
        'location',
    )
    list_filter = ('report_type', 'status', 'location_method')
    search_fields = ('location', 'contact_name', 'contact_phone', 'contact_email', 'description', 'reported_by__email')
