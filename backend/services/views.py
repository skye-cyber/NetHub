from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q, Count, Avg
from django.contrib.auth.decorators import login_required
import json
from .models import (
    ServiceCategory,
    ServiceProvider,
    Service,
    SearchHistory,
    UserFavorite,
    Advertisement,
    ServiceReview,
)


class BaseDiscoverView(View):
    """Base view for discover functionality"""

    def json_response(self, data, status=200):
        return JsonResponse(data, status=status)

    def error_response(self, message, status=400):
        return self.json_response({'error': message}, status=status)

    def parse_json_body(self, request):
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None


@method_decorator(csrf_exempt, name='dispatch')
class DiscoverServicesView(BaseDiscoverView):

    def get(self, request):
        """Get services with filtering and search"""
        try:
            # Get query parameters
            category_id = request.GET.get('category', 'all')
            search_query = request.GET.get('search', '')
            sort_by = request.GET.get('sort', 'featured')
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 12)), 50)

            # Base queryset
            services = Service.objects.filter(
                status='published',
                is_active=True
            ).select_related('provider', 'category', 'service_type')

            # Apply filters
            if category_id != 'all':
                services = services.filter(category_id=category_id)

            if search_query:
                services = services.filter(
                    Q(name__icontains=search_query)
                    | Q(description__icontains=search_query)
                    | Q(short_description__icontains=search_query)
                    | Q(tags__icontains=search_query)
                    | Q(provider__business_name__icontains=search_query)
                )

            # Apply sorting
            if sort_by == 'rating':
                services = services.order_by('-rating', '-review_count')
            elif sort_by == 'newest':
                services = services.order_by('-created_at')
            elif sort_by == 'popular':
                services = services.order_by('-view_count', '-click_count')
            else:  # featured
                services = services.order_by('-is_featured', '-rating', '-created_at')

            # Pagination
            total_count = services.count()
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_services = services[start_idx:end_idx]

            # Build response data
            services_data = []
            for service in paginated_services:
                services_data.append({
                    'id': str(service.id),
                    'name': service.name,
                    'description': service.description,
                    'short_description': service.short_description,
                    'image': service.image,
                    'category': service.category.name,
                    'service_type': service.service_type.name,
                    'provider': {
                        'name': service.provider.business_name,
                        'verification_status': service.provider.verification_status
                    },
                    'rating': float(service.rating),
                    'review_count': service.review_count,
                    'price_range': service.provider.price_range,
                    'wait_time': service.wait_time,
                    'distance': service.distance,
                    'is_online': service.is_online,
                    'is_featured': service.is_featured,
                    'tags': service.tags,
                    'contact': service.provider.phone,
                    'website': service.provider.website,
                    'hours': service.provider.business_hours,
                    'view_count': service.view_count,
                    'favorite_count': service.favorite_count,
                    'created_at': service.created_at.isoformat()
                })

            # Get categories for filter
            categories = ServiceCategory.objects.filter(is_active=True)
            categories_data = [{'id': 'all', 'name': 'All Services', 'count': total_count}]
            for category in categories:
                count = services.filter(category=category).count() if category_id == 'all' else services.count()
                categories_data.append({
                    'id': str(category.id),
                    'name': category.name,
                    'icon': category.icon,
                    'count': count
                })

            # Log search if user is authenticated and there's a query
            if request.user.is_authenticated and search_query:
                SearchHistory.objects.create(
                    user=request.user,
                    query=search_query,
                    category_id=category_id if category_id != 'all' else None,
                    results_count=total_count
                )

            return self.json_response({
                'services': services_data,
                'categories': categories_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                },
                'filters': {
                    'category': category_id,
                    'search': search_query,
                    'sort': sort_by
                }
            })

        except Exception as e:
            return self.error_response(str(e), 500)


@method_decorator(csrf_exempt, name='dispatch')
class FeaturedServicesView(BaseDiscoverView):

    def get(self, request):
        """Get featured services"""
        try:
            featured_services = Service.objects.filter(
                status='published',
                is_active=True,
                is_featured=True
            ).select_related('provider', 'category', 'service_type')[:6]

            services_data = []
            for service in featured_services:
                services_data.append({
                    'id': str(service.id),
                    'name': service.name,
                    'description': service.description,
                    'image': service.image,
                    'category': service.category.name,
                    'provider': service.provider.business_name,
                    'rating': float(service.rating),
                    'review_count': service.review_count,
                    'price_range': service.provider.price_range,
                    'is_featured': service.is_featured
                })

            return self.json_response({'featured_services': services_data})

        except Exception as e:
            return self.error_response(str(e), 500)


@method_decorator(csrf_exempt, name='dispatch')
class ServiceDetailView(BaseDiscoverView):

    def get(self, request, service_id):
        """Get detailed service information"""
        try:
            service = Service.objects.select_related(
                'provider', 'category', 'service_type'
            ).prefetch_related('images', 'reviews').get(
                id=service_id,
                status='published',
                is_active=True
            )

            # Increment view count
            service.view_count += 1
            service.save(update_fields=['view_count'])

            # Get reviews
            reviews = service.reviews.filter(is_approved=True)[:5]
            reviews_data = []
            for review in reviews:
                reviews_data.append({
                    'user': review.user.email,
                    'rating': review.rating,
                    'title': review.title,
                    'comment': review.comment,
                    'is_verified': review.is_verified,
                    'helpful_count': review.helpful_count,
                    'created_at': review.created_at.isoformat()
                })

            # Get images
            images_data = []
            for image in service.images.all():
                images_data.append({
                    'url': image.image.url,
                    'caption': image.caption,
                    'is_primary': image.is_primary
                })

            service_data = {
                'id': str(service.id),
                'name': service.name,
                'description': service.description,
                'short_description': service.short_description,
                'image': service.image,
                'category': {
                    'id': str(service.category.id),
                    'name': service.category.name,
                    'icon': service.category.icon
                },
                'service_type': {
                    'id': str(service.service_type.id),
                    'name': service.service_type.name
                },
                'provider': {
                    'name': service.provider.business_name,
                    'description': service.provider.business_description,
                    'verification_status': service.provider.verification_status,
                    'phone': service.provider.phone,
                    'email': service.provider.email,
                    'website': service.provider.website,
                    'address': service.provider.address,
                    'business_hours': service.provider.business_hours
                },
                'rating': float(service.rating),
                'review_count': service.review_count,
                'price_range': service.provider.price_range,
                'wait_time': service.wait_time,
                'distance': service.distance,
                'is_online': service.is_online,
                'is_featured': service.is_featured,
                'tags': service.tags,
                'images': images_data,
                'reviews': reviews_data,
                'view_count': service.view_count,
                'favorite_count': service.favorite_count,
                'created_at': service.created_at.isoformat()
            }

            # Check if user has favorited this service
            if request.user.is_authenticated:
                is_favorited = UserFavorite.objects.filter(
                    user=request.user, service=service
                ).exists()
                service_data['is_favorited'] = is_favorited

            return self.json_response({'service': service_data})

        except Service.DoesNotExist:
            return self.error_response('Service not found', 404)
        except Exception as e:
            return self.error_response(str(e), 500)


@method_decorator(csrf_exempt, name='dispatch')
class FavoriteServiceView(BaseDiscoverView):

    @method_decorator(login_required)
    def post(self, request, service_id):
        """Add service to favorites"""
        try:
            service = Service.objects.get(id=service_id, status='published', is_active=True)

            favorite, created = UserFavorite.objects.get_or_create(
                user=request.user,
                service=service
            )

            if created:
                service.favorite_count += 1
                service.save(update_fields=['favorite_count'])

            return self.json_response({
                'message': 'Service added to favorites',
                'is_favorited': True,
                'favorite_count': service.favorite_count
            })

        except Service.DoesNotExist:
            return self.error_response('Service not found', 404)
        except Exception as e:
            return self.error_response(str(e), 500)

    @method_decorator(login_required)
    def delete(self, request, service_id):
        """Remove service from favorites"""
        try:
            service = Service.objects.get(id=service_id)

            deleted_count = UserFavorite.objects.filter(
                user=request.user,
                service=service
            ).delete()[0]

            if deleted_count > 0:
                service.favorite_count = max(0, service.favorite_count - 1)
                service.save(update_fields=['favorite_count'])

            return self.json_response({
                'message': 'Service removed from favorites',
                'is_favorited': False,
                'favorite_count': service.favorite_count
            })

        except Service.DoesNotExist:
            return self.error_response('Service not found', 404)
        except Exception as e:
            return self.error_response(str(e), 500)


@method_decorator(csrf_exempt, name='dispatch')
class AdvertisementsView(BaseDiscoverView):

    def get(self, request):
        """Get active advertisements"""
        try:
            now = timezone.now()
            ads = Advertisement.objects.filter(
                status='active',
                start_date__lte=now,
                end_date__gte=now
            )

            ads_data = []
            for ad in ads:
                ads_data.append({
                    'id': str(ad.id),
                    'title': ad.title,
                    'description': ad.description,
                    'ad_type': ad.ad_type,
                    'image_url': ad.image.url if ad.image else None,
                    'target_url': ad.target_url,
                    'is_global': ad.is_global,
                    'categories': [str(cat.id) for cat in ad.categories.all()]
                })

                # Increment impressions
                ad.total_impressions += 1
                ad.save(update_fields=['total_impressions'])

            return self.json_response({'advertisements': ads_data})

        except Exception as e:
            return self.error_response(str(e), 500)


class ServiceStatisticsView(BaseDiscoverView):

    def get(self, request):
        """Get service statistics for dashboard"""
        try:
            total_services = Service.objects.filter(status='published', is_active=True).count()
            total_providers = ServiceProvider.objects.filter(status='approved').count()
            total_categories = ServiceCategory.objects.filter(is_active=True).count()
            total_reviews = ServiceReview.objects.filter(is_approved=True).count()

            # Top categories
            top_categories = ServiceCategory.objects.filter(
                is_active=True
            ).annotate(
                service_count=Count('services')
            ).order_by('-service_count')[:5]

            categories_data = []
            for category in top_categories:
                categories_data.append({
                    'name': category.name,
                    'service_count': category.service_count
                })

            # Recent activity
            recent_services = Service.objects.filter(
                status='published'
            ).order_by('-created_at')[:5]

            recent_services_data = []
            for service in recent_services:
                recent_services_data.append({
                    'name': service.name,
                    'provider': service.provider.business_name,
                    'created_at': service.created_at.isoformat()
                })

            return self.json_response({
                'statistics': {
                    'total_services': total_services,
                    'total_providers': total_providers,
                    'total_categories': total_categories,
                    'total_reviews': total_reviews
                },
                'top_categories': categories_data,
                'recent_activity': recent_services_data
            })

        except Exception as e:
            return self.error_response(str(e), 500)
