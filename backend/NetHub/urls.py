from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("portal.urls")),
    path("", include("payments.urls")),
    path("", include("users.urls")),
    path("", include("management.urls")),
    path("", include("networks.urls")),
    path("", include("devices.urls")),
]
