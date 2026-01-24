# import threading
import logging
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from users.models import UserProfile

logger = logging.getLogger(__name__)

# Thread-local storage for tracking sync origins
# _sync_origin_local = threading.local()


@receiver(post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create user profile when a new user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=get_user_model())
def save_user_profile(sender, instance, **kwargs):
    """Automatically save user profile when user is saved"""
    if hasattr(instance, "profile"):
        instance.profile.save()

