from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import NetHubUser


@admin.register(NetHubUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "is_online",
        "last_seen",
        "is_staff",
        "role",
        "status"
    )
    list_filter = (
        "is_online",
        "is_staff",
        "is_superuser",
        "created_at",
        "role",
        "status"
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
        "department"
    )
    readonly_fields = (
        "last_seen",
        "created_at",
        "updated_at",
        "last_login"
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'avatar',
                'bio',
                'phone',
                'department'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_online',
                'role',
                'status',
                'groups',
                'user_permissions'
            )
        }),
        ('Important dates', {
            'fields': (
                'last_login',
                'last_seen',
                'created_at',
                'updated_at'
            )
        }),
        ('Preferences', {
            'fields': ('color_scheme',)
        }),
        ('Networks', {
            'fields': ('networks',),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ('networks', 'groups', 'user_permissions')

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile_user')

    def get_inline_instances(self, request, obj=None):
        if obj:
            return list(super().get_inline_instances(request, obj))
        return []
