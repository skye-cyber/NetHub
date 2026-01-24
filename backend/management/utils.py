import random
from users.models import NetHubUser
from django.db.models import Q


def get_random_user():
    """
    Get a random user with admin privileges.
    Returns a NetHubUser instance or None if no matching users are found.
    """
    # First try to get a random admin user directly
    admin_users = NetHubUser.objects.filter(
        Q(role='administrator')
        | Q(is_superuser=True, is_staff=True)
    )

    if admin_users.exists():
        return random.choice(admin_users)

    # If no admin users found, return a random user
    all_users = NetHubUser.objects.all()
    if all_users.exists():
        return random.choice(all_users)

    return None
