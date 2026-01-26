import React from 'react'
import {
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Chip,
    Box,
    SelectChangeEvent,
    OutlinedInput,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { SupportedLanguage } from '../../types'
import { useLanguage } from '../../contexts/LanguageContext'

interface LanguageSelectorProps {
    selectedLanguages: SupportedLanguage[]
    onChange: (languages: SupportedLanguage[]) => void
    multiple?: boolean
    required?: boolean
    error?: boolean
    helperText?: string
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
    selectedLanguages,
    onChange,
    multiple = true,
    required = false,
    error = false,
    helperText,
}) => {
    const { t } = useTranslation()
    const { supportedLanguages } = useLanguage()

    const handleChange = (event: SelectChangeEvent<SupportedLanguage | SupportedLanguage[]>) => {
        const value = event.target.value
        if (multiple) {
            onChange(typeof value === 'string' ? [value as SupportedLanguage] : value as SupportedLanguage[])
        } else {
            onChange([value as SupportedLanguage])
        }
    }

    const renderValue = (selected: SupportedLanguage | SupportedLanguage[]) => {
        const languages = Array.isArray(selected) ? selected : [selected]

        if (multiple) {
            return (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {languages.map((lang) => {
                        const langInfo = supportedLanguages.find(l => l.code === lang)
                        return (
                            <Chip
                                key={lang}
                                label={`${langInfo?.flag} ${langInfo?.nativeName}`}
                                size="small"
                                variant="outlined"
                            />
                        )
                    })}
                </Box>
            )
        } else {
            const langInfo = supportedLanguages.find(l => l.code === languages[0])
            return `${langInfo?.flag} ${langInfo?.nativeName}`
        }
    }

    return (
        <FormControl fullWidth required={required} error={error}>
            <InputLabel id="language-selector-label">
                {multiple ? t('profile.languages') : t('common.language')}
            </InputLabel>
            <Select
                labelId="language-selector-label"
                multiple={multiple}
                value={multiple ? selectedLanguages : selectedLanguages[0] || ''}
                onChange={handleChange}
                input={<OutlinedInput label={multiple ? t('profile.languages') : t('common.language')} />}
                renderValue={renderValue}
                MenuProps={{
                    PaperProps: {
                        style: {
                            maxHeight: 300,
                        },
                    },
                }}
            >
                {supportedLanguages.map((language) => (
                    <MenuItem key={language.code} value={language.code}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <span>{language.flag}</span>
                            <span>{language.nativeName}</span>
                            <span style={{ color: 'text.secondary', fontSize: '0.875rem' }}>
                                ({language.name})
                            </span>
                        </Box>
                    </MenuItem>
                ))}
            </Select>
            {helperText && (
                <Box sx={{ mt: 1, fontSize: '0.75rem', color: error ? 'error.main' : 'text.secondary' }}>
                    {helperText}
                </Box>
            )}
        </FormControl>
    )
}