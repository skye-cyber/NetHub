# portal/models.py
from django.db import models


class Device(models.Model):
    mac_address = models.CharField(max_length=17, unique=True)
    ip_address = models.GenericIPAddressField()
    is_authenticated = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.mac_address} ({self.ip_address})"
