import React, { useState, useEffect } from 'react';
import {
    MagnifyingGlassIcon,
    MapPinIcon,
    ClockIcon,
    StarIcon,
    HeartIcon,
    ShareIcon,
    PhoneIcon,
    GlobeAltIcon,
    ShoppingBagIcon,
    FilmIcon,
    MusicalNoteIcon,
    BookOpenIcon,
    TruckIcon,
    BuildingStorefrontIcon,
    WifiIcon
} from '@heroicons/react/24/outline';
import {
    StarIcon as StarIconSolid,
    HeartIcon as HeartIconSolid
} from '@heroicons/react/24/solid';

const DiscoverPage = () => {
    const [activeCategory, setActiveCategory] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [favorites, setFavorites] = useState(new Set());
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDiscoverContent();
    }, []);

    const loadDiscoverContent = async () => {
        try {
            // Simulate API call
            setTimeout(() => {
                setServices([
                    {
                        id: 1,
                        name: "Tech Hub Cafe",
                        category: "food",
                        type: "cafe",
                        description: "Premium coffee and high-speed internet workspace",
                        rating: 4.7,
                        reviews: 128,
                        distance: "0.2 km",
                        waitTime: "5-10 min",
                        priceRange: "$$",
                        image: "🍵",
                        tags: ["WiFi", "Workspace", "Coffee", "Snacks"],
                        contact: "+1 555-0123",
                        website: "techhubcafe.com",
                        hours: "7:00 AM - 10:00 PM",
                        featured: true,
                        coordinates: { lat: 40.7128, lng: -74.0060 }
                    },
                    {
                        id: 2,
                        name: "Digital Print Studio",
                        category: "services",
                        type: "printing",
                        description: "High-quality printing and digital services",
                        rating: 4.5,
                        reviews: 64,
                        distance: "0.5 km",
                        waitTime: "15-30 min",
                        priceRange: "$$$",
                        image: "🖨️",
                        tags: ["Printing", "Scanning", "Design", "Copy"],
                        contact: "+1 555-0124",
                        website: "printstudio.com",
                        hours: "9:00 AM - 6:00 PM",
                        featured: false,
                        coordinates: { lat: 40.7138, lng: -74.0070 }
                    },
                    {
                        id: 3,
                        name: "Netflix Streaming",
                        category: "entertainment",
                        type: "streaming",
                        description: "Unlimited movies and TV shows",
                        rating: 4.8,
                        reviews: 2500,
                        distance: "Online",
                        waitTime: "Instant",
                        priceRange: "$$",
                        image: "🎬",
                        tags: ["Movies", "TV Shows", "4K", "Family"],
                        contact: "support@netflix.com",
                        website: "netflix.com",
                        hours: "24/7",
                        featured: true,
                        coordinates: null
                    },
                    {
                        id: 4,
                        name: "Urban Eats Delivery",
                        category: "food",
                        type: "delivery",
                        description: "Fast food delivery from local restaurants",
                        rating: 4.3,
                        reviews: 892,
                        distance: "Delivery",
                        waitTime: "25-40 min",
                        priceRange: "$$",
                        image: "🚚",
                        tags: ["Delivery", "Fast Food", "Multiple Cuisines"],
                        contact: "+1 555-0125",
                        website: "urbaneats.com",
                        hours: "10:00 AM - 11:00 PM",
                        featured: false,
                        coordinates: null
                    },
                    {
                        id: 5,
                        name: "Spotify Music",
                        category: "entertainment",
                        type: "music",
                        description: "70+ million songs and podcasts",
                        rating: 4.6,
                        reviews: 1800,
                        distance: "Online",
                        waitTime: "Instant",
                        priceRange: "$$",
                        image: "🎵",
                        tags: ["Music", "Podcasts", "Offline", "Curated"],
                        contact: "support@spotify.com",
                        website: "spotify.com",
                        hours: "24/7",
                        featured: true,
                        coordinates: null
                    },
                    {
                        id: 6,
                        name: "Quick Mart",
                        category: "shopping",
                        type: "convenience",
                        description: "24/7 convenience store with essentials",
                        rating: 4.2,
                        reviews: 312,
                        distance: "0.3 km",
                        waitTime: "Quick",
                        priceRange: "$",
                        image: "🏪",
                        tags: ["24/7", "Groceries", "Snacks", "Essentials"],
                        contact: "+1 555-0126",
                        website: "quickmart.com",
                        hours: "24/7",
                        featured: false,
                        coordinates: { lat: 40.7118, lng: -74.0050 }
                    }
                ]);
                setLoading(false);
            }, 1000);
        } catch (error) {
            console.error('Error loading discover content:', error);
            setLoading(false);
        }
    };

    const categories = [
        { id: 'all', name: 'All Services', icon: GlobeAltIcon, count: services.length },
        { id: 'food', name: 'Food & Drink', icon: ShoppingBagIcon, count: services.filter(s => s.category === 'food').length },
        { id: 'services', name: 'Services', icon: WifiIcon, count: services.filter(s => s.category === 'services').length },
        { id: 'entertainment', name: 'Entertainment', icon: FilmIcon, count: services.filter(s => s.category === 'entertainment').length },
        { id: 'shopping', name: 'Shopping', icon: BuildingStorefrontIcon, count: services.filter(s => s.category === 'shopping').length }
    ];

    const toggleFavorite = (serviceId) => {
        setFavorites(prev => {
            const newFavorites = new Set(prev);
            if (newFavorites.has(serviceId)) {
                newFavorites.delete(serviceId);
            } else {
                newFavorites.add(serviceId);
            }
            return newFavorites;
        });
    };

    const filteredServices = services.filter(service => {
        const matchesCategory = activeCategory === 'all' || service.category === activeCategory;
        const matchesSearch = service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            service.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
            service.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
        return matchesCategory && matchesSearch;
    });

    const ServiceCard = ({ service }) => {
        const isFavorite = favorites.has(service.id);
        const FavoriteIcon = isFavorite ? HeartIconSolid : HeartIcon;

        return (
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 border border-white/20 dark:border-gray-700/50 overflow-hidden group">
                {/* Header with Image and Favorite */}
                <div className="relative h-40 bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                    <span className="text-4xl">{service.image}</span>
                    {service.featured && (
                        <div className="absolute top-3 left-3 bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-2 py-1 rounded-full text-xs font-semibold">
                            Featured
                        </div>
                    )}
                    <button
                        onClick={() => toggleFavorite(service.id)}
                        className="absolute top-3 right-3 p-2 bg-white/90 dark:bg-gray-800/90 rounded-full shadow-md hover:scale-110 transition-transform"
                    >
                        <FavoriteIcon className={`w-5 h-5 ${isFavorite ? 'text-red-500' : 'text-gray-400'}`} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4">
                    <div className="flex items-start justify-between mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                            {service.name}
                        </h3>
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                            {service.priceRange}
                        </span>
                    </div>

                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-2">
                        {service.description}
                    </p>

                    {/* Rating and Distance */}
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-1">
                            <StarIconSolid className="w-4 h-4 text-yellow-400" />
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {service.rating}
                            </span>
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                                ({service.reviews})
                            </span>
                        </div>
                        <div className="flex items-center space-x-1 text-sm text-gray-500 dark:text-gray-400">
                            <MapPinIcon className="w-4 h-4" />
                            <span>{service.distance}</span>
                        </div>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1 mb-3">
                        {service.tags.slice(0, 3).map((tag, index) => (
                            <span
                                key={index}
                                className="inline-block bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400 px-2 py-1 rounded-full text-xs"
                            >
                                {tag}
                            </span>
                        ))}
                        {service.tags.length > 3 && (
                            <span className="inline-block bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-1 rounded-full text-xs">
                                +{service.tags.length - 3}
                            </span>
                        )}
                    </div>

                    {/* Wait Time and Hours */}
                    <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-3">
                        <div className="flex items-center space-x-1">
                            <ClockIcon className="w-4 h-4" />
                            <span>{service.waitTime}</span>
                        </div>
                        <span>{service.hours}</span>
                    </div>

                    {/* Actions */}
                    <div className="flex space-x-2">
                        <button className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-2 rounded-lg text-sm font-medium hover:from-blue-700 hover:to-cyan-700 transition-all duration-300 shadow-md hover:shadow-lg">
                            View Details
                        </button>
                        <button className="p-2 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                            <ShareIcon className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>
        );
    };

    const FeaturedSection = () => {
        const featuredServices = services.filter(service => service.featured);

        return (
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Featured Services</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {featuredServices.map(service => (
                        <ServiceCard key={service.id} service={service} />
                    ))}
                </div>
            </div>
        );
    };

    const CategoryFilter = () => {
        const CategoryIcon = categories.find(cat => cat.id === activeCategory)?.icon;

        return (
            <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center space-x-2">
                        {CategoryIcon && <CategoryIcon className="w-6 h-6 text-blue-500" />}
                        <span>Discover Services</span>
                    </h2>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                        {filteredServices.length} services found
                    </div>
                </div>

                {/* Search Bar */}
                <div className="relative mb-4">
                    <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search services, tags, or descriptions..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300"
                    />
                </div>

                {/* Category Tabs */}
                <div className="flex space-x-2 overflow-x-auto pb-2">
                    {categories.map(category => {
                        const Icon = category.icon;
                        return (
                            <button
                                key={category.id}
                                onClick={() => setActiveCategory(category.id)}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-xl whitespace-nowrap transition-all duration-300 ${activeCategory === category.id
                                        ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg'
                                        : 'bg-white/80 dark:bg-gray-800/80 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                                    }`}
                            >
                                <Icon className="w-4 h-4" />
                                <span>{category.name}</span>
                                <span className={`text-xs px-1.5 py-0.5 rounded-full ${activeCategory === category.id
                                        ? 'bg-white/20 text-white'
                                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                                    }`}>
                                    {category.count}
                                </span>
                            </button>
                        );
                    })}
                </div>
            </div>
        );
    };

    const AdvertSection = () => (
        <div className="mb-8">
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-6 text-white shadow-lg">
                <div className="flex flex-col md:flex-row items-center justify-between">
                    <div className="flex-1 mb-4 md:mb-0">
                        <h3 className="text-xl font-bold mb-2">Premium Network Access</h3>
                        <p className="text-purple-100 mb-4">
                            Get faster speeds and priority access. Upgrade now for uninterrupted streaming and browsing.
                        </p>
                        <button className="bg-white text-purple-600 px-6 py-2 rounded-lg font-semibold hover:bg-purple-50 transition-colors">
                            Upgrade Now
                        </button>
                    </div>
                    <div className="text-6xl">🚀</div>
                </div>
            </div>
        </div>
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-gray-900 dark:via-purple-900/20 dark:to-blue-900/20 p-4">
                <div className="max-w-7xl mx-auto">
                    <div className="flex justify-center items-center py-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-gray-900 dark:via-purple-900/20 dark:to-blue-900/20 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                        Discover Services
                    </h1>
                    <p className="text-gray-600 dark:text-gray-300 text-lg">
                        Explore local services, entertainment, and exclusive offers available on our network
                    </p>
                </div>

                {/* Featured Section */}
                <FeaturedSection />

                {/* Advertisement */}
                <AdvertSection />

                {/* Category Filter and Search */}
                <CategoryFilter />

                {/* Services Grid */}
                {filteredServices.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {filteredServices.map(service => (
                            <ServiceCard key={service.id} service={service} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12">
                        <div className="text-6xl mb-4">🔍</div>
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                            No services found
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400">
                            Try adjusting your search or filter criteria
                        </p>
                    </div>
                )}

                {/* Bottom CTA */}
                <div className="mt-12 text-center">
                    <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-8 border border-white/20 dark:border-gray-700/50">
                        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                            Have a service to list?
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400 mb-4">
                            Join our network and reach thousands of potential customers
                        </p>
                        <button className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all duration-300 shadow-lg hover:shadow-xl">
                            List Your Service
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DiscoverPage;
