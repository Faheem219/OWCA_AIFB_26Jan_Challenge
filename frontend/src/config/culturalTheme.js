// Cultural Theme Configuration for Multilingual Mandi
// Implements Requirements 12.1, 12.2, and 9.6

/**
 * Indian Cultural Color Palette
 * Based on traditional Indian colors and the national tricolor
 */
export const culturalColors = {
    // Indian Tricolor
    saffron: '#FF9933',
    white: '#FFFFFF',
    green: '#138808',
    navyBlue: '#000080',

    // Regional Cultural Colors
    goldenYellow: '#FFD700',
    deepOrange: '#FF6B35',
    royalBlue: '#4169E1',
    emeraldGreen: '#50C878',
    crimsonRed: '#DC143C',
    warmBrown: '#8B4513',

    // Cultural Accent Colors
    marigold: '#FFA500',
    turmeric: '#E4D00A',
    henna: '#B85450',
    peacockBlue: '#005F69',
    lotusPink: '#F8BBD9',

    // Gradient Combinations
    culturalGradient: 'linear-gradient(135deg, #FF9933 0%, #FFFFFF 50%, #138808 100%)',
    sunsetGradient: 'linear-gradient(135deg, #FF6B35 0%, #FFD700 100%)',
    heritageGradient: 'linear-gradient(135deg, #4169E1 0%, #005F69 100%)'
};

/**
 * Supported Indian Languages Configuration
 * All 22 official languages with their font families and display names
 */
export const supportedLanguages = [
    {
        code: 'hi',
        name: 'हिंदी',
        englishName: 'Hindi',
        fontFamily: 'Noto Sans Devanagari',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Devanagari'
    },
    {
        code: 'en',
        name: 'English',
        englishName: 'English',
        fontFamily: 'system-ui',
        flag: '🇬🇧',
        direction: 'ltr',
        script: 'Latin'
    },
    {
        code: 'ta',
        name: 'தமிழ்',
        englishName: 'Tamil',
        fontFamily: 'Noto Sans Tamil',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Tamil'
    },
    {
        code: 'te',
        name: 'తెలుగు',
        englishName: 'Telugu',
        fontFamily: 'Noto Sans Telugu',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Telugu'
    },
    {
        code: 'bn',
        name: 'বাংলা',
        englishName: 'Bengali',
        fontFamily: 'Noto Sans Bengali',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Bengali'
    },
    {
        code: 'gu',
        name: 'ગુજરાતી',
        englishName: 'Gujarati',
        fontFamily: 'Noto Sans Gujarati',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Gujarati'
    },
    {
        code: 'kn',
        name: 'ಕನ್ನಡ',
        englishName: 'Kannada',
        fontFamily: 'Noto Sans Kannada',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Kannada'
    },
    {
        code: 'ml',
        name: 'മലയാളം',
        englishName: 'Malayalam',
        fontFamily: 'Noto Sans Malayalam',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Malayalam'
    },
    {
        code: 'mr',
        name: 'मराठी',
        englishName: 'Marathi',
        fontFamily: 'Noto Sans Devanagari',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Devanagari'
    },
    {
        code: 'pa',
        name: 'ਪੰਜਾਬੀ',
        englishName: 'Punjabi',
        fontFamily: 'Noto Sans Gurmukhi',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Gurmukhi'
    },
    {
        code: 'or',
        name: 'ଓଡ଼ିଆ',
        englishName: 'Odia',
        fontFamily: 'Noto Sans Oriya',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Oriya'
    },
    {
        code: 'as',
        name: 'অসমীয়া',
        englishName: 'Assamese',
        fontFamily: 'Noto Sans Bengali',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Bengali'
    },
    {
        code: 'ur',
        name: 'اردو',
        englishName: 'Urdu',
        fontFamily: 'Noto Sans Devanagari',
        flag: '🇮🇳',
        direction: 'rtl',
        script: 'Arabic'
    },
    {
        code: 'sa',
        name: 'संस्कृतम्',
        englishName: 'Sanskrit',
        fontFamily: 'Noto Sans Devanagari',
        flag: '🇮🇳',
        direction: 'ltr',
        script: 'Devanagari'
    },
    {
        code: 'sd',
        name: 'سنڌي',
        englishName: 'Sindhi',
        fontFamily: 'Noto Sans Devanagari',
        flag: '🇮🇳',
        direction: 'rtl',
        script: 'Arabic'
    }
];

/**
 * Cultural Design Patterns and Motifs
 */
export const culturalPatterns = {
    mandala: {
        name: 'Mandala Pattern',
        cssClass: 'mandala-pattern',
        description: 'Traditional circular geometric pattern'
    },
    paisley: {
        name: 'Paisley Accent',
        cssClass: 'paisley-accent',
        description: 'Traditional teardrop-shaped motif'
    },
    rangoli: {
        name: 'Rangoli Border',
        cssClass: 'rangoli-border',
        description: 'Colorful geometric border pattern'
    },
    lotus: {
        name: 'Lotus Pattern',
        cssClass: 'lotus-pattern',
        description: 'Sacred lotus flower motif'
    },
    geometric: {
        name: 'Geometric Pattern',
        cssClass: 'geometric-pattern',
        description: 'Traditional Indian geometric designs'
    }
};

/**
 * Cultural UI Component Variants
 */
export const componentVariants = {
    button: {
        primary: 'cultural-button',
        secondary: 'cultural-button-secondary',
        outline: 'cultural-button-outline',
        gradient: 'cultural-button-gradient'
    },
    card: {
        default: 'cultural-card',
        elevated: 'cultural-card-elevated',
        minimal: 'cultural-card-minimal'
    },
    input: {
        default: 'cultural-input',
        textarea: 'cultural-textarea'
    },
    status: {
        online: 'status-online',
        offline: 'status-offline',
        connecting: 'status-connecting'
    }
};

/**
 * Regional Color Schemes
 * Different color combinations for various Indian regions
 */
export const regionalColorSchemes = {
    north: {
        primary: culturalColors.saffron,
        secondary: culturalColors.goldenYellow,
        accent: culturalColors.crimsonRed,
        name: 'Northern India'
    },
    south: {
        primary: culturalColors.deepOrange,
        secondary: culturalColors.turmeric,
        accent: culturalColors.emeraldGreen,
        name: 'Southern India'
    },
    east: {
        primary: culturalColors.crimsonRed,
        secondary: culturalColors.goldenYellow,
        accent: culturalColors.peacockBlue,
        name: 'Eastern India'
    },
    west: {
        primary: culturalColors.royalBlue,
        secondary: culturalColors.marigold,
        accent: culturalColors.emeraldGreen,
        name: 'Western India'
    },
    central: {
        primary: culturalColors.warmBrown,
        secondary: culturalColors.goldenYellow,
        accent: culturalColors.green,
        name: 'Central India'
    }
};

/**
 * Cultural Symbols and Icons
 */
export const culturalSymbols = {
    flag: '🇮🇳',
    lotus: '🪷',
    om: 'ॐ',
    peacock: '🦚',
    elephant: '🐘',
    tiger: '🐅',
    wheel: '☸️',
    star: '⭐',
    sun: '☀️',
    moon: '🌙',
    flower: '🌸',
    leaf: '🌿',
    temple: '🛕',
    diya: '🪔'
};

/**
 * Accessibility Settings
 */
export const accessibilitySettings = {
    highContrast: {
        saffron: '#FF8C00',
        green: '#006400',
        goldenYellow: '#FFD700'
    },
    fontSize: {
        small: '14px',
        medium: '16px',
        large: '18px',
        extraLarge: '20px'
    },
    reducedMotion: {
        disableAnimations: true,
        disableTransitions: false
    }
};

/**
 * Responsive Breakpoints
 */
export const breakpoints = {
    mobile: '480px',
    tablet: '768px',
    desktop: '1024px',
    wide: '1200px'
};

/**
 * Cultural Theme Utilities
 */
export const themeUtils = {
    /**
     * Get language configuration by code
     */
    getLanguageConfig: (languageCode) => {
        return supportedLanguages.find(lang => lang.code === languageCode) || supportedLanguages[0];
    },

    /**
     * Get regional color scheme
     */
    getRegionalColors: (region) => {
        return regionalColorSchemes[region] || regionalColorSchemes.north;
    },

    /**
     * Generate CSS custom properties for cultural colors
     */
    generateCSSVariables: () => {
        const cssVars = {};
        Object.entries(culturalColors).forEach(([key, value]) => {
            cssVars[`--${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`] = value;
        });
        return cssVars;
    },

    /**
     * Get appropriate font family for language
     */
    getFontFamily: (languageCode) => {
        const config = themeUtils.getLanguageConfig(languageCode);
        return config.fontFamily;
    },

    /**
     * Check if language is RTL
     */
    isRTL: (languageCode) => {
        const config = themeUtils.getLanguageConfig(languageCode);
        return config.direction === 'rtl';
    }
};

export default {
    culturalColors,
    supportedLanguages,
    culturalPatterns,
    componentVariants,
    regionalColorSchemes,
    culturalSymbols,
    accessibilitySettings,
    breakpoints,
    themeUtils
};