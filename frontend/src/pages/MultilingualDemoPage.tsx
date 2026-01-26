import React, { useState } from 'react'
import {
    Container,
    Typography,
    Box,
    Paper,
    Grid,
    Divider,
    Card,
    CardContent,
    Button,
} from '@mui/material'
import { Language, Translate } from '@mui/icons-material'
import { MultilingualText } from '../components/common/MultilingualText'
import { MultilingualTextInput } from '../components/common/MultilingualTextInput'
import { LanguageSelectorDropdown } from '../components/common/LanguageSelectorDropdown'
import { MultilingualText as MultilingualTextType } from '../types'
import useTranslation from '../hooks/useTranslation'

/**
 * Demo page showcasing the multilingual UI framework
 */
export const MultilingualDemoPage: React.FC = () => {
    const { t, currentLanguage, createMultilingualText } = useTranslation()

    const [demoText] = useState<MultilingualTextType>(
        createMultilingualText(
            'Welcome to the Multilingual Mandi Marketplace!',
            'en',
            {
                hi: 'बहुभाषी मंडी मार्केटप्लेस में आपका स्वागत है!',
                ta: 'பன்மொழி மண்டி சந்தையில் உங்களை வரவேற்கிறோம்!',
                te: 'బహుభాషా మండి మార్కెట్‌ప్లేస్‌కు స్వాగతం!',
            }
        )
    )

    const [userInput, setUserInput] = useState<MultilingualTextType>(
        createMultilingualText('', currentLanguage)
    )

    const sampleProducts = [
        createMultilingualText(
            'Fresh Organic Tomatoes',
            'en',
            {
                hi: 'ताज़े जैविक टमाटर',
                ta: 'புதிய இயற்கை தக்காளி',
                te: 'తాజా సేంద్రీయ టమోటాలు',
            }
        ),
        createMultilingualText(
            'Premium Basmati Rice',
            'en',
            {
                hi: 'प्रीमियम बासमती चावल',
                ta: 'பிரீமியம் பாஸ்மதி அரிசி',
                te: 'ప్రీమియం బాస్మతి బియ్యం',
            }
        ),
        createMultilingualText(
            'Seasonal Mangoes',
            'en',
            {
                hi: 'मौसमी आम',
                ta: 'பருவகால மாம்பழம்',
                te: 'కాలానుగుణ మామిడిపండ్లు',
            }
        ),
    ]

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            <Box sx={{ mb: 4, textAlign: 'center' }}>
                <Typography variant="h3" component="h1" gutterBottom>
                    {t('common.language')} Framework Demo
                </Typography>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                    Showcasing multilingual UI components for the Mandi Marketplace
                </Typography>

                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
                    <LanguageSelectorDropdown variant="button" />
                    <LanguageSelectorDropdown variant="chip" />
                    <LanguageSelectorDropdown variant="minimal" />
                </Box>
            </Box>

            <Grid container spacing={4}>
                {/* Multilingual Text Display */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h5" gutterBottom>
                                <Language sx={{ mr: 1, verticalAlign: 'middle' }} />
                                Multilingual Text Display
                            </Typography>
                            <Divider sx={{ mb: 2 }} />

                            <Box sx={{ mb: 3 }}>
                                <Typography variant="h6" gutterBottom>
                                    Welcome Message:
                                </Typography>
                                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                                    <MultilingualText
                                        content={demoText}
                                        variant="h6"
                                        showTranslateButton={true}
                                        showLanguageIndicator={true}
                                    />
                                </Paper>
                            </Box>

                            <Box>
                                <Typography variant="h6" gutterBottom>
                                    Sample Products:
                                </Typography>
                                {sampleProducts.map((product, index) => (
                                    <Paper key={index} sx={{ p: 2, mb: 1, bgcolor: 'grey.50' }}>
                                        <MultilingualText
                                            content={product}
                                            variant="body1"
                                            showTranslateButton={true}
                                            showLanguageIndicator={false}
                                        />
                                    </Paper>
                                ))}
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Multilingual Text Input */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h5" gutterBottom>
                                <Translate sx={{ mr: 1, verticalAlign: 'middle' }} />
                                Multilingual Text Input
                            </Typography>
                            <Divider sx={{ mb: 2 }} />

                            <Box sx={{ mb: 3 }}>
                                <MultilingualTextInput
                                    label="Product Description"
                                    value={userInput}
                                    onChange={setUserInput}
                                    multiline
                                    rows={4}
                                    placeholder="Enter product description in any language..."
                                    autoTranslate={true}
                                />
                            </Box>

                            {userInput.originalText && (
                                <Box>
                                    <Typography variant="h6" gutterBottom>
                                        Preview:
                                    </Typography>
                                    <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                                        <MultilingualText
                                            content={userInput}
                                            variant="body1"
                                            showTranslateButton={true}
                                            showLanguageIndicator={true}
                                        />
                                    </Paper>
                                </Box>
                            )}
                        </CardContent>
                    </Card>
                </Grid>

                {/* Language Features */}
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography variant="h5" gutterBottom>
                                Supported Languages & Features
                            </Typography>
                            <Divider sx={{ mb: 2 }} />

                            <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                    <Typography variant="h6" gutterBottom>
                                        Supported Languages (10):
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                        {[
                                            { code: 'en', name: 'English', flag: '🇺🇸' },
                                            { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
                                            { code: 'ta', name: 'Tamil', flag: '🇮🇳' },
                                            { code: 'te', name: 'Telugu', flag: '🇮🇳' },
                                            { code: 'kn', name: 'Kannada', flag: '🇮🇳' },
                                            { code: 'ml', name: 'Malayalam', flag: '🇮🇳' },
                                            { code: 'gu', name: 'Gujarati', flag: '🇮🇳' },
                                            { code: 'pa', name: 'Punjabi', flag: '🇮🇳' },
                                            { code: 'bn', name: 'Bengali', flag: '🇮🇳' },
                                            { code: 'mr', name: 'Marathi', flag: '🇮🇳' },
                                        ].map((lang) => (
                                            <Button
                                                key={lang.code}
                                                variant="outlined"
                                                size="small"
                                                startIcon={<span>{lang.flag}</span>}
                                            >
                                                {lang.name}
                                            </Button>
                                        ))}
                                    </Box>
                                </Grid>

                                <Grid item xs={12} md={6}>
                                    <Typography variant="h6" gutterBottom>
                                        Framework Features:
                                    </Typography>
                                    <Box component="ul" sx={{ pl: 2 }}>
                                        <li>Static UI text translation (i18n)</li>
                                        <li>Dynamic content translation</li>
                                        <li>Multilingual text input components</li>
                                        <li>Auto-translation capabilities</li>
                                        <li>Language detection and fallback</li>
                                        <li>Cultural sensitivity preservation</li>
                                        <li>Responsive language selectors</li>
                                        <li>Translation caching</li>
                                        <li>Offline language support</li>
                                        <li>Accessibility compliance</li>
                                    </Box>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            <Box sx={{ mt: 4, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                    Current Language: <strong>{currentLanguage.toUpperCase()}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Framework Status: <strong>Ready for Production</strong>
                </Typography>
            </Box>
        </Container>
    )
}

export default MultilingualDemoPage