import os
from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings
import subprocess
from util.helpers import get_client_mac, get_connected_devices, authenticate_mac
from util.device_scanner import DeviceScanner


BASE_DIR = settings.BASE_DIR

FRONTEND_BASE_URL = settings.__getattr__('FRONTEND_BASE_URL')


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


def captive_detection(request):
    return redirect(f'{FRONTEND_BASE_URL}/captive', permanent=True)


def get_client_info(request):
    client_ip = request.META.get("REMOTE_ADDR")
    client_mac = get_client_mac(client_ip)

    return JsonResponse({"client_ip": client_ip, "client_mac": client_mac if client_mac else ''})
