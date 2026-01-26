import React, { useState, useEffect } from 'react'
import {
    Box,
    Typography,
    IconButton,
    Tooltip,
    CircularProgress,
    Chip,
    Fade,
} from '@mui/material'
import { Translate, Language } from '@mui/icons-material'
import { MultilingualText as MultilingualTextType, SupportedLanguage } from '../../types'
import { useLanguage } from '../../contexts/LanguageContext'
import useTranslation from '../../hooks/useTranslation'

interface MultilingualTextProps {
    content: MultilingualTextType
    variant?: 'body1' | 'body2' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'subtitle1' | 'subtitle2' | 'caption'
    showTranslateButton?: boolean
    showLanguageIndicator?: boolean
    maxLines?: number
    targetLanguage?: SupportedLanguage
    onTranslationUpdate?: (updatedContent: MultilingualTextType) => void
}

/**
 * Component for displaying multilingual text with translation capabilities
 */
export const MultilingualText: React.FC<MultilingualTextProps> = ({
    content,
    variant = 'body1',
    showTranslateButton = true,
    showLanguageIndicator = true,
    maxLines,
    targetLanguage,
    onTranslationUpdate,
}) => {
    const { currentLanguage, supportedLanguages } = useLanguage()
    const { getMultilingualText, translateDynamic } = useTranslation()
    const [isTranslating, setIsTranslating] = useState(false)
    const [displayLanguage, setDisplayLanguage] = useState<SupportedLanguage>(
        targetLanguage || currentLanguage
    )

    const displayText = getMultilingualText(content, displayLanguage)
    const isOriginalLanguage = displayLanguage === content.originalLanguage
    const hasTranslation = content.translations && content.translations[displayLanguage]

    useEffect(() => {
        if (targetLanguage) {
            setDisplayLanguage(targetLanguage)
        } else {
            setDisplayLanguage(currentLanguage)
        }
    }, [targetLanguage, currentLanguage])

    const handleTranslate = async () => {
        if (hasTranslation || isOriginalLanguage) return

        setIsTranslating(true)
        try {
            const translatedText = await translateDynamic(content.originalText, displayLanguage)

            const updatedContent: MultilingualTextType = {
                ...content,
                translations: {
                    ...content.translations,
                    [displayLanguage]: translatedText
                },
                autoTranslated: true
            }

            if (onTranslationUpdate) {
                onTranslationUpdate(updatedContent)
            }
        } catch (error) {
            console.error('Translation failed:', error)
        } finally {
            setIsTranslating(false)
        }
    }

    const getLanguageInfo = (langCode: SupportedLanguage) => {
        return supportedLanguages.find(lang => lang.code === langCode)
    }

    const currentLangInfo = getLanguageInfo(displayLanguage)
    const originalLangInfo = getLanguageInfo(content.originalLanguage)

    return (
        <Box sx={{ position: 'relative' }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <Typography
                    variant={variant}
                    sx={{
                        flex: 1,
                        ...(maxLines && {
                            display: '-webkit-box',
                            WebkitLineClamp: maxLines,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                        }),
                    }}
                >
                    {displayText}
                </Typography>

                {showTranslateButton && !isOriginalLanguage && !hasTranslation && (
                    <Tooltip title={`Translate to ${currentLangInfo?.name}`}>
                        <IconButton
                            size="small"
                            onClick={handleTranslate}
                            disabled={isTranslating}
                            sx={{ mt: -0.5 }}
                        >
                            {isTranslating ? (
                                <CircularProgress size={16} />
                            ) : (
                                <Translate fontSize="small" />
                            )}
                        </IconButton>
                    </Tooltip>
                )}
            </Box>

            {showLanguageIndicator && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    {!isOriginalLanguage && (
                        <Fade in={true}>
                            <Chip
                                icon={<Language />}
                                label={`${currentLangInfo?.flag} ${currentLangInfo?.name}`}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.75rem', height: 20 }}
                            />
                        </Fade>
                    )}

                    {content.autoTranslated && hasTranslation && (
                        <Chip
                            label="Auto-translated"
                            size="small"
                            color="info"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 18 }}
                        />
                    )}

                    {!isOriginalLanguage && originalLangInfo && (
                        <Typography variant="caption" color="text.secondary">
                            Original: {originalLangInfo.flag} {originalLangInfo.name}
                        </Typography>
                    )}
                </Box>
            )}
        </Box>
    )
}

export default MultilingualText