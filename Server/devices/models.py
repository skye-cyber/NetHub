from django.db import models
import uuid


class Device(models.Model):
    AUTH_STATUS_CHOICES = [
        ('authenticated', 'Authenticated'),
        ('pending', 'Pending'),
        ('blocked', 'Blocked'),
    ]

    mac_address = models.CharField(max_length=17, primary_key=True)
    ip_address = models.GenericIPAddressField()
    hostname = models.CharField(max_length=100, blank=True, null=True)
    network = models.ForeignKey('networks.Network', on_delete=models.CASCADE, related_name='connected_devices')
    is_authenticated = models.BooleanField(default=False)
    auth_status = models.CharField(max_length=20, choices=AUTH_STATUS_CHOICES, default='pending')
    user_agent = models.TextField(blank=True, null=True)
    last_seen = models.DateTimeField(auto_now=True)
    upload_bytes = models.BigIntegerField(default=0)
    download_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'devices'
        ordering = ['-last_seen']

    def update_streak(self):
        self.streak += 1
        super().save()

    def reset_streak(self):
        self.streak = 1
        super().save()

    def __str__(self):
        return f"{self.hostname or 'Unknown'} ({self.mac_address})"

    @property
    def connection_duration(self):
        if self.last_seen and self.first_seen:
            return self.last_seen - self.first_seen
        return None


class DeviceHistory(models.Model):
    EVENT_CHOICES = [
        ('connect', 'Device Connected'),
        ('disconnect', 'Device Disconnected'),
        ('auth_success', 'Authentication Success'),
        ('auth_failed', 'Authentication Failed'),
        ('access_granted', 'Access Granted'),
        ('access_revoked', 'Access Revoked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='history')
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'device_history'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.device.mac_address} - {self.event_type}"
