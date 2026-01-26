import React, { useState, useEffect } from 'react'
import {
    Box,
    TextField,
    FormControl,
    FormLabel,
    IconButton,
    Tooltip,
    Chip,
    Menu,
    MenuItem,
    Typography,
    Divider,
    CircularProgress,
    Alert,
} from '@mui/material'
import {
    Translate,
    Language,
    Add,
    Delete,
} from '@mui/icons-material'
import { MultilingualText, SupportedLanguage } from '../../types'
import { useLanguage } from '../../contexts/LanguageContext'
import useTranslation from '../../hooks/useTranslation'

interface MultilingualTextInputProps {
    label: string
    value: MultilingualText | null
    onChange: (value: MultilingualText) => void
    required?: boolean
    error?: boolean
    helperText?: string
    multiline?: boolean
    rows?: number
    maxRows?: number
    placeholder?: string
    disabled?: boolean
    autoTranslate?: boolean
}

/**
 * Component for inputting multilingual text with translation capabilities
 */
export const MultilingualTextInput: React.FC<MultilingualTextInputProps> = ({
    label,
    value,
    onChange,
    required = false,
    error = false,
    helperText,
    multiline = false,
    rows,
    maxRows,
    placeholder,
    disabled = false,
    autoTranslate = true,
}) => {
    const { currentLanguage, supportedLanguages } = useLanguage()
    const { translateDynamic, createMultilingualText } = useTranslation()

    const [activeLanguage, setActiveLanguage] = useState<SupportedLanguage>(currentLanguage)
    const [languageMenuAnchor, setLanguageMenuAnchor] = useState<null | HTMLElement>(null)
    const [isTranslating, setIsTranslating] = useState(false)
    const [translationError, setTranslationError] = useState<string | null>(null)

    // Initialize value if null
    useEffect(() => {
        if (!value) {
            onChange(createMultilingualText('', currentLanguage))
        }
    }, [value, onChange, createMultilingualText, currentLanguage])

    const handleTextChange = (text: string) => {
        if (!value) return

        const updatedValue: MultilingualText = {
            ...value,
            originalText: activeLanguage === value.originalLanguage ? text : value.originalText,
            translations: {
                ...value.translations,
                ...(activeLanguage !== value.originalLanguage && { [activeLanguage]: text })
            }
        }

        onChange(updatedValue)
    }

    const handleLanguageMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
        setLanguageMenuAnchor(event.currentTarget)
    }

    const handleLanguageMenuClose = () => {
        setLanguageMenuAnchor(null)
    }

    const handleLanguageChange = (languageCode: SupportedLanguage) => {
        setActiveLanguage(languageCode)
        handleLanguageMenuClose()
    }

    const handleAutoTranslate = async (targetLanguage: SupportedLanguage) => {
        if (!value || !value.originalText.trim()) return

        setIsTranslating(true)
        setTranslationError(null)

        try {
            const translatedText = await translateDynamic(value.originalText, targetLanguage)

            const updatedValue: MultilingualText = {
                ...value,
                translations: {
                    ...value.translations,
                    [targetLanguage]: translatedText
                },
                autoTranslated: true
            }

            onChange(updatedValue)
        } catch (error) {
            console.error('Auto-translation failed:', error)
            setTranslationError('Translation failed. Please try again.')
        } finally {
            setIsTranslating(false)
        }
    }

    const handleRemoveTranslation = (languageCode: SupportedLanguage) => {
        if (!value || languageCode === value.originalLanguage) return

        const updatedTranslations = { ...value.translations }
        delete updatedTranslations[languageCode]

        const updatedValue: MultilingualText = {
            ...value,
            translations: updatedTranslations
        }

        onChange(updatedValue)

        // Switch to original language if current active language was removed
        if (activeLanguage === languageCode) {
            setActiveLanguage(value.originalLanguage)
        }
    }

    const getCurrentText = (): string => {
        if (!value) return ''

        if (activeLanguage === value.originalLanguage) {
            return value.originalText
        }

        return value.translations?.[activeLanguage] || ''
    }

    const getAvailableLanguages = () => {
        if (!value) return []

        const languages = [value.originalLanguage]
        if (value.translations) {
            languages.push(...Object.keys(value.translations) as SupportedLanguage[])
        }

        return [...new Set(languages)]
    }

    const getUntranslatedLanguages = () => {
        const available = getAvailableLanguages()
        return supportedLanguages.filter(lang => !available.includes(lang.code))
    }

    const activeLanguageInfo = supportedLanguages.find(lang => lang.code === activeLanguage)
    const availableLanguages = getAvailableLanguages()
    const untranslatedLanguages = getUntranslatedLanguages()

    return (
        <FormControl fullWidth error={error}>
            <FormLabel required={required} sx={{ mb: 1 }}>
                {label}
            </FormLabel>

            {/* Language selector and controls */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Chip
                    icon={<Language />}
                    label={`${activeLanguageInfo?.flag} ${activeLanguageInfo?.name}`}
                    onClick={handleLanguageMenuOpen}
                    onDelete={availableLanguages.length > 1 && activeLanguage !== value?.originalLanguage
                        ? () => handleRemoveTranslation(activeLanguage)
                        : undefined
                    }
                    deleteIcon={<Delete />}
                    variant="outlined"
                    size="small"
                />

                {autoTranslate && untranslatedLanguages.length > 0 && value?.originalText.trim() && (
                    <Tooltip title="Auto-translate to other languages">
                        <IconButton
                            size="small"
                            onClick={() => {
                                untranslatedLanguages.forEach(lang => {
                                    handleAutoTranslate(lang.code)
                                })
                            }}
                            disabled={isTranslating}
                        >
                            {isTranslating ? (
                                <CircularProgress size={16} />
                            ) : (
                                <Translate />
                            )}
                        </IconButton>
                    </Tooltip>
                )}

                <Typography variant="caption" color="text.secondary">
                    {availableLanguages.length} of {supportedLanguages.length} languages
                </Typography>
            </Box>

            {/* Text input */}
            <TextField
                fullWidth
                multiline={multiline}
                rows={rows}
                maxRows={maxRows}
                placeholder={placeholder}
                value={getCurrentText()}
                onChange={(e) => handleTextChange(e.target.value)}
                disabled={disabled}
                error={error}
                helperText={helperText}
                variant="outlined"
            />

            {/* Available translations */}
            {availableLanguages.length > 1 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                    {availableLanguages.map(langCode => {
                        const langInfo = supportedLanguages.find(l => l.code === langCode)
                        const isActive = langCode === activeLanguage
                        const isOriginal = langCode === value?.originalLanguage

                        return (
                            <Chip
                                key={langCode}
                                label={`${langInfo?.flag} ${langInfo?.nativeName}`}
                                size="small"
                                variant={isActive ? "filled" : "outlined"}
                                color={isOriginal ? "primary" : "default"}
                                onClick={() => setActiveLanguage(langCode)}
                                sx={{ fontSize: '0.75rem' }}
                            />
                        )
                    })}
                </Box>
            )}

            {/* Translation error */}
            {translationError && (
                <Alert severity="warning" sx={{ mt: 1 }} onClose={() => setTranslationError(null)}>
                    {translationError}
                </Alert>
            )}

            {/* Language selection menu */}
            <Menu
                anchorEl={languageMenuAnchor}
                open={Boolean(languageMenuAnchor)}
                onClose={handleLanguageMenuClose}
                PaperProps={{
                    style: {
                        maxHeight: 300,
                    },
                }}
            >
                <MenuItem disabled>
                    <Typography variant="subtitle2">Available Languages</Typography>
                </MenuItem>
                {availableLanguages.map(langCode => {
                    const langInfo = supportedLanguages.find(l => l.code === langCode)
                    const isOriginal = langCode === value?.originalLanguage

                    return (
                        <MenuItem
                            key={langCode}
                            onClick={() => handleLanguageChange(langCode)}
                            selected={langCode === activeLanguage}
                        >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <span>{langInfo?.flag}</span>
                                <span>{langInfo?.nativeName}</span>
                                {isOriginal && (
                                    <Chip label="Original" size="small" color="primary" />
                                )}
                            </Box>
                        </MenuItem>
                    )
                })}

                {untranslatedLanguages.length > 0 && (
                    <>
                        <Divider />
                        <MenuItem disabled>
                            <Typography variant="subtitle2">Add Translation</Typography>
                        </MenuItem>
                        {untranslatedLanguages.map(lang => (
                            <MenuItem
                                key={lang.code}
                                onClick={() => handleLanguageChange(lang.code)}
                            >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Add fontSize="small" />
                                    <span>{lang.flag}</span>
                                    <span>{lang.nativeName}</span>
                                </Box>
                            </MenuItem>
                        ))}
                    </>
                )}
            </Menu>
        </FormControl>
    )
}

export default MultilingualTextInput