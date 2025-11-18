import uuid
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models


class Device(models.Model):
    AUTH_STATUS_CHOICES = [
        ('authenticated', 'Authenticated'),
        ('pending', 'Pending'),
        ('blocked', 'Blocked'),
    ]

    mac_address = models.CharField(max_length=17, primary_key=True)
    ip_address = models.GenericIPAddressField()
    hostname = models.CharField(max_length=100, blank=True, null=True)
    network = models.ForeignKey('portal.Network', on_delete=models.CASCADE, related_name='connected_devices')
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


class Network(models.Model):
    SECURITY_CHOICES = [
        ('open', 'Open'),
        ('wpa2', 'WPA2 Personal'),
        ('wpa3', 'WPA3 Personal'),
        ('enterprise', 'WPA2 Enterprise'),
    ]

    BAND_CHOICES = [
        ('2.4GHz', '2.4 GHz'),
        ('5GHz', '5 GHz'),
        ('dual', 'Dual Band (2.4GHz & 5GHz)'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    ssid = models.CharField(max_length=32, unique=True)
    security = models.CharField(max_length=20, choices=SECURITY_CHOICES, default='wpa2')
    password = models.CharField(max_length=128, blank=True, null=True)
    band = models.CharField(max_length=20, choices=BAND_CHOICES, default='dual')
    vlan_id = models.IntegerField(blank=True, null=True)
    max_clients = models.IntegerField(default=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'networks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.ssid})"

    @property
    def connected_clients_count(self):
        return self.connected_devices.filter(authenticated=True).count()


class AccessCode(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    network = models.ForeignKey(Network, on_delete=models.CASCADE, related_name='access_codes')
    max_uses = models.IntegerField(default=10)
    uses = models.IntegerField(default=0)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'access_codes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.network.name}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_active(self):
        return self.status == 'active' and not self.is_expired and self.uses < self.max_uses


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


class NetworkReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('usage', 'Usage Statistics'),
        ('security', 'Security Audit'),
        ('performance', 'Performance Metrics'),
        ('devices', 'Device Report'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    network = models.ForeignKey(Network, on_delete=models.CASCADE, related_name='reports')
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'network_reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.network.name}"
