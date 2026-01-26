// Local Vendor Service for 'Vocal for Local' Initiative
// Implements Requirements 12.3 and 12.5

/**
 * Mock data for local vendors and products
 * In production, this would connect to a real backend API
 */
const mockVendors = [
    {
        id: 'vendor_001',
        name: 'राम किसान',
        englishName: 'Ram Kisan',
        location: {
            state: 'Uttar Pradesh',
            district: 'Meerut',
            village: 'Sardhana',
            coordinates: { lat: 29.1492, lng: 77.6130 }
        },
        type: 'farmer',
        specialties: ['wheat', 'rice', 'sugarcane'],
        isLocal: true,
        distance: 5.2, // km from user
        rating: 4.7,
        totalTransactions: 156,
        languages: ['hi', 'en'],
        products: [
            {
                id: 'prod_001',
                name: 'गेहूं',
                englishName: 'Wheat',
                category: 'grains',
                quality: 'premium',
                price: 2200, // per quintal
                quantity: 50,
                unit: 'quintal',
                freshness: 95,
                organic: true
            }
        ],
        certifications: ['organic', 'fpo_member'],
        contactInfo: {
            phone: '+91-9876543210',
            whatsapp: '+91-9876543210'
        }
    },
    {
        id: 'vendor_002',
        name: 'सुनीता देवी',
        englishName: 'Sunita Devi',
        location: {
            state: 'Punjab',
            district: 'Ludhiana',
            village: 'Khanna',
            coordinates: { lat: 30.7046, lng: 76.2222 }
        },
        type: 'farmer',
        specialties: ['vegetables', 'dairy'],
        isLocal: true,
        distance: 12.8,
        rating: 4.9,
        totalTransactions: 203,
        languages: ['pa', 'hi', 'en'],
        products: [
            {
                id: 'prod_002',
                name: 'ਦੁੱਧ',
                englishName: 'Fresh Milk',
                category: 'dairy',
                quality: 'premium',
                price: 60, // per liter
                quantity: 100,
                unit: 'liter',
                freshness: 100,
                organic: true
            }
        ],
        certifications: ['dairy_license', 'quality_assured'],
        contactInfo: {
            phone: '+91-9876543211',
            whatsapp: '+91-9876543211'
        }
    },
    {
        id: 'vendor_003',
        name: 'முருகன்',
        englishName: 'Murugan',
        location: {
            state: 'Tamil Nadu',
            district: 'Coimbatore',
            village: 'Pollachi',
            coordinates: { lat: 10.6581, lng: 77.0081 }
        },
        type: 'farmer',
        specialties: ['coconut', 'spices', 'turmeric'],
        isLocal: false,
        distance: 45.3,
        rating: 4.6,
        totalTransactions: 89,
        languages: ['ta', 'en'],
        products: [
            {
                id: 'prod_003',
                name: 'மஞ்சள்',
                englishName: 'Turmeric',
                category: 'spices',
                quality: 'premium',
                price: 8500, // per quintal
                quantity: 20,
                unit: 'quintal',
                freshness: 90,
                organic: true
            }
        ],
        certifications: ['organic', 'export_quality'],
        contactInfo: {
            phone: '+91-9876543212',
            whatsapp: '+91-9876543212'
        }
    }
];

const mockProducts = [
    {
        id: 'prod_004',
        name: 'बासमती चावल',
        englishName: 'Basmati Rice',
        category: 'grains',
        vendorId: 'vendor_001',
        isLocalProduct: true,
        regionalSpecialty: true,
        price: 4500,
        unit: 'quintal',
        quality: 'premium',
        origin: 'Uttar Pradesh',
        seasonality: 'year-round',
        culturalSignificance: 'Traditional aromatic rice variety'
    },
    {
        id: 'prod_005',
        name: 'ਸਰਸੋਂ ਦਾ ਤੇਲ',
        englishName: 'Mustard Oil',
        category: 'oils',
        vendorId: 'vendor_002',
        isLocalProduct: true,
        regionalSpecialty: true,
        price: 150,
        unit: 'liter',
        quality: 'premium',
        origin: 'Punjab',
        seasonality: 'winter-spring',
        culturalSignificance: 'Traditional cooking oil of North India'
    }
];

/**
 * Local Vendor Service Class
 */
class LocalVendorService {
    constructor() {
        this.vendors = mockVendors;
        this.products = mockProducts;
        this.userLocation = null;
        this.preferences = this.loadPreferences();
    }

    /**
     * Set user location for local vendor discovery
     */
    setUserLocation(location) {
        this.userLocation = location;
        localStorage.setItem('userLocation', JSON.stringify(location));
    }

    /**
     * Get user location from storage
     */
    getUserLocation() {
        if (!this.userLocation) {
            const stored = localStorage.getItem('userLocation');
            this.userLocation = stored ? JSON.parse(stored) : null;
        }
        return this.userLocation;
    }

    /**
     * Load user preferences for local markets
     */
    loadPreferences() {
        const stored = localStorage.getItem('localMarketPreferences');
        return stored ? JSON.parse(stored) : {
            preferLocal: true,
            maxDistance: 50, // km
            preferredLanguages: ['hi', 'en'],
            preferOrganic: true,
            supportSmallFarmers: true,
            regionalPreference: 'any'
        };
    }

    /**
     * Save user preferences
     */
    savePreferences(preferences) {
        this.preferences = { ...this.preferences, ...preferences };
        localStorage.setItem('localMarketPreferences', JSON.stringify(this.preferences));
    }

    /**
     * Get local vendors based on user location and preferences
     */
    async getLocalVendors(filters = {}) {
        try {
            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 500));

            let filteredVendors = [...this.vendors];

            // Filter by distance if user location is available
            if (this.userLocation && filters.maxDistance) {
                filteredVendors = filteredVendors.filter(vendor =>
                    vendor.distance <= filters.maxDistance
                );
            }

            // Filter by local preference
            if (filters.localOnly || this.preferences.preferLocal) {
                filteredVendors = filteredVendors.filter(vendor => vendor.isLocal);
            }

            // Filter by language
            if (filters.language) {
                filteredVendors = filteredVendors.filter(vendor =>
                    vendor.languages.includes(filters.language)
                );
            }

            // Filter by product category
            if (filters.category) {
                filteredVendors = filteredVendors.filter(vendor =>
                    vendor.products.some(product => product.category === filters.category)
                );
            }

            // Sort by local preference and distance
            filteredVendors.sort((a, b) => {
                if (a.isLocal && !b.isLocal) return -1;
                if (!a.isLocal && b.isLocal) return 1;
                return a.distance - b.distance;
            });

            return {
                success: true,
                vendors: filteredVendors,
                totalCount: filteredVendors.length,
                localCount: filteredVendors.filter(v => v.isLocal).length
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                vendors: [],
                totalCount: 0,
                localCount: 0
            };
        }
    }

    /**
     * Get highlighted local products
     */
    async getLocalProducts(filters = {}) {
        try {
            await new Promise(resolve => setTimeout(resolve, 300));

            let filteredProducts = [...this.products];

            // Filter by local products
            if (filters.localOnly !== false) {
                filteredProducts = filteredProducts.filter(product => product.isLocalProduct);
            }

            // Filter by regional specialty
            if (filters.regionalSpecialty) {
                filteredProducts = filteredProducts.filter(product => product.regionalSpecialty);
            }

            // Filter by category
            if (filters.category) {
                filteredProducts = filteredProducts.filter(product =>
                    product.category === filters.category
                );
            }

            // Add vendor information
            filteredProducts = filteredProducts.map(product => ({
                ...product,
                vendor: this.vendors.find(v => v.id === product.vendorId)
            }));

            return {
                success: true,
                products: filteredProducts,
                totalCount: filteredProducts.length
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                products: [],
                totalCount: 0
            };
        }
    }

    /**
     * Get vendor recommendations based on user preferences
     */
    async getVendorRecommendations() {
        try {
            await new Promise(resolve => setTimeout(resolve, 400));

            let recommendations = [...this.vendors];

            // Prioritize local vendors
            if (this.preferences.preferLocal) {
                recommendations = recommendations.filter(vendor => vendor.isLocal);
            }

            // Filter by preferred languages
            if (this.preferences.preferredLanguages.length > 0) {
                recommendations = recommendations.filter(vendor =>
                    vendor.languages.some(lang =>
                        this.preferences.preferredLanguages.includes(lang)
                    )
                );
            }

            // Filter by organic preference
            if (this.preferences.preferOrganic) {
                recommendations = recommendations.filter(vendor =>
                    vendor.products.some(product => product.organic)
                );
            }

            // Sort by rating and local preference
            recommendations.sort((a, b) => {
                if (a.isLocal && !b.isLocal) return -1;
                if (!a.isLocal && b.isLocal) return 1;
                return b.rating - a.rating;
            });

            return {
                success: true,
                recommendations: recommendations.slice(0, 10), // Top 10
                totalCount: recommendations.length
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                recommendations: [],
                totalCount: 0
            };
        }
    }

    /**
     * Connect urban buyers with rural vendors
     */
    async facilitateUrbanRuralConnection(buyerProfile, requirements) {
        try {
            await new Promise(resolve => setTimeout(resolve, 600));

            // Find rural vendors that match requirements
            const ruralVendors = this.vendors.filter(vendor =>
                vendor.location.village && // Has village (rural indicator)
                vendor.products.some(product =>
                    requirements.categories.includes(product.category)
                )
            );

            // Calculate compatibility scores
            const connections = ruralVendors.map(vendor => {
                let compatibilityScore = 0;

                // Language compatibility
                const commonLanguages = vendor.languages.filter(lang =>
                    buyerProfile.languages.includes(lang)
                );
                compatibilityScore += commonLanguages.length * 20;

                // Product match
                const matchingProducts = vendor.products.filter(product =>
                    requirements.categories.includes(product.category)
                );
                compatibilityScore += matchingProducts.length * 15;

                // Quality preference
                if (requirements.qualityPreference === 'premium' &&
                    vendor.products.some(p => p.quality === 'premium')) {
                    compatibilityScore += 25;
                }

                // Organic preference
                if (requirements.preferOrganic &&
                    vendor.products.some(p => p.organic)) {
                    compatibilityScore += 20;
                }

                // Rating bonus
                compatibilityScore += vendor.rating * 5;

                return {
                    vendor,
                    compatibilityScore,
                    commonLanguages,
                    matchingProducts,
                    estimatedDeliveryTime: this.calculateDeliveryTime(
                        buyerProfile.location,
                        vendor.location
                    )
                };
            });

            // Sort by compatibility score
            connections.sort((a, b) => b.compatibilityScore - a.compatibilityScore);

            return {
                success: true,
                connections: connections.slice(0, 5), // Top 5 matches
                totalMatches: connections.length,
                averageCompatibility: connections.reduce((sum, conn) =>
                    sum + conn.compatibilityScore, 0) / connections.length
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                connections: [],
                totalMatches: 0
            };
        }
    }

    /**
     * Calculate estimated delivery time between locations
     */
    calculateDeliveryTime(buyerLocation, vendorLocation) {
        // Simple distance-based calculation
        // In production, this would use real routing APIs
        const distance = this.calculateDistance(
            buyerLocation.coordinates,
            vendorLocation.coordinates
        );

        if (distance < 50) return '1-2 days';
        if (distance < 200) return '2-4 days';
        if (distance < 500) return '4-7 days';
        return '7-14 days';
    }

    /**
     * Calculate distance between two coordinates (simplified)
     */
    calculateDistance(coord1, coord2) {
        const R = 6371; // Earth's radius in km
        const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
        const dLon = (coord2.lng - coord1.lng) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    /**
     * Get local market statistics
     */
    async getLocalMarketStats() {
        try {
            await new Promise(resolve => setTimeout(resolve, 200));

            const totalVendors = this.vendors.length;
            const localVendors = this.vendors.filter(v => v.isLocal).length;
            const totalProducts = this.products.length;
            const localProducts = this.products.filter(p => p.isLocalProduct).length;
            const organicProducts = this.products.filter(p => p.organic).length;

            return {
                success: true,
                stats: {
                    totalVendors,
                    localVendors,
                    localVendorPercentage: Math.round((localVendors / totalVendors) * 100),
                    totalProducts,
                    localProducts,
                    localProductPercentage: Math.round((localProducts / totalProducts) * 100),
                    organicProducts,
                    organicPercentage: Math.round((organicProducts / totalProducts) * 100),
                    averageRating: this.vendors.reduce((sum, v) => sum + v.rating, 0) / totalVendors,
                    totalTransactions: this.vendors.reduce((sum, v) => sum + v.totalTransactions, 0)
                }
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                stats: {}
            };
        }
    }

    /**
     * Search local vendors by name or specialty
     */
    async searchLocalVendors(query, filters = {}) {
        try {
            await new Promise(resolve => setTimeout(resolve, 300));

            const searchTerm = query.toLowerCase();
            let results = this.vendors.filter(vendor =>
                vendor.name.toLowerCase().includes(searchTerm) ||
                vendor.englishName.toLowerCase().includes(searchTerm) ||
                vendor.specialties.some(specialty =>
                    specialty.toLowerCase().includes(searchTerm)
                ) ||
                vendor.location.district.toLowerCase().includes(searchTerm) ||
                vendor.location.state.toLowerCase().includes(searchTerm)
            );

            // Apply additional filters
            if (filters.localOnly) {
                results = results.filter(vendor => vendor.isLocal);
            }

            if (filters.maxDistance && this.userLocation) {
                results = results.filter(vendor => vendor.distance <= filters.maxDistance);
            }

            // Sort by relevance and local preference
            results.sort((a, b) => {
                if (a.isLocal && !b.isLocal) return -1;
                if (!a.isLocal && b.isLocal) return 1;
                return b.rating - a.rating;
            });

            return {
                success: true,
                results,
                totalCount: results.length,
                query: searchTerm
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                results: [],
                totalCount: 0
            };
        }
    }
}

// Create and export singleton instance
const localVendorService = new LocalVendorService();
export default localVendorService;

// Export individual methods for testing
export {
    LocalVendorService,
    mockVendors,
    mockProducts
};