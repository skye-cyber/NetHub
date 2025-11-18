from django.urls import path
from . import views

urlpatterns = [
    path('api/settings/', views.SettingsAPIView.as_view(), name='settings'),
    path('api/settings/history/', views.settings_history, name='settings_history'),
]
