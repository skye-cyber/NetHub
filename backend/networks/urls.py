from django.urls import path
from . import views

app_name = 'networks'

urlpatterns = [
    # Network management
    path('api/networks/', views.NetworkAPIView.as_view(), name='networks'),
    path("api/connect", views.connect, name="connect"),
]
