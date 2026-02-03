from django.contrib import admin

from .models import PenaltyCase, PenaltyChecklistItem, PenaltyLineItem


class PenaltyLineItemInline(admin.TabularInline):
    model = PenaltyLineItem
    extra = 0


@admin.register(PenaltyCase)
class PenaltyCaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'dog', 'owner', 'total_amount', 'is_finalized')
    list_filter = ('is_finalized',)
    inlines = [PenaltyLineItemInline]


@admin.register(PenaltyChecklistItem)
class PenaltyChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('code', 'section', 'description', 'default_amount', 'is_active')
    list_filter = ('section', 'is_active')
