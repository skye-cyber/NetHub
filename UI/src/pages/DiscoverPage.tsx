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
    WifiIcon,
} from '@heroicons/react/24/outline';
import {
    StarIcon as StarIconSolid,
    HeartIcon as HeartIconSolid,
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
            setTimeout(() => {
                setServices([
                    {
                        id: 1,
                        name: 'Tech Hub Cafe',
                        category: 'food',
                        type: 'cafe',
                        description: 'Premium coffee and high-speed internet workspace',
                        rating: 4.7,
                        reviews: 128,
                        distance: '0.2 km',
                        waitTime: '5-10 min',
                        priceRange: '$$',
                        image: '🍵',
                        tags: ['WiFi', 'Workspace', 'Coffee', 'Snacks'],
                        contact: '+1 555-0123',
                        website: 'techhubcafe.com',
                        hours: '7:00 AM - 10:00 PM',
                        featured: true,
                        coordinates: { lat: 40.7128, lng: -74.0060 },
                    },
                    {
                        id: 2,
                        name: 'Digital Print Studio',
                        category: 'services',
                        type: 'printing',
                        description: 'High-quality printing and digital services',
                        rating: 4.5,
                        reviews: 64,
                        distance: '0.5 km',
                        waitTime: '15-30 min',
                        priceRange: '$$$',
                        image: '🖨️',
                        tags: ['Printing', 'Scanning', 'Design', 'Copy'],
                        contact: '+1 555-0124',
                        website: 'printstudio.com',
                        hours: '9:00 AM - 6:00 PM',
                        featured: false,
                        coordinates: { lat: 40.7138, lng: -74.0070 },
                    },
                    {
                        id: 3,
                        name: 'Netflix Streaming',
                        category: 'entertainment',
                        type: 'streaming',
                        description: 'Unlimited movies and TV shows',
                        rating: 4.8,
                        reviews: 2500,
                        distance: 'Online',
                        waitTime: 'Instant',
                        priceRange: '$$',
                        image: '🎬',
                        tags: ['Movies', 'TV Shows', '4K', 'Family'],
                        contact: 'support@netflix.com',
                        website: 'netflix.com',
                        hours: '24/7',
                        featured: true,
                        coordinates: null,
                    },
                    {
                        id: 4,
                        name: 'Urban Eats Delivery',
                        category: 'food',
                        type: 'delivery',
                        description: 'Fast food delivery from local restaurants',
                        rating: 4.3,
                        reviews: 892,
                        distance: 'Delivery',
                        waitTime: '25-40 min',
                        priceRange: '$$',
                        image: '🚚',
                        tags: ['Delivery', 'Fast Food', 'Multiple Cuisines'],
                        contact: '+1 555-0125',
                        website: 'urbaneats.com',
                        hours: '10:00 AM - 11:00 PM',
                        featured: false,
                        coordinates: null,
                    },
                    {
                        id: 5,
                        name: 'Spotify Music',
                        category: 'entertainment',
                        type: 'music',
                        description: '70+ million songs and podcasts',
                        rating: 4.6,
                        reviews: 1800,
                        distance: 'Online',
                        waitTime: 'Instant',
                        priceRange: '$$',
                        image: '🎵',
                        tags: ['Music', 'Podcasts', 'Offline', 'Curated'],
                        contact: 'support@spotify.com',
                        website: 'spotify.com',
                        hours: '24/7',
                        featured: true,
                        coordinates: null,
                    },
                    {
                        id: 6,
                        name: 'Quick Mart',
                        category: 'shopping',
                        type: 'convenience',
                        description: '24/7 convenience store with essentials',
                        rating: 4.2,
                        reviews: 312,
                        distance: '0.3 km',
                        waitTime: 'Quick',
                        priceRange: '$',
                        image: '🏪',
                        tags: ['24/7', 'Groceries', 'Snacks', 'Essentials'],
                        contact: '+1 555-0126',
                        website: 'quickmart.com',
                        hours: '24/7',
                        featured: false,
                        coordinates: { lat: 40.7118, lng: -74.0050 },
                    },
                ]);
                setLoading(false);
            }, 800);
        } catch (error) {
            console.error('Error loading discover content:', error);
            setLoading(false);
        }
    };

    const categories = [
        { id: 'all', name: 'All Services', icon: GlobeAltIcon, count: services.length },
        { id: 'food', name: 'Food & Drink', icon: ShoppingBagIcon, count: services.filter((s) => s.category === 'food').length },
        { id: 'services', name: 'Services', icon: WifiIcon, count: services.filter((s) => s.category === 'services').length },
        { id: 'entertainment', name: 'Entertainment', icon: FilmIcon, count: services.filter((s) => s.category === 'entertainment').length },
        { id: 'shopping', name: 'Shopping', icon: BuildingStorefrontIcon, count: services.filter((s) => s.category === 'shopping').length },
    ];

    const toggleFavorite = (serviceId) => {
        setFavorites((prev) => {
            const newFavorites = new Set(prev);
            newFavorites.has(serviceId) ? newFavorites.delete(serviceId) : newFavorites.add(serviceId);
            return newFavorites;
        });
    };

    const filteredServices = services.filter((service) => {
        const matchesCategory = activeCategory === 'all' || service.category === activeCategory;
        const matchesSearch =
            service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            service.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
            service.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()));
        return matchesCategory && matchesSearch;
    });

    const ServiceCard = ({ service }) => {
        const isFavorite = favorites.has(service.id);
        const FavoriteIcon = isFavorite ? HeartIconSolid : HeartIcon;

        return (
            <div className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 shadow-md dark:shadow-lg hover:shadow-lg dark:hover:shadow-neo transition-all duration-300">
                {/* Image area */}
                <div className="relative h-36 bg-gradient-to-br from-neo-primary/10 to-neo-secondary/10 flex items-center justify-center">
                    <span className="text-4xl">{service.image}</span>
                    {service.featured && (
                        <div className="absolute top-3 left-3 bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 text-xs font-semibold px-2 py-0.5 rounded-full">
                            Featured
                        </div>
                    )}
                    <button
                        onClick={() => toggleFavorite(service.id)}
                        className="absolute top-3 right-3 p-2 bg-white/90 dark:bg-neo-dark/80 rounded-full shadow-md hover:scale-110 transition-transform"
                    >
                        <FavoriteIcon className={`w-4 h-4 ${isFavorite ? 'text-red-500' : 'text-gray-400 dark:text-neo-dim'}`} />
                    </button>
                </div>

                <div className="p-4">
                    <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-gray-900 dark:text-neo-text group-hover:text-neo-primary transition-colors">
                            {service.name}
                        </h3>
                        <span className="text-xs font-medium text-gray-500 dark:text-neo-dim bg-gray-100 dark:bg-primary-900/50 px-2 py-0.5 rounded">
                            {service.priceRange}
                        </span>
                    </div>

                    <p className="text-sm text-gray-500 dark:text-neo-dim mb-3 line-clamp-2">{service.description}</p>

                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-1">
                            <StarIconSolid className="w-3.5 h-3.5 text-yellow-400" />
                            <span className="text-sm font-medium text-gray-900 dark:text-neo-text">{service.rating}</span>
                            <span className="text-xs text-gray-500 dark:text-neo-dim">({service.reviews})</span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-neo-dim">
                            <MapPinIcon className="w-3.5 h-3.5" />
                            <span>{service.distance}</span>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-1 mb-3">
                        {service.tags.slice(0, 3).map((tag, idx) => (
                            <span
                                key={idx}
                                className="inline-block bg-neo-primary/10 text-neo-primary border border-neo-primary/20 px-2 py-0.5 rounded-full text-xs"
                            >
                                {tag}
                            </span>
                        ))}
                        {service.tags.length > 3 && (
                            <span className="inline-block bg-gray-100 dark:bg-primary-900/50 text-gray-500 dark:text-neo-dim px-2 py-0.5 rounded-full text-xs">
                                +{service.tags.length - 3}
                            </span>
                        )}
                    </div>

                    <div className="flex items-center justify-between text-xs text-gray-500 dark:text-neo-dim mb-3">
                        <div className="flex items-center gap-1">
                            <ClockIcon className="w-3.5 h-3.5" />
                            <span>{service.waitTime}</span>
                        </div>
                        <span>{service.hours}</span>
                    </div>

                    <div className="flex gap-2">
                        <button className="flex-1 py-2 rounded-lg bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 text-sm font-medium shadow-md hover:shadow-neo transition-all duration-300">
                            View Details
                        </button>
                        <button className="p-2 rounded-lg bg-gray-100 dark:bg-primary-900/50 text-gray-500 dark:text-neo-dim border border-gray-200 dark:border-neo-primary/20 hover:bg-gray-200 dark:hover:bg-primary-800/70 transition-colors">
                            <ShareIcon className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>
        );
    };

    const FeaturedSection = () => {
        const featuredServices = services.filter((s) => s.featured);
        if (featuredServices.length === 0) return null;

        return (
            <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-neo-text mb-4 flex items-center gap-2">
                    <span className="w-1 h-5 bg-gradient-to-b from-neo-primary to-neo-secondary rounded-full" />
                    Featured Services
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {featuredServices.map((service) => (
                        <ServiceCard key={service.id} service={service} />
                    ))}
                </div>
            </div>
        );
    };

    const CategoryFilter = () => (
        <div className="mb-6">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-neo-text flex items-center gap-2">
                    <span className="w-1 h-5 bg-gradient-to-b from-neo-primary to-neo-secondary rounded-full" />
                    Discover Services
                </h2>
                <span className="text-sm text-gray-500 dark:text-neo-dim">{filteredServices.length} services found</span>
            </div>

            {/* Search */}
            <div className="relative mb-4">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-neo-dim" />
                <input
                    type="text"
                    placeholder="Search services, tags, or descriptions..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 text-gray-900 dark:text-neo-text placeholder-gray-400 dark:placeholder-neo-dim/50 focus:border-neo-primary focus:ring-1 focus:ring-neo-primary/30 outline-none transition-colors"
                />
            </div>

            {/* Category tabs */}
            <div className="flex gap-2 overflow-x-auto pb-2">
                {categories.map((category) => {
                    const Icon = category.icon;
                    const isActive = activeCategory === category.id;
                    return (
                        <button
                            key={category.id}
                            onClick={() => setActiveCategory(category.id)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-xl whitespace-nowrap text-sm font-medium transition-all duration-300 ${isActive
                                    ? 'bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 shadow-md'
                                    : 'bg-white dark:bg-neo-dark/60 text-gray-700 dark:text-neo-dim border border-gray-200 dark:border-neo-primary/20 hover:bg-gray-50 dark:hover:bg-neo-dark/80'
                                }`}
                        >
                            <Icon className="w-4 h-4" />
                            <span>{category.name}</span>
                            <span
                                className={`text-xs px-1.5 py-0.5 rounded-full ${isActive ? 'bg-white/20 text-white' : 'bg-gray-100 dark:bg-primary-900/50 text-gray-500 dark:text-neo-dim'
                                    }`}
                            >
                                {category.count}
                            </span>
                        </button>
                    );
                })}
            </div>
        </div>
    );

    const AdvertBanner = () => (
        <div className="mb-8">
            <div className="rounded-xl bg-gradient-to-r from-neo-primary/20 via-neo-secondary/20 to-neo-accent/20 dark:from-neo-primary/10 dark:via-neo-secondary/10 dark:to-neo-accent/10 backdrop-blur-sm border border-neo-primary/30 p-6">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-1">Premium Network Access</h3>
                        <p className="text-sm text-gray-600 dark:text-neo-dim mb-4">
                            Get faster speeds and priority access. Upgrade now for uninterrupted streaming and browsing.
                        </p>
                        <button className="px-5 py-2 rounded-lg bg-white dark:bg-neo-dark text-neo-primary dark:text-neo-primary font-medium border border-neo-primary/30 shadow-sm hover:shadow-md transition-all">
                            Upgrade Now
                        </button>
                    </div>
                    <div className="text-5xl">🚀</div>
                </div>
            </div>
        </div>
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-neo-darker dark:to-neo-dark flex items-center justify-center">
                <div className="animate-spin rounded-full h-10 w-10 border-2 border-neo-primary border-t-transparent" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-neo-darker dark:to-neo-dark transition-colors duration-300 p-4 sm:p-6">
            {/* Ambient glows */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-neo-primary/5 blur-3xl" />
                <div className="absolute bottom-0 left-0 h-80 w-80 rounded-full bg-neo-secondary/5 blur-3xl" />
            </div>

            <div className="relative max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
                        <span className="bg-gradient-to-r from-neo-primary via-neo-secondary to-neo-accent bg-clip-text text-transparent">
                            Discover
                        </span>
                        <span className="text-gray-900 dark:text-neo-text"> Services</span>
                    </h1>
                    <p className="text-gray-500 dark:text-neo-dim text-sm sm:text-base mt-1">
                        Explore local services, entertainment, and exclusive offers available on our network
                    </p>
                </div>

                <FeaturedSection />
                <AdvertBanner />
                <CategoryFilter />

                {filteredServices.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                        {filteredServices.map((service) => (
                            <ServiceCard key={service.id} service={service} />
                        ))}
                    </div>
                ) : (
                    <div className="rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-12 text-center">
                        <div className="text-5xl mb-4">🔍</div>
                        <h3 className="text-lg font-medium text-gray-900 dark:text-neo-text mb-2">No services found</h3>
                        <p className="text-sm text-gray-500 dark:text-neo-dim">Try adjusting your search or filter criteria</p>
                    </div>
                )}

                {/* Bottom CTA */}
                <div className="rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-8 text-center shadow-md">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-neo-text mb-2">Have a service to list?</h3>
                    <p className="text-sm text-gray-500 dark:text-neo-dim mb-4">
                        Join our network and reach thousands of potential customers
                    </p>
                    <button className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 font-medium shadow-md hover:shadow-neo transition-all duration-300">
                        List Your Service
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DiscoverPage;
