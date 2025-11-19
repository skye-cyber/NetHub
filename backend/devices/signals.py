'''
Signal handler for devices eg creation/deletion updates arp tables
'''
import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Device

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Device())
def register_device_profile(sender, instance, created, **kwargs):
    """Automatically create user profile when a new user is created"""
    if created:
        '''
        #
        '''


@receiver(pre_delete, sender=Device())
def delete_devices_profile(sender, instance, **kwargs):
    """Automatically create user profile when a new user is created"""
    mac = instance.mac_address
    '''
    Block the device...
    '''
