from django.urls import path
from . import views

app_name = 'portal'

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
    path("", views.captive_api, name="portal"),
    path("api/connect", views.connect, name="connect"),
    path("api/dashboard", views.dashboard, name="dashboard"),
    path("api/status", views.status, name="status"),
    path("api/clientinfo/", views.get_client_info, name="clientinfo"),
    path("api/admin/devices", views.admin_devices, name="admin_devices"),
    path(
        "api/admin/check_access/<str:mac>",
        views.admin_check_access,
        name="admin_check_access",
    ),
    path(
        "api/admin/grant_access/<str:mac>",
        views.admin_grant_access,
        name="admin_grant_access",
    ),
    path(
        "api/admin/revoke_access/<str:mac>",
        views.admin_revoke_access,
        name="admin_revoke_access",
    ),
    path("api/health", views.health, name="health"),

    # Network management
    path('api/networks/', views.NetworkAPIView.as_view(), name='networks'),

    # Access codes
    path('api/access-codes/', views.AccessCodeAPIView.as_view(), name='access_codes'),

    # Device management
    path('api/devices/v2/', views.DeviceAPIView.as_view(), name='devices'),
    path('api/admin/grant_access/v2/<str:mac_address>/', views.AdminAccessAPIView.as_view(), name='grant_access'),
    path('api/admin/revoke_access/v2/<str:mac_address>/', views.AdminAccessAPIView.as_view(), name='revoke_access'),

    # System status
    path('api/status/v2/', views.StatusAPIView.as_view(), name='status'),

    # Reports
    path('api/reports/', views.StatusAPIView.as_view(), name='reports'),
]
