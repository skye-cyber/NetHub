from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # AP Manager WebSocket endpoint
    re_path(r'ws/ap-manager/$', consumers.APManagerConsumer.as_asgi()),

    # Frontend WebSocket endpoint
    re_path(r'ws/frontend/$', consumers.FrontendConsumer.as_asgi()),

    # Device monitoring WebSocket
    # re_path(r'ws/devices/$', consumers.DeviceConsumer.as_asgi()),

    # Individual device channel
    # re_path(r'ws/device/(?P<mac>[^/]+)/$', consumers.DeviceDetailConsumer.as_asgi()),
]
