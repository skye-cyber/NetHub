from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User management
    path('api/users/', views.UserManagementAPIView.as_view(), name='users'),
]
