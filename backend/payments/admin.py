from .models import (
    PricingPlan,
    PaymentTransaction,
    PaymentQueue,
    MpesaCallback,
    InternetAccess
)
from django.utils.html import format_html
from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('host', 'plan', 'start_time', 'end_time')
    list_filter = ('start_time', 'end_time', 'elapsed_time')
    readonly_fields = [('created_at')]


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration', 'price', 'original_price', 'savings_display', 'is_popular', 'is_active', 'display_order']
    list_filter = ['duration', 'is_popular', 'is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'savings_display']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'duration', 'duration_minutes')
        }),
        ('Pricing', {
            'fields': ('price', 'original_price', 'savings_display')
        }),
        ('Features', {
            'fields': ('features',)
        }),
        ('Display', {
            'fields': ('is_popular', 'is_active', 'display_order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def savings_display(self, obj):
        savings = obj.savings_percentage
        if savings > 0:
            return format_html('<span style="color: green;">{}% OFF</span>', savings)
        return '-'
    savings_display.short_description = 'Savings'


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'payment_method', 'status', 'initiated_at', 'completed_at']
    list_filter = ['status', 'payment_method', 'initiated_at', 'completed_at']
    search_fields = ['user__email', 'mpesa_transaction_id', 'mpesa_phone']
    readonly_fields = ['initiated_at', 'processed_at', 'completed_at', 'is_expired_display']
    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'plan', 'amount', 'payment_method', 'status')
        }),
        ('M-Pesa Details', {
            'fields': ('mpesa_phone', 'mpesa_transaction_id', 'mpesa_checkout_request_id', 'mpesa_merchant_request_id'),
            'classes': ('collapse',)
        }),
        ('Card Details', {
            'fields': ('card_last4', 'card_brand'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('queue_position', 'retry_count', 'expires_at', 'is_expired_display')
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'processed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def is_expired_display(self, obj):
        return obj.is_expired
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Expired'


@admin.register(InternetAccess)
class InternetAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_time', 'end_time', 'is_active_display', 'remaining_time_display']
    list_filter = ['status', 'start_time', 'end_time']
    search_fields = ['user__email', 'plan__name']
    readonly_fields = ['start_time', 'end_time', 'created_at', 'updated_at', 'is_active_display', 'remaining_time_display']

    def is_active_display(self, obj):
        return obj.is_active
    is_active_display.boolean = True
    is_active_display.short_description = 'Is Active'

    def remaining_time_display(self, obj):
        return f"{obj.remaining_time} minutes"
    remaining_time_display.short_description = 'Remaining Time'


@admin.register(MpesaCallback)
class MpesaCallbackAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'received_at', 'processed']
    list_filter = ['processed', 'received_at']
    search_fields = ['transaction__mpesa_transaction_id']
    readonly_fields = ['received_at']


@admin.register(PaymentQueue)
class PaymentQueueAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'position', 'estimated_wait_time', 'entered_at', 'processed_at']
    list_filter = ['processed_at', 'entered_at']
    search_fields = ['transaction__user__email']
    readonly_fields = ['entered_at', 'processed_at']
