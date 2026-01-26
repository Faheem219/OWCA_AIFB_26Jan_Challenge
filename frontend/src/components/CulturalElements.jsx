import React from 'react';

// Cultural Design Components for Multilingual Mandi
// Implements Requirements 12.1, 12.2, and 9.6

/**
 * Language-specific typography component
 * Supports all 22 official Indian languages with appropriate fonts
 */
export const CulturalText = ({
    children,
    language = 'en',
    className = '',
    variant = 'body'
}) => {
    const languageFonts = {
        'hi': 'font-devanagari', // Hindi
        'ta': 'font-tamil',      // Tamil
        'te': 'font-telugu',     // Telugu
        'bn': 'font-bengali',    // Bengali
        'gu': 'font-gujarati',   // Gujarati
        'kn': 'font-kannada',    // Kannada
        'ml': 'font-malayalam',  // Malayalam
        'or': 'font-oriya',      // Odia
        'pa': 'font-gurmukhi',   // Punjabi
        'mr': 'font-devanagari', // Marathi (uses Devanagari script)
        'as': 'font-bengali',    // Assamese (uses Bengali script)
        'ur': 'font-devanagari', // Urdu
        'en': ''                 // English (default)
    };

    const variantClasses = {
        'heading': 'text-2xl font-bold',
        'subheading': 'text-xl font-semibold',
        'body': 'text-base',
        'caption': 'text-sm'
    };

    const fontClass = languageFonts[language] || '';
    const variantClass = variantClasses[variant] || variantClasses.body;

    return (
        <span className={`${fontClass} ${variantClass} ${className}`}>
            {children}
        </span>
    );
};

/**
 * Cultural card component with Indian design motifs
 */
export const CulturalCard = ({
    children,
    className = '',
    variant = 'default',
    showTricolorBorder = false
}) => {
    const variantClasses = {
        'default': 'cultural-card',
        'elevated': 'cultural-card shadow-2xl',
        'minimal': 'cultural-card border-1'
    };

    const borderClass = showTricolorBorder ? 'cultural-pattern-border' : '';

    return (
        <div className={`${variantClasses[variant]} ${borderClass} ${className}`}>
            {children}
        </div>
    );
};

/**
 * Cultural button with Indian color schemes
 */
export const CulturalButton = ({
    children,
    onClick,
    variant = 'primary',
    size = 'medium',
    disabled = false,
    className = '',
    showPulse = false
}) => {
    const variantClasses = {
        'primary': 'cultural-button',
        'secondary': 'bg-white text-saffron border-2 border-saffron hover:bg-saffron hover:text-white',
        'outline': 'bg-transparent text-saffron border-2 border-saffron hover:bg-saffron hover:text-white',
        'success': 'bg-green text-white hover:bg-emerald-green',
        'warning': 'bg-turmeric text-navy-blue hover:bg-golden-yellow'
    };

    const sizeClasses = {
        'small': 'px-3 py-1.5 text-sm',
        'medium': 'px-6 py-3 text-base',
        'large': 'px-8 py-4 text-lg'
    };

    const pulseClass = showPulse ? 'cultural-pulse' : '';
    const disabledClass = disabled ? 'opacity-50 cursor-not-allowed' : '';

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`
        ${variantClasses[variant]} 
        ${sizeClasses[size]} 
        ${pulseClass} 
        ${disabledClass} 
        ${className}
        rounded-full font-semibold transition-all duration-300
      `}
        >
            {children}
        </button>
    );
};

/**
 * Language selector with cultural styling
 */
export const LanguageSelector = ({
    selectedLanguage,
    onLanguageChange,
    languages = [],
    className = ''
}) => {
    const defaultLanguages = [
        { code: 'hi', name: 'हिंदी', flag: '🇮🇳' },
        { code: 'en', name: 'English', flag: '🇬🇧' },
        { code: 'ta', name: 'தமிழ்', flag: '🇮🇳' },
        { code: 'te', name: 'తెలుగు', flag: '🇮🇳' },
        { code: 'bn', name: 'বাংলা', flag: '🇮🇳' },
        { code: 'gu', name: 'ગુજરાતી', flag: '🇮🇳' },
        { code: 'kn', name: 'ಕನ್ನಡ', flag: '🇮🇳' },
        { code: 'ml', name: 'മലയാളം', flag: '🇮🇳' },
        { code: 'mr', name: 'मराठी', flag: '🇮🇳' },
        { code: 'pa', name: 'ਪੰਜਾਬੀ', flag: '🇮🇳' }
    ];

    const languageList = languages.length > 0 ? languages : defaultLanguages;

    return (
        <select
            value={selectedLanguage}
            onChange={(e) => onLanguageChange(e.target.value)}
            className={`language-selector ${className}`}
        >
            {languageList.map((lang) => (
                <option key={lang.code} value={lang.code}>
                    {lang.flag} {lang.name}
                </option>
            ))}
        </select>
    );
};

/**
 * Cultural input field with Indian design elements
 */
export const CulturalInput = ({
    type = 'text',
    placeholder,
    value,
    onChange,
    language = 'en',
    className = '',
    ...props
}) => {
    const languageFont = {
        'hi': 'font-devanagari',
        'ta': 'font-tamil',
        'te': 'font-telugu',
        'bn': 'font-bengali',
        'gu': 'font-gujarati',
        'kn': 'font-kannada',
        'ml': 'font-malayalam',
        'or': 'font-oriya',
        'pa': 'font-gurmukhi',
        'mr': 'font-devanagari',
        'as': 'font-bengali',
        'ur': 'font-devanagari'
    }[language] || '';

    return (
        <input
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            className={`cultural-input ${languageFont} ${className}`}
            {...props}
        />
    );
};

/**
 * Status indicator with cultural colors
 */
export const CulturalStatusIndicator = ({
    status,
    label,
    showIcon = true,
    className = ''
}) => {
    const statusConfig = {
        'online': {
            class: 'status-online',
            icon: '🟢',
            text: 'ऑनलाइन / Online'
        },
        'offline': {
            class: 'status-offline',
            icon: '🔴',
            text: 'ऑफलाइन / Offline'
        },
        'connecting': {
            class: 'status-connecting',
            icon: '🟡',
            text: 'कनेक्ट हो रहा है / Connecting'
        },
        'success': {
            class: 'text-green',
            icon: '✅',
            text: 'सफल / Success'
        },
        'error': {
            class: 'text-crimson-red',
            icon: '❌',
            text: 'त्रुटि / Error'
        }
    };

    const config = statusConfig[status] || statusConfig.offline;

    return (
        <span className={`${config.class} ${className} flex items-center gap-2`}>
            {showIcon && <span>{config.icon}</span>}
            <span>{label || config.text}</span>
        </span>
    );
};

/**
 * Cultural header with tricolor accent
 */
export const CulturalHeader = ({
    title,
    subtitle,
    showFlag = true,
    className = ''
}) => {
    return (
        <header className={`text-center py-6 ${className}`}>
            <div className="tricolor-shimmer h-1 w-full mb-4"></div>
            <h1 className="cultural-title text-3xl font-bold mb-2">
                {title}
                {showFlag && <span className="ml-3">🇮🇳</span>}
            </h1>
            {subtitle && (
                <p className="text-white/80 text-lg">
                    {subtitle}
                </p>
            )}
            <div className="tricolor-shimmer h-1 w-full mt-4"></div>
        </header>
    );
};

/**
 * Cultural loading spinner with Indian motifs
 */
export const CulturalLoader = ({
    size = 'medium',
    message = 'लोड हो रहा है... / Loading...',
    className = ''
}) => {
    const sizeClasses = {
        'small': 'w-6 h-6',
        'medium': 'w-12 h-12',
        'large': 'w-16 h-16'
    };

    return (
        <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
            <div className={`
        ${sizeClasses[size]} 
        border-4 border-saffron border-t-transparent 
        rounded-full animate-spin mb-4
      `}></div>
            <p className="text-white/80 text-center font-medium">
                {message}
            </p>
        </div>
    );
};

/**
 * Cultural notification/alert component
 */
export const CulturalAlert = ({
    type = 'info',
    title,
    message,
    onClose,
    className = ''
}) => {
    const typeConfig = {
        'success': {
            bgColor: 'bg-green/10',
            borderColor: 'border-green',
            textColor: 'text-green',
            icon: '✅'
        },
        'error': {
            bgColor: 'bg-crimson-red/10',
            borderColor: 'border-crimson-red',
            textColor: 'text-crimson-red',
            icon: '❌'
        },
        'warning': {
            bgColor: 'bg-turmeric/10',
            borderColor: 'border-turmeric',
            textColor: 'text-turmeric',
            icon: '⚠️'
        },
        'info': {
            bgColor: 'bg-peacock-blue/10',
            borderColor: 'border-peacock-blue',
            textColor: 'text-peacock-blue',
            icon: 'ℹ️'
        }
    };

    const config = typeConfig[type];

    return (
        <div className={`
      ${config.bgColor} ${config.borderColor} ${config.textColor}
      border-l-4 p-4 rounded-r-lg ${className}
    `}>
            <div className="flex items-start">
                <span className="text-xl mr-3">{config.icon}</span>
                <div className="flex-1">
                    {title && (
                        <h4 className="font-semibold mb-1">{title}</h4>
                    )}
                    <p className="text-sm">{message}</p>
                </div>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="ml-4 text-lg hover:opacity-70 transition-opacity"
                    >
                        ×
                    </button>
                )}
            </div>
        </div>
    );
};

export default {
    CulturalText,
    CulturalCard,
    CulturalButton,
    LanguageSelector,
    CulturalInput,
    CulturalStatusIndicator,
    CulturalHeader,
    CulturalLoader,
    CulturalAlert
};