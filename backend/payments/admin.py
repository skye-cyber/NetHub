from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('host', 'plan', 'start_time', 'end_time')
    list_filter = ('start_time', 'end_time', 'elapsed_time')
    readonly_fields = [('created_at')]
