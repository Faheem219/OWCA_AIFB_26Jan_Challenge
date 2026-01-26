import React, { createContext, useContext, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { SupportedLanguage } from '../types'

interface LanguageInfo {
    code: SupportedLanguage
    name: string
    nativeName: string
    flag: string
}

interface LanguageContextType {
    currentLanguage: SupportedLanguage
    supportedLanguages: LanguageInfo[]
    changeLanguage: (languageCode: SupportedLanguage) => void
    isRTL: boolean
    getLanguageName: (code: SupportedLanguage) => string
    translateText: (text: string, targetLanguage?: SupportedLanguage) => Promise<string>
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export { LanguageContext }

const supportedLanguages: LanguageInfo[] = [
    { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
    { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
    { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳' },
    { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳' },
    { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', flag: '🇮🇳' },
    { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', flag: '🇮🇳' },
    { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', flag: '🇮🇳' },
    { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
    { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇮🇳' },
    { code: 'mr', name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳' },
]

// RTL languages (none in our current list, but prepared for future)
const rtlLanguages: SupportedLanguage[] = []

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { i18n } = useTranslation()
    const [currentLanguage, setCurrentLanguage] = useState<SupportedLanguage>('en')

    useEffect(() => {
        // Get language from localStorage or browser preference
        const savedLanguage = localStorage.getItem('preferredLanguage') as SupportedLanguage
        const browserLanguage = navigator.language.split('-')[0] as SupportedLanguage

        const initialLanguage =
            savedLanguage && supportedLanguages.find(lang => lang.code === savedLanguage)
                ? savedLanguage
                : supportedLanguages.find(lang => lang.code === browserLanguage)?.code || 'en'

        setCurrentLanguage(initialLanguage)
        i18n.changeLanguage(initialLanguage)
    }, [i18n])

    const changeLanguage = (languageCode: SupportedLanguage) => {
        setCurrentLanguage(languageCode)
        i18n.changeLanguage(languageCode)
        localStorage.setItem('preferredLanguage', languageCode)

        // Update document direction for RTL languages
        document.dir = rtlLanguages.includes(languageCode) ? 'rtl' : 'ltr'

        // Update document language attribute
        document.documentElement.lang = languageCode
    }

    const isRTL = rtlLanguages.includes(currentLanguage)

    const getLanguageName = (code: SupportedLanguage): string => {
        const language = supportedLanguages.find(lang => lang.code === code)
        return language ? language.name : code
    }

    const translateText = async (text: string, targetLanguage?: SupportedLanguage): Promise<string> => {
        const target = targetLanguage || currentLanguage

        // If target language is the same as source, return original text
        if (target === 'en') {
            return text
        }

        try {
            // TODO: Implement actual translation API call to backend
            // This will integrate with the translation service from task 3.1
            const response = await fetch('/api/v1/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text,
                    source_language: 'auto',
                    target_language: target,
                }),
            })

            if (!response.ok) {
                throw new Error('Translation request failed')
            }

            const data = await response.json()
            return data.translated_text || text
        } catch (error) {
            console.error('Translation error:', error)
            // Return original text on error as fallback
            return text
        }
    }

    const value: LanguageContextType = {
        currentLanguage,
        supportedLanguages,
        changeLanguage,
        isRTL,
        getLanguageName,
        translateText,
    }

    return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export const useLanguage = () => {
    const context = useContext(LanguageContext)
    if (context === undefined) {
        throw new Error('useLanguage must be used within a LanguageProvider')
    }
    return context
}