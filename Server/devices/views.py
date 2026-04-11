from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import (
    Device,
    # DeviceHistory,
)
from util.view_utils import BaseAPIView


@method_decorator(csrf_exempt, name='dispatch')
class DeviceAPIView(BaseAPIView):

    def get(self, request):
        """Get all devices"""
        try:
            # online_devices = net_scanner() let celery update devices NO manual scans
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

'''
Implement post for admin device registraction
'''
