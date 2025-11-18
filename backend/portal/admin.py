from .models import (
    Device,
    DeviceHistory,
    Network,
    AccessCode,
    NetworkReport,
)
from django.contrib import admin


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'ssid', 'security', 'band', 'status', 'connected_clients_count', 'created_at']
    list_filter = ['security', 'band', 'status', 'created_at']
    search_fields = ['name', 'ssid']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'ssid', 'status')
        }),
        ('Network Configuration', {
            'fields': ('security', 'password', 'band', 'vlan_id', 'max_clients')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AccessCode)
class AccessCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'network', 'status', 'uses', 'max_uses', 'expires_at', 'created_by', 'created_at']
    list_filter = ['status', 'network', 'created_at']
    search_fields = ['code', 'network__name', 'description']
    readonly_fields = ['uses', 'created_at']

    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = 'Active'


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['mac_address', 'hostname', 'ip_address', 'network', 'auth_status', 'is_authenticated', 'last_seen']
    list_filter = ['auth_status', 'is_authenticated', 'network', 'last_seen']
    search_fields = ['mac_address', 'hostname', 'ip_address']
    readonly_fields = ['created_at', 'last_seen', 'upload_bytes', 'download_bytes']

    def connection_duration_display(self, obj):
        duration = obj.connection_duration
        if duration:
            return str(duration).split('.')[0]
        return 'N/A'
    connection_duration_display.short_description = 'Connection Duration'


@admin.register(DeviceHistory)
class DeviceHistoryAdmin(admin.ModelAdmin):
    list_display = ['device', 'event_type', 'ip_address', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['device__mac_address', 'device__hostname', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(NetworkReport)
class NetworkReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'network', 'generated_by', 'period_start', 'period_end', 'created_at']
    list_filter = ['report_type', 'created_at']
    search_fields = ['title', 'network__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
