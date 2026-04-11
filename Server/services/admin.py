from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    ServiceCategory,
    ServiceType,
    ServiceProvider,
    Service,
    ServiceImage,
    SearchHistory,
    UserFavorite,
    Advertisement,
    ServiceReview,
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'display_order', 'is_active', 'service_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ['name']}
    readonly_fields = ['created_at', 'updated_at']

    def service_count(self, obj):
        return obj.services.count()
    service_count.short_description = 'Services'


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'icon', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'category__name']
    readonly_fields = ['created_at']


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user_email', 'status', 'verification_status', 'is_featured', 'average_rating', 'created_at']
    list_filter = ['status', 'verification_status', 'is_featured', 'created_at']
    search_fields = ['business_name', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'total_views', 'total_clicks', 'average_rating_display']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'business_name', 'business_description', 'logo', 'cover_image')
        }),
        ('Status', {
            'fields': ('status', 'verification_status', 'is_featured', 'featured_until')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Business Details', {
            'fields': ('business_hours', 'price_range')
        }),
        ('Statistics', {
            'fields': ('total_views', 'total_clicks', 'average_rating_display'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def average_rating_display(self, obj):
        return f"{obj.average_rating:.1f}/5.0"
    average_rating_display.short_description = 'Average Rating'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'category', 'service_type', 'rating', 'review_count', 'is_featured', 'status', 'created_at']
    list_filter = ['category', 'service_type', 'status', 'is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'provider__business_name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'view_count', 'click_count', 'favorite_count']
    prepopulated_fields = {'slug': ['name']}
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'category', 'service_type', 'name', 'slug')
        }),
        ('Description', {
            'fields': ('description', 'short_description', 'image', 'tags')
        }),
        ('Details', {
            'fields': ('wait_time', 'distance', 'is_online')
        }),
        ('Ratings', {
            'fields': ('rating', 'review_count')
        }),
        ('Status', {
            'fields': ('status', 'is_featured', 'featured_until', 'is_active')
        }),
        ('Statistics', {
            'fields': ('view_count', 'click_count', 'favorite_count', 'published_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('provider', 'category', 'service_type')


@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ['service', 'image_preview', 'caption', 'display_order', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['service__name', 'caption']
    readonly_fields = ['created_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'


@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ['service', 'user', 'rating', 'title', 'is_verified', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_verified', 'is_approved', 'created_at']
    search_fields = ['service__name', 'user__email', 'title']
    readonly_fields = ['created_at', 'updated_at', 'helpful_count']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('service', 'user')


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'service__name']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'service')


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['title', 'ad_type', 'status', 'is_active', 'start_date', 'end_date', 'total_clicks', 'total_impressions', 'created_at']
    list_filter = ['ad_type', 'status', 'is_global', 'start_date', 'end_date', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'total_clicks', 'total_impressions', 'total_spent', 'is_active_display']
    filter_horizontal = ['categories']

    def is_active_display(self, obj):
        return obj.is_active
    is_active_display.boolean = True
    is_active_display.short_description = 'Is Active'


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'query', 'category', 'results_count', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['user__email', 'query']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category')

# Extend User Admin


class ServiceProviderInline(admin.StackedInline):
    model = ServiceProvider
    can_delete = False
    verbose_name_plural = 'Service Provider Profile'


class CustomUserAdmin(UserAdmin):
    inlines = [ServiceProviderInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'service_provider_status']

    def service_provider_status(self, obj):
        if hasattr(obj, 'service_provider'):
            return obj.service_provider.status
        return 'Not a Provider'
    service_provider_status.short_description = 'Provider Status'


# Re-register UserAdmin
try:
    admin.site.unregister(User)
except Exception:
    pass

admin.site.register(User, CustomUserAdmin)
