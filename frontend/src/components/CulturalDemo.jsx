import React, { useState } from 'react';
import {
    CulturalText,
    CulturalCard,
    CulturalButton,
    LanguageSelector,
    CulturalInput,
    CulturalStatusIndicator,
    CulturalHeader,
    CulturalLoader,
    CulturalAlert
} from './CulturalElements';

/**
 * Demo component showcasing all cultural design elements
 * Implements Requirements 12.1, 12.2, and 9.6
 */
const CulturalDemo = () => {
    const [selectedLanguage, setSelectedLanguage] = useState('hi');
    const [inputValue, setInputValue] = useState('');
    const [showAlert, setShowAlert] = useState(false);
    const [showLoader, setShowLoader] = useState(false);

    const demoTexts = {
        'hi': {
            welcome: 'स्वागत है',
            description: 'यह भारतीय सांस्कृतिक डिज़ाइन सिस्टम का प्रदर्शन है',
            placeholder: 'अपना संदेश यहाँ लिखें',
            button: 'भेजें',
            status: 'ऑनलाइन'
        },
        'en': {
            welcome: 'Welcome',
            description: 'This is a demonstration of the Indian Cultural Design System',
            placeholder: 'Type your message here',
            button: 'Send',
            status: 'Online'
        },
        'ta': {
            welcome: 'வரவேற்கிறோம்',
            description: 'இது இந்திய கலாச்சார வடிவமைப்பு அமைப்பின் ஆர்ப்பாட்டம்',
            placeholder: 'உங்கள் செய்தியை இங்கே தட்டச்சு செய்யுங்கள்',
            button: 'அனுப்பு',
            status: 'ஆன்லைன்'
        },
        'te': {
            welcome: 'స్వాగతం',
            description: 'ఇది భారతీయ సాంస్కృతిక డిజైన్ సిస్టమ్ యొక్క ప్రదర్శన',
            placeholder: 'మీ సందేశాన్ని ఇక్కడ టైప్ చేయండి',
            button: 'పంపు',
            status: 'ఆన్‌లైన్'
        },
        'bn': {
            welcome: 'স্বাগতম',
            description: 'এটি ভারতীয় সাংস্কৃতিক ডিজাইন সিস্টেমের একটি প্রদর্শনী',
            placeholder: 'এখানে আপনার বার্তা টাইপ করুন',
            button: 'পাঠান',
            status: 'অনলাইন'
        }
    };

    const currentTexts = demoTexts[selectedLanguage] || demoTexts['en'];

    const handleSubmit = () => {
        if (inputValue.trim()) {
            setShowLoader(true);
            setTimeout(() => {
                setShowLoader(false);
                setShowAlert(true);
                setInputValue('');
            }, 2000);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-saffron/20 via-white to-green/20 p-4">
            <CulturalHeader
                title="सांस्कृतिक डिज़ाइन सिस्टम / Cultural Design System"
                subtitle="Viksit Bharat - Digital India with Cultural Authenticity"
                showFlag={true}
            />

            <div className="max-w-4xl mx-auto space-y-6">
                {/* Language Selection Section */}
                <CulturalCard variant="elevated">
                    <div className="text-center mb-4">
                        <CulturalText language={selectedLanguage} variant="subheading" className="mb-2">
                            भाषा चुनें / Choose Language
                        </CulturalText>
                        <LanguageSelector
                            selectedLanguage={selectedLanguage}
                            onLanguageChange={setSelectedLanguage}
                            className="mx-auto"
                        />
                    </div>
                </CulturalCard>

                {/* Welcome Section */}
                <CulturalCard showTricolorBorder={true}>
                    <div className="text-center">
                        <CulturalText language={selectedLanguage} variant="heading" className="mb-4 cultural-heading">
                            {currentTexts.welcome}
                        </CulturalText>
                        <CulturalText language={selectedLanguage} variant="body" className="text-gray-700">
                            {currentTexts.description}
                        </CulturalText>
                    </div>
                </CulturalCard>

                {/* Interactive Demo Section */}
                <CulturalCard>
                    <div className="space-y-4">
                        <CulturalText language={selectedLanguage} variant="subheading" className="cultural-subheading">
                            Interactive Demo / इंटरैक्टिव डेमो
                        </CulturalText>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <CulturalInput
                                    language={selectedLanguage}
                                    placeholder={currentTexts.placeholder}
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    className="w-full"
                                />
                            </div>
                            <div className="flex items-end">
                                <CulturalButton
                                    variant="primary"
                                    onClick={handleSubmit}
                                    disabled={!inputValue.trim() || showLoader}
                                    showPulse={inputValue.trim() && !showLoader}
                                    className="w-full md:w-auto"
                                >
                                    {showLoader ? '⏳' : '📤'} {currentTexts.button}
                                </CulturalButton>
                            </div>
                        </div>

                        <div className="flex justify-between items-center">
                            <CulturalStatusIndicator
                                status="online"
                                label={currentTexts.status}
                            />
                            <div className="text-sm text-gray-600">
                                Selected: {selectedLanguage.toUpperCase()}
                            </div>
                        </div>
                    </div>
                </CulturalCard>

                {/* Component Showcase */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Button Variants */}
                    <CulturalCard>
                        <CulturalText variant="subheading" className="mb-4">
                            Button Variants
                        </CulturalText>
                        <div className="space-y-2">
                            <CulturalButton variant="primary" size="small" className="w-full">
                                Primary
                            </CulturalButton>
                            <CulturalButton variant="secondary" size="small" className="w-full">
                                Secondary
                            </CulturalButton>
                            <CulturalButton variant="outline" size="small" className="w-full">
                                Outline
                            </CulturalButton>
                            <CulturalButton variant="success" size="small" className="w-full">
                                Success
                            </CulturalButton>
                        </div>
                    </CulturalCard>

                    {/* Status Indicators */}
                    <CulturalCard>
                        <CulturalText variant="subheading" className="mb-4">
                            Status Indicators
                        </CulturalText>
                        <div className="space-y-2">
                            <CulturalStatusIndicator status="online" />
                            <CulturalStatusIndicator status="offline" />
                            <CulturalStatusIndicator status="connecting" />
                            <CulturalStatusIndicator status="success" />
                            <CulturalStatusIndicator status="error" />
                        </div>
                    </CulturalCard>

                    {/* Typography Showcase */}
                    <CulturalCard>
                        <CulturalText variant="subheading" className="mb-4">
                            Typography
                        </CulturalText>
                        <div className="space-y-2">
                            <CulturalText language="hi" variant="heading" className="text-sm">
                                हिंदी - Hindi
                            </CulturalText>
                            <CulturalText language="ta" variant="body" className="text-sm">
                                தமிழ் - Tamil
                            </CulturalText>
                            <CulturalText language="te" variant="body" className="text-sm">
                                తెలుగు - Telugu
                            </CulturalText>
                            <CulturalText language="bn" variant="body" className="text-sm">
                                বাংলা - Bengali
                            </CulturalText>
                            <CulturalText language="gu" variant="body" className="text-sm">
                                ગુજરાતી - Gujarati
                            </CulturalText>
                        </div>
                    </CulturalCard>
                </div>

                {/* Cultural Patterns Demo */}
                <CulturalCard>
                    <CulturalText variant="subheading" className="mb-4 cultural-subheading">
                        Cultural Patterns / सांस्कृतिक पैटर्न
                    </CulturalText>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="h-20 mandala-pattern border-2 border-golden-yellow rounded-lg flex items-center justify-center">
                            <span className="bg-white/80 px-2 py-1 rounded text-sm font-semibold">
                                Mandala Pattern
                            </span>
                        </div>
                        <div className="h-20 geometric-pattern border-2 border-saffron rounded-lg flex items-center justify-center">
                            <span className="bg-white/80 px-2 py-1 rounded text-sm font-semibold">
                                Geometric Pattern
                            </span>
                        </div>
                        <div className="h-20 lotus-pattern border-2 border-peacock-blue rounded-lg flex items-center justify-center">
                            <span className="bg-white/80 px-2 py-1 rounded text-sm font-semibold">
                                Lotus Pattern
                            </span>
                        </div>
                    </div>
                </CulturalCard>

                {/* Loader Demo */}
                {showLoader && (
                    <CulturalCard>
                        <CulturalLoader
                            size="medium"
                            message={selectedLanguage === 'hi' ? 'संदेश भेजा जा रहा है...' : 'Sending message...'}
                        />
                    </CulturalCard>
                )}

                {/* Alert Demo */}
                {showAlert && (
                    <CulturalAlert
                        type="success"
                        title={selectedLanguage === 'hi' ? 'सफलता!' : 'Success!'}
                        message={selectedLanguage === 'hi' ? 'आपका संदेश सफलतापूर्वक भेजा गया।' : 'Your message was sent successfully.'}
                        onClose={() => setShowAlert(false)}
                    />
                )}

                {/* Cultural Symbols */}
                <CulturalCard>
                    <CulturalText variant="subheading" className="mb-4 cultural-subheading">
                        Cultural Symbols / सांस्कृतिक प्रतीक
                    </CulturalText>
                    <div className="text-center text-4xl space-x-4">
                        <span title="Indian Flag">🇮🇳</span>
                        <span title="Lotus">🪷</span>
                        <span title="Peacock">🦚</span>
                        <span title="Elephant">🐘</span>
                        <span title="Tiger">🐅</span>
                        <span title="Temple">🛕</span>
                        <span title="Diya">🪔</span>
                        <span title="Wheel">☸️</span>
                    </div>
                </CulturalCard>

                {/* Footer */}
                <div className="text-center py-8">
                    <div className="tricolor-shimmer h-2 w-full mb-4 rounded"></div>
                    <CulturalText variant="body" className="text-gray-600">
                        Made with ❤️ for Viksit Bharat 2047
                    </CulturalText>
                    <CulturalText language="hi" variant="caption" className="text-gray-500 mt-2">
                        विकसित भारत के लिए प्रेम से बनाया गया
                    </CulturalText>
                    <div className="tricolor-shimmer h-2 w-full mt-4 rounded"></div>
                </div>
            </div>
        </div>
    );
};

export default CulturalDemo;