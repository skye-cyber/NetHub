from django.urls import path
from . import views

urlpatterns = [
    # Service discovery
    path('api/discover/services/', views.DiscoverServicesView.as_view(), name='discover_services'),
    path('api/discover/services/featured/', views.FeaturedServicesView.as_view(), name='featured_services'),
    path('api/discover/services/<uuid:service_id>/', views.ServiceDetailView.as_view(), name='service_detail'),

    # Favorites
    path('api/discover/services/<uuid:service_id>/favorite/', views.FavoriteServiceView.as_view(), name='favorite_service'),

    # Advertisements
    path('api/discover/advertisements/', views.AdvertisementsView.as_view(), name='advertisements'),

    # Statistics
    path('api/discover/statistics/', views.ServiceStatisticsView.as_view(), name='service_statistics'),
]
