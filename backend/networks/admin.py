from django.contrib import admin
from .models import Network, NetworkReport


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'ssid', 'interface', 'security', 'band', 'status', 'connected_clients_count', 'created_at']
    list_filter = ['security', 'band', 'interface', 'status', 'created_at']
    search_fields = ['name', 'ssid', 'interface']
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


@admin.register(NetworkReport)
class NetworkReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'network', 'generated_by', 'period_start', 'period_end', 'created_at']
    list_filter = ['report_type', 'created_at']
    search_fields = ['title', 'network__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
