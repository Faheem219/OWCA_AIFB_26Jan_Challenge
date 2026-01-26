import React, { useState } from 'react'
import {
    Box,
    Button,
    Menu,
    MenuItem,
    Typography,
    Divider,
    ListItemIcon,
    ListItemText,
    Chip,
} from '@mui/material'
import { Language, Check, ExpandMore } from '@mui/icons-material'
import { SupportedLanguage } from '../../types'
import { useLanguage } from '../../contexts/LanguageContext'
import useTranslation from '../../hooks/useTranslation'

interface LanguageSelectorDropdownProps {
    variant?: 'button' | 'chip' | 'minimal'
    showFlag?: boolean
    showNativeName?: boolean
    size?: 'small' | 'medium' | 'large'
}

/**
 * Enhanced language selector dropdown component
 */
export const LanguageSelectorDropdown: React.FC<LanguageSelectorDropdownProps> = ({
    variant = 'button',
    showFlag = true,
    showNativeName = true,
    size = 'medium',
}) => {
    const { currentLanguage, changeLanguage, supportedLanguages } = useLanguage()
    const { t } = useTranslation()
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

    const handleClick = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget)
    }

    const handleClose = () => {
        setAnchorEl(null)
    }

    const handleLanguageSelect = (languageCode: SupportedLanguage) => {
        changeLanguage(languageCode)
        handleClose()
    }

    const currentLangInfo = supportedLanguages.find(lang => lang.code === currentLanguage)

    const renderTrigger = () => {
        const content = (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {showFlag && <span>{currentLangInfo?.flag}</span>}
                <span>
                    {showNativeName ? currentLangInfo?.nativeName : currentLangInfo?.name}
                </span>
                <ExpandMore fontSize="small" />
            </Box>
        )

        switch (variant) {
            case 'chip':
                return (
                    <Chip
                        icon={showFlag ? undefined : <Language />}
                        label={content}
                        onClick={handleClick}
                        variant="outlined"
                        size={size === 'large' ? 'medium' : 'small'}
                    />
                )
            case 'minimal':
                return (
                    <Button
                        onClick={handleClick}
                        sx={{
                            minWidth: 'auto',
                            p: 0.5,
                            color: 'text.secondary',
                            '&:hover': { color: 'text.primary' }
                        }}
                    >
                        {content}
                    </Button>
                )
            default:
                return (
                    <Button
                        onClick={handleClick}
                        startIcon={!showFlag ? <Language /> : undefined}
                        endIcon={<ExpandMore />}
                        variant="outlined"
                        size={size}
                    >
                        {showFlag && <span style={{ marginRight: 8 }}>{currentLangInfo?.flag}</span>}
                        {showNativeName ? currentLangInfo?.nativeName : currentLangInfo?.name}
                    </Button>
                )
        }
    }

    return (
        <>
            {renderTrigger()}
            <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleClose}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'left',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'left',
                }}
                PaperProps={{
                    style: {
                        maxHeight: 400,
                        minWidth: 200,
                    },
                }}
            >
                <MenuItem disabled>
                    <Typography variant="subtitle2" color="text.secondary">
                        {t('common.language')}
                    </Typography>
                </MenuItem>
                <Divider />
                {supportedLanguages.map((language) => (
                    <MenuItem
                        key={language.code}
                        onClick={() => handleLanguageSelect(language.code)}
                        selected={language.code === currentLanguage}
                    >
                        <ListItemIcon>
                            {language.code === currentLanguage ? (
                                <Check color="primary" />
                            ) : (
                                <span style={{ width: 24, textAlign: 'center' }}>
                                    {language.flag}
                                </span>
                            )}
                        </ListItemIcon>
                        <ListItemText
                            primary={language.nativeName}
                            secondary={language.name}
                        />
                    </MenuItem>
                ))}
            </Menu>
        </>
    )
}

export default LanguageSelectorDropdown