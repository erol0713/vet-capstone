from django.contrib import admin

from .models import AdoptionReservation, ReclaimRequest


@admin.register(AdoptionReservation)
class AdoptionReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'dog', 'requester', 'status', 'reservation_date')
    list_filter = ('status',)


@admin.register(ReclaimRequest)
class ReclaimRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'dog', 'owner', 'status', 'reclaim_date')
    list_filter = ('status',)
