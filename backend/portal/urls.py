from django.urls import path
from . import views

urlpatterns = [
    path("hotspot-detect.html", views.captive_detection),
    path("library/test/success.html", views.captive_detection),
    path("ncsi.txt", views.captive_detection),
    path("connecttest.txt", views.captive_detection),
    path("fwlink/", views.captive_detection),
    path("generate_204", views.captive_detection),
    path("redirect", views.captive_detection),
    path("captiveportal", views.captive_detection),
    path("api/v1/captive", views.captive_api),
    path("", views.portal_view, name="portal"),
    path("connect", views.connect, name="connect"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("status", views.status, name="status"),
    path("admin/devices", views.admin_devices, name="admin_devices"),
    path(
        "admin/check_access/<str:mac>",
        views.admin_check_access,
        name="admin_check_access",
    ),
    path(
        "admin/grant_access/<str:mac>",
        views.admin_grant_access,
        name="admin_grant_access",
    ),
    path(
        "admin/revoke_access/<str:mac>",
        views.admin_revoke_access,
        name="admin_revoke_access",
    ),
    path("health", views.health, name="health"),
]
