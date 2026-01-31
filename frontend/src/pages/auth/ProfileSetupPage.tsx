import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
    Container,
    Paper,
    Box,
    Typography,
    Button,
    Alert,
    Stepper,
    Step,
    StepLabel,
    Grid,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    FormHelperText,
    TextField,
} from '@mui/material'
import { CheckCircle, ArrowBack, ArrowForward } from '@mui/icons-material'
import { useAuth } from '../../hooks/useAuth'
import { LanguageSelector } from '../../components/auth/LanguageSelector'
import { LocationSelector } from '../../components/auth/LocationSelector'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { profileService } from '../../services/profileService'
import { SupportedLanguage, LocationData } from '../../types'

const steps = ['Languages', 'Location', 'Business Details']

// Valid business types matching backend enum
const businessTypeOptions = [
    { value: 'individual', label: 'Individual Seller' },
    { value: 'small_business', label: 'Small Business' },
    { value: 'cooperative', label: 'Cooperative' },
    { value: 'wholesaler', label: 'Wholesaler' },
    { value: 'retailer', label: 'Retailer' },
]

export const ProfileSetupPage: React.FC = () => {
    const navigate = useNavigate()
    const { user, updateUser } = useAuth()

    const [activeStep, setActiveStep] = useState(0)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)

    const [formData, setFormData] = useState({
        preferredLanguages: user?.preferredLanguages || ['en'],
        location: user?.location || null,
        businessName: '',
        businessType: '',
        phone: '',
    })

    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

    if (!user) {
        navigate('/login')
        return null
    }

    const validateStep = (step: number) => {
        const errors: Record<string, string> = {}

        switch (step) {
            case 0: // Languages
                if (formData.preferredLanguages.length === 0) {
                    errors.preferredLanguages = 'Please select at least one preferred language'
                }
                break

            case 1: // Location
                if (!formData.location || !formData.location.address) {
                    errors.location = 'Please enter your location'
                }
                break

            case 2: // Business Details (for vendors)
                if (user.role === 'VENDOR') {
                    if (!formData.businessName.trim()) {
                        errors.businessName = 'Business name is required'
                    }
                    if (!formData.businessType.trim()) {
                        errors.businessType = 'Business type is required'
                    }
                }
                break
        }

        setValidationErrors(errors)
        return Object.keys(errors).length === 0
    }

    const handleLanguagesChange = (languages: SupportedLanguage[]) => {
        setFormData(prev => ({ ...prev, preferredLanguages: languages }))
        if (validationErrors.preferredLanguages) {
            setValidationErrors(prev => ({ ...prev, preferredLanguages: '' }))
        }
    }

    const handleLocationChange = (location: LocationData) => {
        setFormData(prev => ({ ...prev, location }))
        if (validationErrors.location) {
            setValidationErrors(prev => ({ ...prev, location: '' }))
        }
    }

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = event.target
        setFormData(prev => ({ ...prev, [name]: value }))

        if (validationErrors[name]) {
            setValidationErrors(prev => ({ ...prev, [name]: '' }))
        }
    }

    const handleNext = () => {
        if (validateStep(activeStep)) {
            setActiveStep(prev => prev + 1)
        }
    }

    const handleBack = () => {
        setActiveStep(prev => prev - 1)
    }

    const handleComplete = async () => {
        if (!validateStep(activeStep)) {
            return
        }

        setIsLoading(true)
        setError(null)

        try {
            const updateData: any = {
                preferred_languages: formData.preferredLanguages,
                location: formData.location,
                phone: formData.phone || undefined,
            }

            if (user.role === 'VENDOR') {
                updateData.business_name = formData.businessName
                updateData.business_type = formData.businessType
            }

            const updatedUser = await profileService.updateProfile(updateData)
            updateUser(updatedUser)

            setSuccess('Profile setup completed successfully!')

            // Redirect to dashboard after a short delay
            setTimeout(() => {
                navigate('/dashboard', { replace: true })
            }, 2000)
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to update profile')
        } finally {
            setIsLoading(false)
        }
    }

    const renderStepContent = (step: number) => {
        switch (step) {
            case 0:
                return (
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            Select Your Preferred Languages
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                            Choose the languages you're comfortable with. This will help us provide better translations and connect you with the right people.
                        </Typography>
                        <LanguageSelector
                            selectedLanguages={formData.preferredLanguages}
                            onChange={handleLanguagesChange}
                            required
                            error={!!validationErrors.preferredLanguages}
                            helperText={validationErrors.preferredLanguages}
                        />
                    </Box>
                )

            case 1:
                return (
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            Set Your Location
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                            Your location helps us show you nearby {user.role === 'VENDOR' ? 'buyers' : 'vendors'} and relevant market information.
                        </Typography>
                        <LocationSelector
                            location={formData.location}
                            onChange={handleLocationChange}
                            required
                            error={!!validationErrors.location}
                            helperText={validationErrors.location}
                        />
                    </Box>
                )

            case 2:
                if (user.role === 'VENDOR') {
                    return (
                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Business Information
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                Tell us about your business to help buyers find and trust your products.
                            </Typography>
                            <Grid container spacing={3}>
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        name="businessName"
                                        label="Business Name"
                                        value={formData.businessName}
                                        onChange={handleInputChange}
                                        error={!!validationErrors.businessName}
                                        helperText={validationErrors.businessName}
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <FormControl fullWidth error={!!validationErrors.businessType}>
                                        <InputLabel id="business-type-label">Business Type</InputLabel>
                                        <Select
                                            labelId="business-type-label"
                                            name="businessType"
                                            value={formData.businessType}
                                            onChange={(e) => {
                                                setFormData(prev => ({ ...prev, businessType: e.target.value as string }))
                                                if (validationErrors.businessType) {
                                                    setValidationErrors(prev => ({ ...prev, businessType: '' }))
                                                }
                                            }}
                                            label="Business Type"
                                        >
                                            {businessTypeOptions.map((option) => (
                                                <MenuItem key={option.value} value={option.value}>
                                                    {option.label}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                        {validationErrors.businessType && (
                                            <FormHelperText>{validationErrors.businessType}</FormHelperText>
                                        )}
                                    </FormControl>
                                </Grid>
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        name="phone"
                                        label="Phone Number (Optional)"
                                        type="tel"
                                        value={formData.phone}
                                        onChange={handleInputChange}
                                    />
                                </Grid>
                            </Grid>
                        </Box>
                    )
                } else {
                    return (
                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Complete Your Profile
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                Your profile is almost ready! You can add more details later from your profile page.
                            </Typography>
                            <Grid container spacing={3}>
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        name="phone"
                                        label="Phone Number (Optional)"
                                        type="tel"
                                        value={formData.phone}
                                        onChange={handleInputChange}
                                    />
                                </Grid>
                            </Grid>
                        </Box>
                    )
                }

            default:
                return null
        }
    }

    if (isLoading) {
        return (
            <Container maxWidth="sm">
                <Box
                    sx={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        minHeight: '60vh',
                    }}
                >
                    <LoadingSpinner message="Setting up your profile..." />
                </Box>
            </Container>
        )
    }

    if (success) {
        return (
            <Container maxWidth="sm">
                <Box
                    sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minHeight: '60vh',
                        textAlign: 'center',
                    }}
                >
                    <CheckCircle color="success" sx={{ fontSize: 64, mb: 2 }} />
                    <Typography variant="h4" gutterBottom>
                        Welcome to the Marketplace!
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                        Your profile has been set up successfully. Redirecting to your dashboard...
                    </Typography>
                </Box>
            </Container>
        )
    }

    const maxSteps = user.role === 'VENDOR' ? 3 : 2

    return (
        <Container maxWidth="md">
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '80vh',
                    py: 4,
                }}
            >
                <Paper
                    elevation={3}
                    sx={{
                        p: 4,
                        width: '100%',
                        maxWidth: 600,
                        borderRadius: 2,
                    }}
                >
                    <Box sx={{ textAlign: 'center', mb: 4 }}>
                        <Typography variant="h4" gutterBottom fontWeight="bold">
                            Complete Your Profile
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Let's set up your profile to get you started in the marketplace
                        </Typography>
                    </Box>

                    <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
                        {steps.slice(0, maxSteps).map((label) => (
                            <Step key={label}>
                                <StepLabel>{label}</StepLabel>
                            </Step>
                        ))}
                    </Stepper>

                    {error && (
                        <Alert severity="error" sx={{ mb: 3 }}>
                            {error}
                        </Alert>
                    )}

                    {renderStepContent(activeStep)}

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                        <Button
                            onClick={handleBack}
                            disabled={activeStep === 0}
                            startIcon={<ArrowBack />}
                        >
                            Back
                        </Button>

                        {activeStep === maxSteps - 1 ? (
                            <Button
                                onClick={handleComplete}
                                variant="contained"
                                disabled={isLoading}
                                sx={{ px: 4 }}
                            >
                                Complete Setup
                            </Button>
                        ) : (
                            <Button
                                onClick={handleNext}
                                variant="contained"
                                endIcon={<ArrowForward />}
                            >
                                Next
                            </Button>
                        )}
                    </Box>
                </Paper>
            </Box>
        </Container>
    )
}