from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth import get_user_model

_User = get_user_model()


class CustomUser(User):
    """
    Custom user model extending Django's AbstractUser.
    """

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    def _serialize_custom_user(self, instance):
        """Optimized custom user serialization"""
        return {
            "user_id": str(instance.id),
            "username": instance.username,
            "email": instance.email,
            "is_online": instance.is_online,
            "last_seen": instance.last_seen.isoformat() if instance.last_seen else None,
            "avatar": str(instance.avatar) if instance.avatar else None,
            "bio": instance.bio or "",
        }


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('administrator', 'Administrator'),
        ('technician', 'Technician'),
        ('viewer', 'Viewer'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    networks = models.ManyToManyField('networks.Network', related_name='authorized_users', blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.user.email} ({self.role})"
