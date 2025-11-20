from django.db import models
import uuid
from django.contrib.auth.models import User


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
    subnet = models.IPAddressField(default='192.168.1.0/24')
    interface = models.CharField(max_length=10, null=True)
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


''' TODO:
Implement network tracking for report generation and nalytics
'''
