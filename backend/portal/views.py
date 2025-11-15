from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# from .models import Device
import subprocess
from pathlib import Path
from util.helpers import get_client_mac
from util.device_scanner import authenticate_mac

BASE_DIR = Path(__file__).parent.parent


def dashboard(request):
    return redirect("portal")


def status(request):
    return redirect("portal")


def admin_devices(request):
    return redirect("portal")


def admin_check_access(request):
    return redirect("portal")


def admin_grant_access(request):
    return redirect("portal")


def admin_revoke_access(request):
    return redirect("portal")


def health(request):
    return redirect("portal")


def captive_detection(request):
    return redirect("portal")


def captive_api(request):
    return redirect("portal")


def portal_view(request):
    client_ip = request.META.get("REMOTE_ADDR")
    # Implement MAC address retrieval logic
    client_mac = get_client_mac(client_ip)
    return render(
        request, "portal.html", {"client_ip": client_ip, "client_mac": client_mac}
    )


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
                    "redirect_url": f"/dashboard?mac={client_mac}&ip={client_ip}",
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
