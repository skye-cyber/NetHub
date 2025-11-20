from django.urls import path
from . import views
from .utils import flushSession

app_name = 'users'

urlpatterns = [
    # User management
    path('api/users/', views.UserManagementAPIView.as_view(), name='users'),
    path("session/flush/", flushSession, name="flush_session"),
]
