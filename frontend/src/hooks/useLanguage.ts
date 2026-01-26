import { useContext } from 'react'
import { LanguageContext } from '../contexts/LanguageContext'

// Re-export the useLanguage hook from the context
export const useLanguage = () => {
    const context = useContext(LanguageContext)
    if (context === undefined) {
        throw new Error('useLanguage must be used within a LanguageProvider')
    }
    return context
}