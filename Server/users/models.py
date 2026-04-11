from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class NetHubUser(AbstractUser):
    """
    Custom user model combining both user and profile information.
    Extends Django's AbstractUser for authentication functionality.
    """

    # Basic user fields (from CustomUser)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)

    # User preferences
    color_scheme = models.CharField(
        max_length=20,
        default="blue",
        choices=[
            ("blue", "Blue"),
            ("green", "Green"),
            ("purple", "Purple"),
            ("red", "Red"),
            ("yellow", "Yellow"),
            ("indigo", "Indigo"),
            ("pink", "Pink"),
        ],
    )

    # Profile fields (from UserProfile)
    role = models.CharField(
        max_length=20,
        choices=[
            ('administrator', 'Administrator'),
            ('technician', 'Technician'),
            ('viewer', 'Viewer'),
        ],
        default='viewer'
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('suspended', 'Suspended'),
        ],
        default='active'
    )

    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    networks = models.ManyToManyField('networks.Network', related_name='authorized_users', blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username

    @property
    def online(self):
        return self.is_active

    @property
    def color(self):
        """Get user's color for UI elements"""
        return self.color_scheme

    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = timezone.now()
        self.save()

    @property
    def is_privileged(self):
        return self.is_staff

    @property
    def is_admin(self):
        return self.is_superuser

    def _serialize_custom_user(self):
        """Optimized custom user serialization"""
        return {
            "user_id": str(self.id),
            "username": self.username,
            "email": self.email,
            "is_online": self.is_online,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "avatar": str(self.avatar) if self.avatar else None,
            "bio": self.bio or "",
            "role": self.role,
            "status": self.status,
            "phone": self.phone,
            "department": self.department,
            "networks": list(self.networks.values_list('id', flat=True)),
        }
