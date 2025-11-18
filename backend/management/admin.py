from django.contrib import admin
from django.utils.html import format_html
from .models import SystemSettings, SettingsHistory


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['network_name', 'free_internet_enabled', 'paid_mode_enabled', 'maintenance_mode', 'updated_at']
    list_filter = ['free_internet_enabled', 'paid_mode_enabled', 'maintenance_mode', 'updated_at']
    readonly_fields = ['created_at', 'updated_at', 'updated_by']
    fieldsets = (
        ('Network Configuration', {
            'fields': (
                'network_name', 'max_devices_per_user', 'session_timeout',
                'bandwidth_limit', 'allow_guest_network'
            ),
            'classes': ('collapse',)
        }),
        ('Payment & Monetization', {
            'fields': (
                'free_internet_enabled', 'paid_mode_enabled', 'payment_gateway',
                'currency', 'hourly_rate', 'daily_rate', 'monthly_rate'
            ),
            'classes': ('collapse',)
        }),
        ('Security Settings', {
            'fields': (
                'require_authentication', 'enable_captive_portal', 'block_vpn_connections',
                'enable_mac_filtering', 'log_retention_days'
            ),
            'classes': ('collapse',)
        }),
        ('Notification Settings', {
            'fields': (
                'email_notifications', 'sms_notifications', 'low_balance_alerts',
                'security_alerts', 'monthly_reports'
            ),
            'classes': ('collapse',)
        }),
        ('System Configuration', {
            'fields': (
                'maintenance_mode', 'auto_backup', 'backup_frequency',
                'system_logs', 'debug_mode'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow one settings instance
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion of settings


@admin.register(SettingsHistory)
class SettingsHistoryAdmin(admin.ModelAdmin):
    list_display = ['changed_by', 'changes_preview', 'timestamp', 'reason']
    list_filter = ['timestamp', 'changed_by']
    search_fields = ['changed_by__email', 'reason']
    readonly_fields = ['timestamp', 'changed_by', 'changes_formatted']

    def changes_preview(self, obj):
        changes = obj.changes
        if changes:
            return format_html('<code>{}</code>', str(changes)[:100] + '...' if len(str(changes)) > 100 else str(changes))
        return '-'
    changes_preview.short_description = 'Changes'

    def changes_formatted(self, obj):
        changes = obj.changes
        if changes:
            formatted = '<ul>'
            for field, values in changes.items():
                formatted += f'<li><strong>{field}</strong>: {values["old"]} → {values["new"]}</li>'
            formatted += '</ul>'
            return format_html(formatted)
        return '-'
    changes_formatted.short_description = 'Changes Details'
