from django.db import models


class Subscription(models.Model):
    class Plans(models.TextChoices):
        MINS = "minutes", "minutes_subscription"
        HOURLY = "hourly", "Hourly subscription"
        DAILY = "daily", "Daily Subscription"
        WEEKLY = "weekly", "Weekly Subscription"
        MONTHLY = "montly", "Monthly subscription"

    host = models.ForeignKey('portal.Device', on_delete=models.CASCADE, related_name='subscribed_device')
    plan = models.CharField(max_length=30, choices=Plans.choices, default=None)
    start_time = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(null=True)
    elapsed_time = models.DurationField(null=True)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plan.title()} plan"
