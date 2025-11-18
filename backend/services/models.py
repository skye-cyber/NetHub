from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator

class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, help_text="Heroicon name or emoji")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_categories'
        verbose_name_plural = 'Service Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

class ServiceType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='service_types')
    icon = models.CharField(max_length=50, help_text="Heroicon name or emoji")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'service_types'
        unique_together = ['name', 'category']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class ServiceProvider(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    VERIFICATION_CHOICES = [
        ('unverified', 'Unverified'),
        ('verified', 'Verified'),
        ('premium', 'Premium Partner'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='service_provider')
    business_name = models.CharField(max_length=200)
    business_description = models.TextField()
    logo = models.ImageField(upload_to='service_providers/logos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='service_providers/covers/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='unverified')
    is_featured = models.BooleanField(default=False)
    featured_until = models.DateTimeField(blank=True, null=True)

    # Contact Information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)

    # Location
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # Business Details
    business_hours = models.JSONField(default=dict, help_text="JSON structure for business hours")
    price_range = models.CharField(max_length=10, choices=[('$', '$'), ('$$', '$$'), ('$$$', '$$$'), ('$$$$', '$$$$')], default='$$')

    # Statistics
    total_views = models.PositiveIntegerField(default=0)
    total_clicks = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_providers'
        ordering = ['-created_at']

    def __str__(self):
        return self.business_name

    @property
    def average_rating(self):
        ratings = self.services.aggregate(avg_rating=models.Avg('rating'))
        return ratings['avg_rating'] or 0

    @property
    def total_reviews(self):
        return self.services.aggregate(total=models.Sum('review_count'))['total'] or 0

class Service(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='services')

    # Basic Information
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300)
    image = models.CharField(max_length=50, help_text="Emoji or icon representation")

    # Details
    tags = models.JSONField(default=list, help_text="List of tags as strings")
    wait_time = models.CharField(max_length=50, blank=True, null=True)
    distance = models.CharField(max_length=50, blank=True, null=True, help_text="Display distance from user")
    is_online = models.BooleanField(default=False, help_text="Service is available online")

    # Ratings and Reviews
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0,
                                validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_count = models.PositiveIntegerField(default=0)

    # Status and Features
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    featured_until = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Metadata
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'services'
        ordering = ['-is_featured', '-rating', '-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['category', 'service_type']),
            models.Index(fields=['rating', 'review_count']),
        ]

    def __str__(self):
        return f"{self.name} - {self.provider.business_name}"

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_available(self):
        return self.status == 'published' and self.is_active

class ServiceImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='services/images/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'service_images'
        ordering = ['display_order', 'created_at']

    def __str__(self):
        return f"Image for {self.service.name}"

class ServiceReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_reviews'
        unique_together = ['service', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating} stars for {self.service.name} by {self.user.email}"

class UserFavorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_favorites'
        unique_together = ['user', 'service']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} favorites {self.service.name}"

class Advertisement(models.Model):
    TYPE_CHOICES = [
        ('banner', 'Banner Ad'),
        ('featured', 'Featured Placement'),
        ('sponsored', 'Sponsored Content'),
        ('promotion', 'Special Promotion'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    ad_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='banner')
    image = models.ImageField(upload_to='advertisements/')
    target_url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Targeting
    categories = models.ManyToManyField(ServiceCategory, blank=True, related_name='advertisements')
    is_global = models.BooleanField(default=True)

    # Campaign Details
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_clicks = models.PositiveIntegerField(default=0)
    max_impressions = models.PositiveIntegerField(default=0)

    # Statistics
    total_clicks = models.PositiveIntegerField(default=0)
    total_impressions = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'advertisements'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        return (self.status == 'active' and
                self.start_date <= now <= self.end_date and
                (self.max_clicks == 0 or self.total_clicks < self.max_clicks) and
                (self.max_impressions == 0 or self.total_impressions < self.max_impressions))

class SearchHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=255)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} searched: {self.query}"
