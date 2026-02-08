from django.contrib import admin

from .models import AdoptionReservation, ReclaimRequest


@admin.register(AdoptionReservation)
class AdoptionReservationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dog',
        'requester',
        'status',
        'reservation_date',
        'eligibility_notified_at',
        'confirmed_at',
        'appointment_schedule',
    )
    list_filter = ('status',)


@admin.register(ReclaimRequest)
class ReclaimRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'dog', 'owner', 'status', 'ownership_proof')
    list_filter = ('status',)
