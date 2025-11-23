from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
import uuid


class SystemSettings(models.Model):
    PAYMENT_GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('razorpay', 'Razorpay'),
        ('mpesa', 'M-Pesa'),
        ('manual', 'Manual Payment'),
    ]

    CURRENCY_CHOICES = [
        ('KSH', 'Kenya Shillings'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('INR', 'Indian Rupee'),
    ]

    BACKUP_FREQUENCY_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Network Settings
    network = models.ForeignKey('networks.Network', on_delete=models.CASCADE, null=True)
    network_name = models.CharField(max_length=100, default="NetHub")
    max_devices_per_user = models.IntegerField(default=5)
    session_timeout = models.IntegerField(default=24)  # hours
    bandwidth_limit = models.IntegerField(default=1000)  # MB
    allow_guest_network = models.BooleanField(default=True)

    # Payment & Monetization
    free_internet_enabled = models.BooleanField(default=False)
    paid_mode_enabled = models.BooleanField(default=True)
    payment_gateway = models.CharField(max_length=20, choices=PAYMENT_GATEWAY_CHOICES, default='mpesa')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='KSH')
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=2.50)
    daily_rate = models.DecimalField(max_digits=6, decimal_places=2, default=15.00)
    monthly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=99.00)

    # Security Settings
    require_authentication = models.BooleanField(default=True)
    enable_captive_portal = models.BooleanField(default=True)
    block_vpn_connections = models.BooleanField(default=False)
    enable_mac_filtering = models.BooleanField(default=True)
    log_retention_days = models.IntegerField(default=90)

    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    low_balance_alerts = models.BooleanField(default=True)
    security_alerts = models.BooleanField(default=True)
    monthly_reports = models.BooleanField(default=True)

    # System Settings
    maintenance_mode = models.BooleanField(default=False)
    auto_backup = models.BooleanField(default=True)
    backup_frequency = models.CharField(max_length=10, choices=BACKUP_FREQUENCY_CHOICES, default='daily')
    system_logs = models.BooleanField(default=True)
    debug_mode = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f"System Settings ({self.updated_at.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        # Ensure only one settings instance exists
        if not self.pk and SystemSettings.objects.exists():
            # Update the existing instance instead of creating new one
            existing = SystemSettings.objects.first()
            existing.network_name = self.network_name
            existing.max_devices_per_user = self.max_devices_per_user
            # ... copy all other fields
            return existing.save(*args, **kwargs)
        return super().save(*args, **kwargs)


class SettingsHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    settings = models.ForeignKey(SystemSettings, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    changes = models.JSONField()  # Store changed fields and values
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'settings_history'
        ordering = ['-timestamp']
        verbose_name = 'Settings History'
        verbose_name_plural = 'Settings History'

    def __str__(self):
        return f"Settings change by {self.changed_by.email} at {self.timestamp}"


class AccessCode(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    network = models.ForeignKey('networks.Network', on_delete=models.CASCADE, related_name='access_codes')
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
