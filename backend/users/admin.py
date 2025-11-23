from django.contrib import admin
from .models import CustomUser, UserProfile
from django.contrib.auth.admin import UserAdmin


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_online", "last_seen", "is_staff")
    list_filter = ("is_online", "is_staff", "is_superuser", "created_at")
    search_fields = ("username", "email", "first_name", "last_name")
    readonly_fields = ("last_seen", "created_at", "updated_at")

    fieldsets = UserAdmin.fieldsets + (
        (
            "User Features",
            {
                "fields": (
                    "is_online",
                    "last_seen",
                    "avatar",
                    "bio",
                    "color_scheme",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else 'No Profile'
    get_role.short_description = 'Role'


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
