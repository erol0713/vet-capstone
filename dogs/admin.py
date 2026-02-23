from django.contrib import admin

from .models import Dog


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'status',
        'registration_approval_status',
        'vaccination_status',
        'vaccination_request',
        'vaccination_schedule',
        'barangay',
        'kennel_slot',
        'owner',
    )
    list_filter = (
        'status',
        'registration_approval_status',
        'vaccination_status',
        'vaccination_request',
        'barangay',
    )
    search_fields = ('barangay', 'kennel_slot', 'owner__email', 'name')
