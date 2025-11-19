from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Network
from devices.models import Device
from util.view_utils import BaseAPIView
import subprocess
from django.http import JsonResponse
from util.device_utils import meta_scanner
# from util.netscanner import net_scanner
from django.conf import settings

BASE_DIR = settings.BASE_DIR

FRONTEND_BASE_URL = settings.__getattr__('FRONTEND_BASE_URL')


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
                name=data.get('interface', 'ap0'),
                ssid=data.get('ssid'),
                security=data.get('security', 'wpa2'),
                password=data.get('password'),
                band=data.get('band', 'dual'),
                vlan_id=data.get('vlan_id'),
                max_clients=data.get('max_clients', 50),
                status=data.get('status', 'active')
            )
            subnet = data.get('subnet', None)
            if subnet:
                network.subnet = subnet

            # Create Network
            return self.json_response({
                'message': 'Network created successfully',
                'network': {
                    'id': str(network.id),
                    'name': network.name,
                    'ssid': network.ssid,
                    'interface': network.interface,
                    'status': network.status
                }
            }, 201)
        except Exception as e:
            return self.error_response(str(e), 400)


@csrf_exempt
def connect(request):
    if request.method == "POST":
        client_ip = request.META.get("REMOTE_ADDR")
        client_ip = client_ip if client_ip else meta_scanner.get_client_ip(request)

        client_mac = meta_scanner.get_mac_address(client_ip)
        host_name = meta_scanner.get_hostname_from_ip(client_ip)
        network = Network.objects.first()

        if client_mac:
            # Update devices
            device = Device.objects.get_or_create(
                mac_address=client_mac,
                ip_address=client_ip,
                hostname=host_name,
                network=network,
                is_authenticated=False,
                auth_status='pending',
                user_agent='',
            )
            # Update firewall rules
            subprocess.run(
                ["sudo", (BASE_DIR / "scripts/update_firewall.sh").as_posix()],
                check=False,
            )

            # Update auth status
            device.is_authenticated = True
            device.auth_status = 'authenticated'
            device.save()

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
