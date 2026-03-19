from django.contrib import admin
from .models import Event, Round, Contestant, PointTransaction


class RoundInline(admin.TabularInline):
    model = Round
    extra = 1


class ContestantInline(admin.TabularInline):
    model = Contestant
    extra = 0
    readonly_fields = ['points', 'registered_at']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'created_at']
    inlines = [RoundInline]
    search_fields = ['name']


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'round_head', 'created_at']
    list_filter = ['event']
    inlines = [ContestantInline]
    search_fields = ['name', 'event__name']


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    list_display = ['name', 'roll_number', 'phone_number', 'round', 'points', 'registered_at']
    list_filter = ['round__event', 'round']
    search_fields = ['name', 'roll_number', 'phone_number']
    readonly_fields = ['registered_at']


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ['contestant', 'transaction_type', 'points', 'reason', 'performed_by', 'created_at']
    list_filter = ['transaction_type', 'contestant__round']
    readonly_fields = ['created_at']
