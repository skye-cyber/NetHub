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
    path("api/v1/captive", views.captive_detection),
    path("", views.captive_detection, name="portal"),
    path("api/dashboard", views.captive_detection, name="dashboard"),
    path("api/clientinfo/", views.get_client_info, name="clientinfo"),
]
