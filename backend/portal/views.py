from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings
from util.device_utils import meta_scanner


BASE_DIR = settings.BASE_DIR

FRONTEND_BASE_URL = settings.__getattr__('FRONTEND_BASE_URL')


def captive_detection(request):
    return redirect(f'{FRONTEND_BASE_URL}/captive', permanent=True)


def get_client_info(request):
    client_ip = request.META.get("REMOTE_ADDR")
    client_mac = meta_scanner.get_mac_address(client_ip)

    return JsonResponse({"client_ip": client_ip, "client_mac": client_mac if client_mac else ''})
