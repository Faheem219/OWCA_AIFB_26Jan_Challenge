import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import Backend from 'i18next-http-backend'

// Import translation files
import enTranslations from './locales/en.json'
import hiTranslations from './locales/hi.json'
import taTranslations from './locales/ta.json'
import teTranslations from './locales/te.json'
import knTranslations from './locales/kn.json'
import mlTranslations from './locales/ml.json'
import guTranslations from './locales/gu.json'
import paTranslations from './locales/pa.json'
import bnTranslations from './locales/bn.json'
import mrTranslations from './locales/mr.json'

const resources = {
    en: {
        translation: enTranslations,
    },
    hi: {
        translation: hiTranslations,
    },
    ta: {
        translation: taTranslations,
    },
    te: {
        translation: teTranslations,
    },
    kn: {
        translation: knTranslations,
    },
    ml: {
        translation: mlTranslations,
    },
    gu: {
        translation: guTranslations,
    },
    pa: {
        translation: paTranslations,
    },
    bn: {
        translation: bnTranslations,
    },
    mr: {
        translation: mrTranslations,
    },
}

i18n
    .use(Backend)
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources,
        fallbackLng: 'en',
        debug: process.env.NODE_ENV === 'development',

        interpolation: {
            escapeValue: false, // React already escapes values
        },

        detection: {
            order: ['localStorage', 'navigator', 'htmlTag'],
            caches: ['localStorage'],
        },

        backend: {
            loadPath: '/locales/{{lng}}/{{ns}}.json',
        },

        react: {
            useSuspense: false,
        },
    })

export default i18n