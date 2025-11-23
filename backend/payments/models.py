import uuid
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models


class Subscription(models.Model):
    class Plans(models.TextChoices):
        MINS = "minutes", "minutes_subscription"
        HOURLY = "hourly", "Hourly subscription"
        DAILY = "daily", "Daily Subscription"
        WEEKLY = "weekly", "Weekly Subscription"
        MONTHLY = "montly", "Monthly subscription"

    host = models.ForeignKey('devices.Device', on_delete=models.CASCADE, related_name='subscribed_device')
    plan = models.CharField(max_length=30, choices=Plans.choices, default=None)
    start_time = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(null=True)
    elapsed_time = models.DurationField(null=True)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plan.title()} plan"


class PricingPlan(models.Model):
    DURATION_CHOICES = [
        ('30min', '30 Minutes'),
        ('1hour', '1 Hour'),
        ('4hours', '4 Hours'),
        ('1day', '24 Hours'),
        ('1week', '1 Week'),
        ('1month', '1 Month'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    original_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list, help_text="List of features as strings")
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pricing_plans'
        ordering = ['display_order', 'duration_minutes']

    def __str__(self):
        return f"{self.name} - KES {self.price}"

    @property
    def savings_percentage(self):
        if self.original_price and self.original_price > self.price:
            savings = ((self.original_price - self.price) / self.original_price) * 100
            return round(savings)
        return 0


class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(PricingPlan, on_delete=models.CASCADE, related_name='transactions')

    # Payment Details
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')

    # M-Pesa Specific Fields
    mpesa_phone = models.CharField(max_length=15, blank=True, null=True)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True)
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    mpesa_merchant_request_id = models.CharField(max_length=100, blank=True, null=True)

    # Card Specific Fields
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=50, blank=True, null=True)

    # Queue and Processing
    queue_position = models.IntegerField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)

    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="When this payment request expires")

    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['mpesa_transaction_id']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} - KES {self.amount}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def access_duration(self):
        return self.plan.duration_minutes


class InternetAccess(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='internet_access')
    payment = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='access')
    plan = models.ForeignKey(PricingPlan, on_delete=models.CASCADE, related_name='active_access')

    # Access Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    bandwidth_limit = models.PositiveIntegerField(help_text="Bandwidth in Mbps", default=10)

    # Usage Tracking
    data_used = models.BigIntegerField(default=0, help_text="Data used in bytes")
    devices_connected = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'internet_access'
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        return self.status == 'active' and timezone.now() < self.end_time

    @property
    def remaining_time(self):
        if self.is_active:
            remaining = self.end_time - timezone.now()
            return max(0, remaining.total_seconds() // 60)  # Return minutes
        return 0


class MpesaCallback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name='callbacks')
    callback_data = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'mpesa_callbacks'
        ordering = ['-received_at']

    def __str__(self):
        return f"Callback for {self.transaction}"


class PaymentQueue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='queue_entry')
    position = models.PositiveIntegerField()
    estimated_wait_time = models.PositiveIntegerField(help_text="Estimated wait time in seconds")
    entered_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payment_queue'
        ordering = ['position']

    def __str__(self):
        return f"Queue #{self.position} - {self.transaction}"
