import React, { useState, useEffect } from 'react';
import {
    CulturalCard,
    CulturalButton,
    CulturalText,
    CulturalInput,
    CulturalLoader,
    CulturalAlert,
    LanguageSelector
} from './CulturalElements';
import localVendorService from '../services/localVendorService';
import './VocalForLocal.css';

/**
 * VocalForLocal Component - Implements Requirements 12.3 and 12.5
 * Promotes local vendors and facilitates urban-rural connections
 */
const VocalForLocal = ({ language = 'hi', onLanguageChange }) => {
    const [activeTab, setActiveTab] = useState('discover');
    const [loading, setLoading] = useState(false);
    const [localVendors, setLocalVendors] = useState([]);
    const [localProducts, setLocalProducts] = useState([]);
    const [marketStats, setMarketStats] = useState({});
    const [preferences, setPreferences] = useState({});
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [alert, setAlert] = useState(null);
    const [urbanRuralConnections, setUrbanRuralConnections] = useState([]);

    // Translations for different languages
    const translations = {
        hi: {
            title: 'वोकल फॉर लोकल',
            subtitle: 'स्थानीय विक्रेताओं को बढ़ावा दें',
            discover: 'खोजें',
            vendors: 'विक्रेता',
            products: 'उत्पाद',
            connect: 'जुड़ें',
            settings: 'सेटिंग्स',
            localVendors: 'स्थानीय विक्रेता',
            nearbyProducts: 'आस-पास के उत्पाद',
            searchPlaceholder: 'विक्रेता या उत्पाद खोजें...',
            distance: 'दूरी',
            rating: 'रेटिंग',
            transactions: 'लेन-देन',
            organic: 'जैविक',
            premium: 'प्रीमियम',
            contact: 'संपर्क करें',
            viewDetails: 'विवरण देखें',
            localSupport: 'स्थानीय समर्थन',
            ruralConnection: 'ग्रामीण कनेक्शन',
            preferences: 'प्राथमिकताएं',
            maxDistance: 'अधिकतम दूरी (किमी)',
            preferLocal: 'स्थानीय को प्राथमिकता दें',
            preferOrganic: 'जैविक को प्राथमिकता दें',
            supportSmallFarmers: 'छोटे किसानों का समर्थन करें',
            save: 'सहेजें',
            stats: 'आंकड़े',
            totalVendors: 'कुल विक्रेता',
            localPercentage: 'स्थानीय प्रतिशत',
            averageRating: 'औसत रेटिंग',
            connecting: 'जुड़ रहा है...',
            connected: 'जुड़ गया',
            error: 'त्रुटि',
            success: 'सफलता'
        },
        en: {
            title: 'Vocal for Local',
            subtitle: 'Promote Local Vendors',
            discover: 'Discover',
            vendors: 'Vendors',
            products: 'Products',
            connect: 'Connect',
            settings: 'Settings',
            localVendors: 'Local Vendors',
            nearbyProducts: 'Nearby Products',
            searchPlaceholder: 'Search vendors or products...',
            distance: 'Distance',
            rating: 'Rating',
            transactions: 'Transactions',
            organic: 'Organic',
            premium: 'Premium',
            contact: 'Contact',
            viewDetails: 'View Details',
            localSupport: 'Local Support',
            ruralConnection: 'Rural Connection',
            preferences: 'Preferences',
            maxDistance: 'Max Distance (km)',
            preferLocal: 'Prefer Local',
            preferOrganic: 'Prefer Organic',
            supportSmallFarmers: 'Support Small Farmers',
            save: 'Save',
            stats: 'Statistics',
            totalVendors: 'Total Vendors',
            localPercentage: 'Local Percentage',
            averageRating: 'Average Rating',
            connecting: 'Connecting...',
            connected: 'Connected',
            error: 'Error',
            success: 'Success'
        },
        ta: {
            title: 'வோக்கல் ஃபார் லோக்கல்',
            subtitle: 'உள்ளூர் விற்பனையாளர்களை ஊக்குவிக்கவும்',
            discover: 'கண்டுபிடி',
            vendors: 'விற்பனையாளர்கள்',
            products: 'பொருட்கள்',
            connect: 'இணைக்க',
            settings: 'அமைப்புகள்',
            localVendors: 'உள்ளூர் விற்பனையாளர்கள்',
            nearbyProducts: 'அருகிலுள்ள பொருட்கள்',
            searchPlaceholder: 'விற்பனையாளர்கள் அல்லது பொருட்களைத் தேடுங்கள்...',
            distance: 'தூரம்',
            rating: 'மதிப்பீடு',
            transactions: 'பரிவர்த்தனைகள்',
            organic: 'இயற்கை',
            premium: 'பிரீமியம்',
            contact: 'தொடர்பு கொள்ளுங்கள்',
            viewDetails: 'விவரங்களைப் பார்க்கவும்',
            localSupport: 'உள்ளூர் ஆதரவு',
            ruralConnection: 'கிராமப்புற இணைப்பு',
            preferences: 'விருப்பத்தேர்வுகள்',
            maxDistance: 'அதிகபட்ச தூரம் (கிமீ)',
            preferLocal: 'உள்ளூரை விரும்பு',
            preferOrganic: 'இயற்கையை விரும்பு',
            supportSmallFarmers: 'சிறு விவசாயிகளை ஆதரிக்கவும்',
            save: 'சேமி',
            stats: 'புள்ளிவிவரங்கள்',
            totalVendors: 'மொத்த விற்பனையாளர்கள்',
            localPercentage: 'உள்ளூர் சதவீதம்',
            averageRating: 'சராசரி மதிப்பீடு',
            connecting: 'இணைக்கிறது...',
            connected: 'இணைக்கப்பட்டது',
            error: 'பிழை',
            success: 'வெற்றி'
        }
    };

    const t = translations[language] || translations.en;

    useEffect(() => {
        loadInitialData();
        loadPreferences();
    }, []);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            const [vendorsResult, productsResult, statsResult] = await Promise.all([
                localVendorService.getLocalVendors({ localOnly: true, maxDistance: 50 }),
                localVendorService.getLocalProducts({ localOnly: true }),
                localVendorService.getLocalMarketStats()
            ]);

            if (vendorsResult.success) {
                setLocalVendors(vendorsResult.vendors);
            }

            if (productsResult.success) {
                setLocalProducts(productsResult.products);
            }

            if (statsResult.success) {
                setMarketStats(statsResult.stats);
            }
        } catch (error) {
            setAlert({
                type: 'error',
                message: `${t.error}: ${error.message}`
            });
        } finally {
            setLoading(false);
        }
    };

    const loadPreferences = () => {
        const prefs = localVendorService.loadPreferences();
        setPreferences(prefs);
    };

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;

        setLoading(true);
        try {
            const result = await localVendorService.searchLocalVendors(searchQuery, {
                localOnly: preferences.preferLocal
            });

            if (result.success) {
                setSearchResults(result.results);
                setActiveTab('search');
            } else {
                setAlert({
                    type: 'error',
                    message: result.error
                });
            }
        } catch (error) {
            setAlert({
                type: 'error',
                message: error.message
            });
        } finally {
            setLoading(false);
        }
    };

    const handleUrbanRuralConnect = async () => {
        setLoading(true);
        try {
            const buyerProfile = {
                location: {
                    coordinates: { lat: 28.6139, lng: 77.2090 } // Delhi coordinates
                },
                languages: [language, 'en']
            };

            const requirements = {
                categories: ['grains', 'vegetables', 'dairy'],
                qualityPreference: 'premium',
                preferOrganic: preferences.preferOrganic
            };

            const result = await localVendorService.facilitateUrbanRuralConnection(
                buyerProfile,
                requirements
            );

            if (result.success) {
                setUrbanRuralConnections(result.connections);
                setActiveTab('connect');
                setAlert({
                    type: 'success',
                    message: `${t.success}: ${result.totalMatches} ${t.connected}`
                });
            } else {
                setAlert({
                    type: 'error',
                    message: result.error
                });
            }
        } catch (error) {
            setAlert({
                type: 'error',
                message: error.message
            });
        } finally {
            setLoading(false);
        }
    };

    const handleSavePreferences = () => {
        localVendorService.savePreferences(preferences);
        setAlert({
            type: 'success',
            message: `${t.preferences} ${t.save}d successfully!`
        });
        loadInitialData(); // Reload data with new preferences
    };

    const renderDiscoverTab = () => (
        <div className="vocal-discover">
            {/* Market Statistics */}
            <CulturalCard className="mb-6" showTricolorBorder>
                <div className="p-4">
                    <CulturalText variant="heading" language={language} className="mb-4">
                        {t.stats}
                    </CulturalText>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-saffron">
                                {marketStats.totalVendors || 0}
                            </div>
                            <div className="text-sm text-gray-600">{t.totalVendors}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-green">
                                {marketStats.localVendorPercentage || 0}%
                            </div>
                            <div className="text-sm text-gray-600">{t.localPercentage}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-peacock-blue">
                                {marketStats.averageRating?.toFixed(1) || 0}
                            </div>
                            <div className="text-sm text-gray-600">{t.averageRating}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-turmeric">
                                {marketStats.organicPercentage || 0}%
                            </div>
                            <div className="text-sm text-gray-600">{t.organic}</div>
                        </div>
                    </div>
                </div>
            </CulturalCard>

            {/* Search Bar */}
            <div className="mb-6">
                <div className="flex gap-2">
                    <CulturalInput
                        placeholder={t.searchPlaceholder}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        language={language}
                        className="flex-1"
                        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    <CulturalButton onClick={handleSearch} disabled={loading}>
                        {loading ? t.connecting : t.discover}
                    </CulturalButton>
                </div>
            </div>

            {/* Local Vendors Grid */}
            <div className="mb-8">
                <CulturalText variant="heading" language={language} className="mb-4">
                    {t.localVendors}
                </CulturalText>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {localVendors.slice(0, 6).map(vendor => (
                        <VendorCard key={vendor.id} vendor={vendor} language={language} t={t} />
                    ))}
                </div>
            </div>

            {/* Local Products Grid */}
            <div>
                <CulturalText variant="heading" language={language} className="mb-4">
                    {t.nearbyProducts}
                </CulturalText>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {localProducts.slice(0, 8).map(product => (
                        <ProductCard key={product.id} product={product} language={language} t={t} />
                    ))}
                </div>
            </div>
        </div>
    );

    const renderConnectTab = () => (
        <div className="vocal-connect">
            <div className="mb-6 text-center">
                <CulturalText variant="heading" language={language} className="mb-2">
                    {t.ruralConnection}
                </CulturalText>
                <CulturalText language={language} className="text-gray-600 mb-4">
                    Connect urban buyers with rural vendors
                </CulturalText>
                <CulturalButton onClick={handleUrbanRuralConnect} disabled={loading}>
                    {loading ? t.connecting : t.connect}
                </CulturalButton>
            </div>

            {urbanRuralConnections.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {urbanRuralConnections.map((connection, index) => (
                        <ConnectionCard
                            key={index}
                            connection={connection}
                            language={language}
                            t={t}
                        />
                    ))}
                </div>
            )}
        </div>
    );

    const renderSettingsTab = () => (
        <div className="vocal-settings">
            <CulturalCard className="p-6">
                <CulturalText variant="heading" language={language} className="mb-6">
                    {t.preferences}
                </CulturalText>

                <div className="space-y-6">
                    <div>
                        <label className="block mb-2">
                            <CulturalText language={language}>{t.maxDistance}</CulturalText>
                        </label>
                        <CulturalInput
                            type="number"
                            value={preferences.maxDistance || 50}
                            onChange={(e) => setPreferences({
                                ...preferences,
                                maxDistance: parseInt(e.target.value)
                            })}
                            language={language}
                        />
                    </div>

                    <div className="space-y-3">
                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                checked={preferences.preferLocal || false}
                                onChange={(e) => setPreferences({
                                    ...preferences,
                                    preferLocal: e.target.checked
                                })}
                                className="mr-3"
                            />
                            <CulturalText language={language}>{t.preferLocal}</CulturalText>
                        </label>

                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                checked={preferences.preferOrganic || false}
                                onChange={(e) => setPreferences({
                                    ...preferences,
                                    preferOrganic: e.target.checked
                                })}
                                className="mr-3"
                            />
                            <CulturalText language={language}>{t.preferOrganic}</CulturalText>
                        </label>

                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                checked={preferences.supportSmallFarmers || false}
                                onChange={(e) => setPreferences({
                                    ...preferences,
                                    supportSmallFarmers: e.target.checked
                                })}
                                className="mr-3"
                            />
                            <CulturalText language={language}>{t.supportSmallFarmers}</CulturalText>
                        </label>
                    </div>

                    <CulturalButton onClick={handleSavePreferences}>
                        {t.save}
                    </CulturalButton>
                </div>
            </CulturalCard>
        </div>
    );

    const renderSearchTab = () => (
        <div className="vocal-search">
            <CulturalText variant="heading" language={language} className="mb-4">
                Search Results for "{searchQuery}"
            </CulturalText>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {searchResults.map(vendor => (
                    <VendorCard key={vendor.id} vendor={vendor} language={language} t={t} />
                ))}
            </div>
        </div>
    );

    return (
        <div className="vocal-for-local">
            {/* Header */}
            <div className="vocal-header mb-8">
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <CulturalText variant="heading" language={language} className="text-3xl mb-2">
                            {t.title} 🇮🇳
                        </CulturalText>
                        <CulturalText language={language} className="text-gray-600">
                            {t.subtitle}
                        </CulturalText>
                    </div>
                    <LanguageSelector
                        selectedLanguage={language}
                        onLanguageChange={onLanguageChange}
                    />
                </div>

                {/* Tab Navigation */}
                <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
                    {[
                        { key: 'discover', label: t.discover },
                        { key: 'connect', label: t.connect },
                        { key: 'settings', label: t.settings }
                    ].map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`px-4 py-2 rounded-md transition-all ${activeTab === tab.key
                                    ? 'bg-saffron text-white'
                                    : 'text-gray-600 hover:text-saffron'
                                }`}
                        >
                            <CulturalText language={language}>{tab.label}</CulturalText>
                        </button>
                    ))}
                </div>
            </div>

            {/* Alert */}
            {alert && (
                <CulturalAlert
                    type={alert.type}
                    message={alert.message}
                    onClose={() => setAlert(null)}
                    className="mb-6"
                />
            )}

            {/* Loading */}
            {loading && (
                <CulturalLoader
                    message={language === 'hi' ? 'लोड हो रहा है...' : 'Loading...'}
                    className="mb-6"
                />
            )}

            {/* Tab Content */}
            <div className="vocal-content">
                {activeTab === 'discover' && renderDiscoverTab()}
                {activeTab === 'connect' && renderConnectTab()}
                {activeTab === 'settings' && renderSettingsTab()}
                {activeTab === 'search' && renderSearchTab()}
            </div>
        </div>
    );
};

// Vendor Card Component
const VendorCard = ({ vendor, language, t }) => (
    <CulturalCard className="vendor-card">
        <div className="p-4">
            <div className="flex justify-between items-start mb-3">
                <div>
                    <CulturalText variant="subheading" language={language} className="mb-1">
                        {language === 'en' ? vendor.englishName : vendor.name}
                    </CulturalText>
                    <div className="text-sm text-gray-600">
                        {vendor.location.district}, {vendor.location.state}
                    </div>
                </div>
                {vendor.isLocal && (
                    <span className="bg-green text-white px-2 py-1 rounded-full text-xs">
                        Local
                    </span>
                )}
            </div>

            <div className="flex justify-between items-center mb-3">
                <div className="text-sm">
                    <span className="text-gray-600">{t.distance}:</span> {vendor.distance}km
                </div>
                <div className="text-sm">
                    <span className="text-gray-600">{t.rating}:</span> ⭐ {vendor.rating}
                </div>
            </div>

            <div className="flex flex-wrap gap-1 mb-3">
                {vendor.specialties.slice(0, 3).map(specialty => (
                    <span key={specialty} className="bg-saffron/10 text-saffron px-2 py-1 rounded text-xs">
                        {specialty}
                    </span>
                ))}
            </div>

            <div className="flex gap-2">
                <CulturalButton size="small" className="flex-1">
                    {t.contact}
                </CulturalButton>
                <CulturalButton variant="outline" size="small" className="flex-1">
                    {t.viewDetails}
                </CulturalButton>
            </div>
        </div>
    </CulturalCard>
);

// Product Card Component
const ProductCard = ({ product, language, t }) => (
    <CulturalCard className="product-card">
        <div className="p-4">
            <CulturalText variant="subheading" language={language} className="mb-2">
                {language === 'en' ? product.englishName : product.name}
            </CulturalText>

            <div className="text-sm text-gray-600 mb-2">
                {product.vendor?.location.district}
            </div>

            <div className="flex justify-between items-center mb-3">
                <div className="text-lg font-bold text-saffron">
                    ₹{product.price}/{product.unit}
                </div>
                {product.organic && (
                    <span className="bg-green text-white px-2 py-1 rounded-full text-xs">
                        {t.organic}
                    </span>
                )}
            </div>

            {product.regionalSpecialty && (
                <div className="text-xs text-peacock-blue mb-2">
                    Regional Specialty
                </div>
            )}

            <CulturalButton size="small" className="w-full">
                {t.viewDetails}
            </CulturalButton>
        </div>
    </CulturalCard>
);

// Connection Card Component
const ConnectionCard = ({ connection, language, t }) => (
    <CulturalCard className="connection-card">
        <div className="p-4">
            <div className="flex justify-between items-start mb-3">
                <CulturalText variant="subheading" language={language}>
                    {language === 'en' ? connection.vendor.englishName : connection.vendor.name}
                </CulturalText>
                <div className="text-right">
                    <div className="text-sm font-bold text-saffron">
                        {connection.compatibilityScore}% Match
                    </div>
                    <div className="text-xs text-gray-600">
                        {connection.estimatedDeliveryTime}
                    </div>
                </div>
            </div>

            <div className="text-sm text-gray-600 mb-3">
                {connection.vendor.location.village}, {connection.vendor.location.district}
            </div>

            <div className="mb-3">
                <div className="text-xs text-gray-600 mb-1">Common Languages:</div>
                <div className="flex gap-1">
                    {connection.commonLanguages.map(lang => (
                        <span key={lang} className="bg-peacock-blue/10 text-peacock-blue px-2 py-1 rounded text-xs">
                            {lang}
                        </span>
                    ))}
                </div>
            </div>

            <div className="mb-3">
                <div className="text-xs text-gray-600 mb-1">Matching Products:</div>
                <div className="flex flex-wrap gap-1">
                    {connection.matchingProducts.slice(0, 3).map(product => (
                        <span key={product.id} className="bg-green/10 text-green px-2 py-1 rounded text-xs">
                            {language === 'en' ? product.englishName : product.name}
                        </span>
                    ))}
                </div>
            </div>

            <CulturalButton size="small" className="w-full">
                {t.connect}
            </CulturalButton>
        </div>
    </CulturalCard>
);

export default VocalForLocal;