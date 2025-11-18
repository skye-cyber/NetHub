from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
import json
from .models import SystemSettings, SettingsHistory


@method_decorator(csrf_exempt, name='dispatch')
class SettingsAPIView(View):

    def get(self, request):
        """Get current system settings"""
        try:
            settings = SystemSettings.objects.first()
            if not settings:
                # Create default settings if none exist
                settings = SystemSettings.objects.create()

            data = {
                'network_name': settings.network_name,
                'max_devices_per_user': settings.max_devices_per_user,
                'session_timeout': settings.session_timeout,
                'bandwidth_limit': settings.bandwidth_limit,
                'allow_guest_network': settings.allow_guest_network,

                'free_internet_enabled': settings.free_internet_enabled,
                'paid_mode_enabled': settings.paid_mode_enabled,
                'payment_gateway': settings.payment_gateway,
                'currency': settings.currency,
                'hourly_rate': float(settings.hourly_rate),
                'daily_rate': float(settings.daily_rate),
                'monthly_rate': float(settings.monthly_rate),

                'require_authentication': settings.require_authentication,
                'enable_captive_portal': settings.enable_captive_portal,
                'block_vpn_connections': settings.block_vpn_connections,
                'enable_mac_filtering': settings.enable_mac_filtering,
                'log_retention_days': settings.log_retention_days,

                'email_notifications': settings.email_notifications,
                'sms_notifications': settings.sms_notifications,
                'low_balance_alerts': settings.low_balance_alerts,
                'security_alerts': settings.security_alerts,
                'monthly_reports': settings.monthly_reports,

                'maintenance_mode': settings.maintenance_mode,
                'auto_backup': settings.auto_backup,
                'backup_frequency': settings.backup_frequency,
                'system_logs': settings.system_logs,
                'debug_mode': settings.debug_mode,
            }

            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def put(self, request):
        """Update system settings"""
        try:
            data = json.loads(request.body)
            settings = SystemSettings.objects.first()
            if not settings:
                settings = SystemSettings.objects.create()

            # Track changes for history
            changes = {}
            old_settings = {field.name: getattr(settings, field.name) for field in settings._meta.fields if not field.primary_key}

            # Update settings
            for key, value in data.items():
                if hasattr(settings, key) and getattr(settings, key) != value:
                    changes[key] = {
                        'old': getattr(settings, key),
                        'new': value
                    }
                    setattr(settings, key, value)

            settings.updated_by = request.user if request.user.is_authenticated else None
            settings.save()

            # Save to history if changes were made
            if changes and request.user.is_authenticated:
                SettingsHistory.objects.create(
                    settings=settings,
                    changed_by=request.user,
                    changes=changes,
                    reason=data.get('reason', 'Settings updated via admin panel')
                )

            return JsonResponse({
                'message': 'Settings updated successfully',
                'changes': changes
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@method_decorator(login_required)
def settings_history(request):
    """Get settings change history"""
    try:
        history = SettingsHistory.objects.select_related('changed_by').all()[:50]  # Last 50 changes
        data = []
        for entry in history:
            data.append({
                'id': str(entry.id),
                'changed_by': entry.changed_by.email,
                'changes': entry.changes,
                'timestamp': entry.timestamp.isoformat(),
                'reason': entry.reason
            })
        return JsonResponse({'history': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
