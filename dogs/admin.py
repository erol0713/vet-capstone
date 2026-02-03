from django.contrib import admin

from .models import Dog


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'barangay', 'kennel_slot', 'owner')
    list_filter = ('status', 'barangay')
    search_fields = ('barangay', 'kennel_slot')
