from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    # Device management
    path('api/devices', views.DeviceAPIView.as_view(), name='devices'),
]
