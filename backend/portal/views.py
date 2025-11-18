from .models import (
    Device,
    DeviceHistory,
    Network,
    User,
    AccessCode,
)
from users.models import UserProfile
import json
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import os
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import subprocess
from pathlib import Path
from util.helpers import get_client_mac, get_connected_devices, authenticate_mac
from util.device_scanner import DeviceScanner
from django.utils import timezone

BASE_DIR = Path(__file__).parent.parent
FRONTEND_BASE_URL = settings.__getattr__('FRONTEND_BASE_URL')
AUTH_FILE = BASE_DIR / "auth/authenticated_macs"


def dashboard(request):
    return redirect("portal")


def status(request):
    """Admin endpoint to see connected devices"""
    devices = get_connected_devices()
    authenticated_macs = []

    if os.path.exists(AUTH_FILE.as_posix()):
        with open(AUTH_FILE, "r") as f:
            authenticated_macs = [line.strip() for line in f if line.strip()]

    return JsonResponse({
        'status': 'online',
        "connected_devices": devices,
        "authenticated_devices": authenticated_macs,
        "total_connected": len(devices),
        "total_authenticated": len(authenticated_macs),
    })


def admin_devices(request):
    """Admin page to view all devices"""
    scanner = DeviceScanner()
    all_devices = scanner.get_connected_devices()

    # Add authentication status to each device
    for device in all_devices:
        device["authenticated"] = scanner.is_authenticated(device["mac"])

    authenticated_count = len([d for d in all_devices if d["authenticated"]])
    blocked_count = len(all_devices) - authenticated_count

    return JsonResponse(
        {
            "devices": all_devices,
            "total_devices": len(all_devices),
            "authenticated_count": authenticated_count,
            "blocked_count": blocked_count,
        }
    )


def admin_check_access(request, mac):
    """Check access for specific MAC"""
    scanner = DeviceScanner()

    # Get device info
    devices = scanner.get_connected_devices()
    device_info = next((d for d in devices if d["mac"] == mac), None)

    is_authenticated = scanner.is_authenticated(mac)

    return JsonResponse(
        {
            "mac": mac,
            "authenticated": is_authenticated,
            "device_info": device_info,
            "status": "authenticated" if is_authenticated else "blocked",
        }
    )


def admin_grant_access(request, mac):
    """Manually grant access to a device"""
    if authenticate_mac(mac):
        subprocess.run(
            ["sudo", (BASE_DIR / "scripts/update_firewall.sh").as_posix()], check=False
        )
        return JsonResponse({"status": "success", "message": f"Access granted for {mac}"})
    else:
        return JsonResponse(
            {"status": "error", "message": f"Failed to grant access for {mac}"},
            400)


def admin_revoke_access(request, mac):
    """Manually revoke access from a device"""
    try:
        auth_file = (BASE_DIR / "auth/authenticated_macs").as_posix()
        # Remove MAC from auth file
        if os.path.exists(auth_file):
            with open(auth_file, "r") as f:
                lines = f.readlines()
            with open(auth_file, "w") as f:
                for line in lines:
                    if line.strip() != mac:
                        f.write(line)

        # Update firewall
        subprocess.run(
            ["sudo", (BASE_DIR / "scripts/update_firewall.sh").as_posix()],
            check=False,
        )
        return JsonResponse({"status": "success", "message": f"Access revoked for {mac}"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def health(request):
    return JsonResponse({"status": "healthy"})


def captive_detection(request):
    return redirect(f'{FRONTEND_BASE_URL}/captive', permanent=True)


def captive_api(request):
    return captive_detection(request)


def get_client_info(request):
    client_ip = request.META.get("REMOTE_ADDR")
    client_mac = get_client_mac(client_ip)

    return JsonResponse({"client_ip": client_ip, "client_mac": client_mac if client_mac else ''})


@csrf_exempt
def connect(request):
    if request.method == "POST":
        client_ip = request.META.get("REMOTE_ADDR")
        client_mac = get_client_mac(client_ip)

        if client_mac and authenticate_mac(client_mac):
            # Update firewall rules
            subprocess.run(
                ["sudo", (BASE_DIR / "scripts/update_firewall.sh").as_posix()],
                check=False,
            )
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Access granted! Welcome to the network.",
                    "dashboard": True,
                    "redirect_url": f"{FRONTEND_BASE_URL}/dashboard",
                    "client_mac": client_mac,
                    "client_ip": client_ip,
                }
            )
        return JsonResponse(
            {
                "status": "error",
                "message": "Could not authenticate device. Please try again.",
            },
            status=400,
        )


class BaseAPIView(View):
    """Base API view with common functionality"""

    def json_response(self, data, status=200):
        return JsonResponse(data, status=status)

    def error_response(self, message, status=400):
        return self.json_response({'error': message}, status=status)

    def parse_json_body(self, request):
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None


@method_decorator(csrf_exempt, name='dispatch')
class NetworkAPIView(BaseAPIView):

    def get(self, request):
        """Get all networks"""
        try:
            networks = Network.objects.all()
            data = []
            for network in networks:
                data.append({
                    'id': str(network.id),
                    'name': network.name,
                    'ssid': network.ssid,
                    'security': network.security,
                    'band': network.band,
                    'status': network.status,
                    'clients': network.connected_clients_count,
                    'max_clients': network.max_clients,
                    'created_at': network.created_at.isoformat(),
                })
            return self.json_response({'networks': data})
        except Exception as e:
            return self.error_response(str(e), 500)

    def post(self, request):
        """Create a new network"""
        data = self.parse_json_body(request)
        if not data:
            return self.error_response('Invalid JSON')

        try:
            network = Network.objects.create(
                name=data.get('name'),
                ssid=data.get('ssid'),
                security=data.get('security', 'wpa2'),
                password=data.get('password'),
                band=data.get('band', 'dual'),
                vlan_id=data.get('vlan_id'),
                max_clients=data.get('max_clients', 50),
                status=data.get('status', 'active')
            )

            return self.json_response({
                'message': 'Network created successfully',
                'network': {
                    'id': str(network.id),
                    'name': network.name,
                    'ssid': network.ssid,
                    'status': network.status
                }
            }, 201)
        except Exception as e:
            return self.error_response(str(e), 400)


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
            return self.error_response(str(e), 500)

    def post(self, request):
        """Generate a new access code"""
        data = self.parse_json_body(request)
        if not data:
            return self.error_response('Invalid JSON')

        try:
            import secrets
            import string

            # Generate random code
            alphabet = string.ascii_uppercase + string.digits
            code = 'NET-' + ''.join(secrets.choice(alphabet) for _ in range(8))

            network = Network.objects.get(id=data.get('network_id'))

            access_code = AccessCode.objects.create(
                code=code,
                network=network,
                max_uses=data.get('max_uses', 10),
                expires_at=data.get('expires_at'),
                description=data.get('description'),
                created_by=request.user if request.user.is_authenticated else None
            )

            return self.json_response({
                'message': 'Access code generated successfully',
                'access_code': {
                    'id': str(access_code.id),
                    'code': access_code.code,
                    'network': access_code.network.name,
                    'expires_at': access_code.expires_at.isoformat(),
                    'max_uses': access_code.max_uses
                }
            }, 201)
        except Network.DoesNotExist:
            return self.error_response('Network not found', 404)
        except Exception as e:
            return self.error_response(str(e), 400)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceAPIView(BaseAPIView):

    def get(self, request):
        """Get all devices"""
        try:
            devices = Device.objects.select_related('network').all()
            data = []
            for device in devices:
                data.append({
                    'mac_address': device.mac_address,
                    'ip_address': device.ip_address,
                    'hostname': device.hostname,
                    'network': device.network.name,
                    'authenticated': device.authenticated,
                    'auth_status': device.auth_status,
                    'first_seen': device.first_seen.isoformat(),
                    'last_seen': device.last_seen.isoformat(),
                    'upload_mb': round(device.upload_bytes / (1024 * 1024), 2),
                    'download_mb': round(device.download_bytes / (1024 * 1024), 2),
                })
            return self.json_response({'devices': data})
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
