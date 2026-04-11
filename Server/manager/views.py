from .models import AccessCode
from django.views.decorators.http import require_POST
import base64
import io
import qrcode
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from networks.models import Network
from devices.models import Device, DeviceHistory
from util.view_utils import BaseAPIView
from django.utils import timezone
from util.netscanner import NetScanner
from .models import SystemSettings, SettingsHistory, AccessCode
from datetime import datetime
from .utils import get_random_user


net_scanner = NetScanner()


@method_decorator(csrf_exempt, name='dispatch')
class SettingsAPIView(View):

    def get(self, request, net_id=None):
        """Get current system settings"""
        try:

            settings = SystemSettings.objects.first() if not net_id else SystemSettings.objects.filter(id=net_id)

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


@method_decorator(csrf_exempt, name='dispatch')
class AccessCodeAPIView(BaseAPIView):

    def get(self, request):
        """Get all access codes"""
        try:
            codes = AccessCode.objects.select_related('network').all()
            data = []
            for code in codes:
                data.append({
                    'id': str(code.id),
                    'code': code.code,
                    'network': code.network.name,
                    'network_id': str(code.network.id),
                    'max_uses': code.max_uses,
                    'uses': code.uses,
                    'expires_at': code.expires_at.isoformat(),
                    'status': code.status,
                    'is_active': code.is_active,
                    'description': code.description,
                    'created_at': code.created_at.isoformat(),
                })
            return self.json_response({'access_codes': data})
        except Exception as e:
            print(e)
            return self.error_response(str(e), 500)

    def post(self, request):
        """Generate a new access code"""
        data = self.parse_json_body(request)
        if not data:
            return self.error_response('Invalid JSON')

        try:
            import secrets
            import string
            from django.utils import timezone

            # Generate random code
            alphabet = string.ascii_uppercase + string.digits
            code = 'NET-' + ''.join(secrets.choice(alphabet) for _ in range(8))

            # Get and validate network ID
            network_id = data.get('network')
            if not network_id:
                return self.error_response('Network ID is required', 400)

            # Clean the network ID by removing any quotes or whitespace
            network_id = str(network_id).strip('"\' ')

            try:
                # Convert to UUID if it's a valid UUID string
                from uuid import UUID
                network_id = str(UUID(network_id))
            except ValueError:
                pass  # Keep as string if it's not a valid UUID

            # Get the network
            try:
                network = Network.objects.get(id=network_id)
            except Network.DoesNotExist:
                return self.error_response('Network not found', 404)
            except Exception as e:
                return self.error_response(f'Invalid network ID: {str(e)}', 400)

            network = Network.objects.get(id=data.get('network'))

            # Get the creator (random user with privileges)
            creator = get_random_user()

            # Handle expiration date
            aware_datetime = None
            if data.get('expires_at'):
                try:
                    # Convert to naive datetime object
                    naive_datetime = datetime.strptime(f"{data.get('expires_at')} 00:00:00", '%Y-%m-%d %H:%M:%S')
                    # Convert to timezone-aware datetime
                    aware_datetime = timezone.make_aware(naive_datetime)
                except ValueError:
                    return self.error_response('Invalid date format. Use YYYY-MM-DD', 400)

            # Create access code
            access_code = AccessCode.objects.create(
                code=code,
                network=network,
                max_uses=data.get('max_uses', 10),  # Default to 10 uses
                expires_at=aware_datetime,
                description=data.get('description', ''),
                created_by=request.user if request.user.is_authenticated else creator,
                status='active'
            )

            return self.json_response({
                'access_code': {
                    'id': str(access_code.id),
                    'code': access_code.code,
                    'network': access_code.network.name,
                    'expires_at': access_code.expires_at.isoformat() if access_code.expires_at else None,
                    'max_uses': access_code.max_uses,
                    'uses': access_code.uses,
                    'status': access_code.status,
                    'description': access_code.description
                }
            }, 201)

        except Network.DoesNotExist:
            return self.error_response('Network not found', 404)
        except Exception as e:
            print(e)
            return self.error_response(str(e), 400)

    def delete(self, request, code_id):
        """Delete an access code"""
        try:
            # Get the access code
            access_code = AccessCode.objects.get(id=code_id)

            # Check if the user has permission to delete this code
            if not request.user.is_authenticated:
                return self.error_response('Authentication required', 401)

            # Check if the user is the creator or has admin privileges
            if (request.user != access_code.created_by
                and not request.user.is_staff
                    and not request.user.is_superuser):
                return self.error_response('Permission denied', 403)

            # Delete the access code
            access_code.delete()

            return self.json_response({
                'message': 'Access code deleted successfully',
                'code_id': str(code_id)
            }, 200)

        except AccessCode.DoesNotExist:
            return self.error_response('Access code not found', 404)
        except Exception as e:
            print(e)
            return self.error_response(str(e), 500)

    def put(self, request, code_id):
        """Update an access code (revoke or modify)"""
        try:
            # Get the access code
            access_code = AccessCode.objects.get(id=code_id)

            # Check if the user has permission to update this code
            if not request.user.is_authenticated:
                return self.error_response('Authentication required', 401)

            # Check if the user is the creator or has admin privileges
            if (request.user != access_code.created_by
                and not request.user.is_staff
                    and not request.user.is_superuser):
                return self.error_response('Permission denied', 403)

            data = self.parse_json_body(request)
            if not data:
                return self.error_response('Invalid JSON', 400)

            # Handle revocation
            if 'revoke' in data and data['revoke']:
                access_code.status = 'revoked'
                access_code.save()
                return self.json_response({
                    'message': 'Access code revoked successfully',
                    'code_id': str(code_id),
                    'status': access_code.status
                }, 200)

            # Handle other updates
            if 'max_uses' in data:
                access_code.max_uses = data['max_uses']
            if 'expires_at' in data:
                try:
                    naive_datetime = datetime.strptime(f"{data['expires_at']} 00:00:00", '%Y-%m-%d %H:%M:%S')
                    access_code.expires_at = timezone.make_aware(naive_datetime)
                except ValueError:
                    return self.error_response('Invalid date format. Use YYYY-MM-DD', 400)
            if 'description' in data:
                access_code.description = data['description']

            access_code.save()

            return self.json_response({
                'message': 'Access code updated successfully',
                'code_id': str(code_id),
                'max_uses': access_code.max_uses,
                'expires_at': access_code.expires_at.isoformat() if access_code.expires_at else None,
                'description': access_code.description
            }, 200)

        except AccessCode.DoesNotExist:
            return self.error_response('Access code not found', 404)
        except Exception as e:
            print(e)
            return self.error_response(str(e), 500)


class StatusAPIView(BaseAPIView):
    """System status and dashboard data"""

    def get(self, request):
        try:
            total_devices = Device.objects.count()
            authenticated_devices = Device.objects.filter(authenticated=True).count()
            total_networks = Network.objects.count()
            active_networks = Network.objects.filter(status='active').count()

            # Recent activity
            recent_activity = DeviceHistory.objects.select_related('device')[:10]
            activity_data = []
            for activity in recent_activity:
                activity_data.append({
                    'device_mac': activity.device.mac_address,
                    'event_type': activity.event_type,
                    'timestamp': activity.timestamp.isoformat(),
                    'ip_address': activity.ip_address
                })

            return self.json_response({
                'status': 'online',
                'statistics': {
                    'total_devices': total_devices,
                    'authenticated_devices': authenticated_devices,
                    'total_networks': total_networks,
                    'active_networks': active_networks,
                },
                'recent_activity': activity_data,
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            return self.error_response(str(e), 500)


@method_decorator(csrf_exempt, name='dispatch')
class AdminAccessAPIView(BaseAPIView):
    """Handle device access granting/revoking"""

    def post(self, request, mac_address):
        """Grant access to a device"""
        try:
            device = Device.objects.get(mac_address=mac_address)
            device.authenticated = True
            device.auth_status = 'authenticated'
            device.save()

            # Log the event
            DeviceHistory.objects.create(
                device=device,
                event_type='access_granted',
                ip_address=device.ip_address,
                details={'action': 'admin_granted'}
            )

            return self.json_response({
                'message': f'Access granted for device {mac_address}',
                'device': {
                    'mac_address': device.mac_address,
                    'authenticated': device.authenticated,
                    'auth_status': device.auth_status
                }
            })
        except Device.DoesNotExist:
            return self.error_response('Device not found', 404)
        except Exception as e:
            return self.error_response(str(e), 400)

    def delete(self, request, mac_address):
        """Revoke access from a device"""
        try:
            device = Device.objects.get(mac_address=mac_address)
            device.authenticated = False
            device.auth_status = 'blocked'
            device.save()

            # Log the event
            DeviceHistory.objects.create(
                device=device,
                event_type='access_revoked',
                ip_address=device.ip_address,
                details={'action': 'admin_revoked'}
            )

            return self.json_response({
                'message': f'Access revoked for device {mac_address}',
                'device': {
                    'mac_address': device.mac_address,
                    'authenticated': device.authenticated,
                    'auth_status': device.auth_status
                }
            })
        except Device.DoesNotExist:
            return self.error_response('Device not found', 404)
        except Exception as e:
            return self.error_response(str(e), 400)


def admin_check_access(request, mac):
    """Check access for specific MAC"""
    # Get device info
    device = net_scanner.get_connected_devices()

    if device:
        return JsonResponse(
            {
                "mac": mac,
                "authenticated": device.is_authenticated,
                "device_info": device,
                "status": device.auth_status
            }
        )
    return JsonResponse({
        "mac": mac,
        "authenticated": False,
        "device_info": {},
        "status": False
    })


def heartbeat(request):
    """Check access for specific MAC"""
    # Get device info
    return JsonResponse({
        "success": True,
        "status": True
    })


@csrf_exempt
@require_POST
def generate_qr_code(request):
    """
    Generate a QR code containing access code and band data.
    Expects JSON with:
    - code_id: UUID of the access code
    - band_data: Additional data to include in the QR code
    """
    try:
        import json
        data = json.loads(request.body.decode())

        code_id = data.get('code_id')
        band_data = data.get('band_data', {})

        if not code_id:
            return JsonResponse({
                'status': 'error',
                'message': 'code_id is required',
                'code': 400
            }, status=400)

        try:
            # Get the access code
            access_code = AccessCode.objects.get(id=code_id)

            # Prepare data for QR code
            qr_data = {
                'access_code': access_code.code,
                'network': access_code.network.name,
                'expires_at': access_code.expires_at.isoformat() if access_code.expires_at else None,
                'max_uses': access_code.max_uses,
                'uses': access_code.uses,
                'status': access_code.status,
                'description': access_code.description,
                'band_data': band_data
            }

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)

            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64 for JSON response
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return JsonResponse({
                'status': 'success',
                'qr_code': img_str,
                'data': qr_data,
                'code': 200
            }, status=200)

        except AccessCode.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Access code not found',
                'code': 404
            }, status=404)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON',
            'code': 400
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'code': 500
        }, status=500)
