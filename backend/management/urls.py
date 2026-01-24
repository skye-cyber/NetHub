from django.urls import path
from . import views

urlpatterns = [
    path('api/status/heartbeat', views.heartbeat, name='server_heartbeat'),
    path('api/settings', views.SettingsAPIView.as_view(), name='settings'),
    path('api/settings/history', views.settings_history, name='settings_history'),
    # Access codes
    path('api/access-codes', views.AccessCodeAPIView.as_view(), name='access_codes'),
    path('api/access-codes/delete/<str:code_id>', views.AccessCodeAPIView.as_view(), name='delete_code'),
    path('api/access-codes/revoke/<str:code_id>', views.AccessCodeAPIView.as_view(), name='revoke_code'),
    path('api/access-codes/qr-code/<str:code_id>', views.generate_qr_code, name='qr_code'),

    # Reports
    path('api/status/report', views.StatusAPIView.as_view(), name='status_report'),
    path('api/admin/grant_access/v2/<str:mac_address>', views.AdminAccessAPIView.as_view(), name='grant_access'),
    path('api/admin/revoke_access/v2/<str:mac_address>', views.AdminAccessAPIView.as_view(), name='revoke_access'),
    path(
        "api/admin/check_access/<str:mac>",
        views.admin_check_access,
        name="admin_check_access",
    ),
]
