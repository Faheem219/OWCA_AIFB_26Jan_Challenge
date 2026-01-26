import { useTranslation as useI18nTranslation } from 'react-i18next'
import { useLanguage } from '../contexts/LanguageContext'
import { SupportedLanguage, MultilingualText } from '../types'

/**
 * Enhanced translation hook that provides both static and dynamic translation capabilities
 */
export const useTranslation = () => {
    const { t, i18n } = useI18nTranslation()
    const { currentLanguage, translateText } = useLanguage()

    /**
     * Translate static text using i18n keys
     */
    const translate = (key: string, options?: any): string => {
        return t(key, options) as string
    }

    /**
     * Get translated text from multilingual content
     * Falls back to original text if translation not available
     */
    const getMultilingualText = (content: MultilingualText, targetLanguage?: SupportedLanguage): string => {
        const lang = targetLanguage || currentLanguage

        // Return translation if available
        if (content.translations && content.translations[lang]) {
            return content.translations[lang]
        }

        // Fallback to original text
        return content.originalText
    }

    /**
     * Translate dynamic content using the translation service
     */
    const translateDynamic = async (text: string, targetLanguage?: SupportedLanguage): Promise<string> => {
        return await translateText(text, targetLanguage)
    }

    /**
     * Create multilingual text object from a string
     */
    const createMultilingualText = (
        text: string,
        language: SupportedLanguage = currentLanguage,
        translations: Partial<Record<SupportedLanguage, string>> = {}
    ): MultilingualText => {
        return {
            originalLanguage: language,
            originalText: text,
            translations: translations as Record<SupportedLanguage, string>,
            autoTranslated: false
        }
    }

    /**
     * Format text with interpolation
     */
    const formatText = (template: string, values: Record<string, any>): string => {
        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return values[key] !== undefined ? String(values[key]) : match
        })
    }

    return {
        t: translate,
        currentLanguage,
        changeLanguage: i18n.changeLanguage,
        getMultilingualText,
        translateDynamic,
        createMultilingualText,
        formatText,
        isReady: i18n.isInitialized
    }
}

export default useTranslation