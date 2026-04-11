from django.contrib import admin
from .models import Device, DeviceHistory


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
