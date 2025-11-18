from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'role', 'status', 'last_login', 'created_at']
    list_filter = ['role', 'status', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'department']
    readonly_fields = ['created_at', 'last_login']
    filter_horizontal = ['networks']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(User):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active']

    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else 'No Profile'
    get_role.short_description = 'Role'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User)
