import React, { useState } from 'react'
import {
    Box,
    TextField,
    Button,
    FormControlLabel,
    Checkbox,
    IconButton,
    InputAdornment,
    Alert,
    Stepper,
    Step,
    StepLabel,
    Typography,
    Divider,
} from '@mui/material'
import { Visibility, VisibilityOff, Google, ArrowBack, ArrowForward } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { RoleSelector } from './RoleSelector'
import { LanguageSelector } from './LanguageSelector'
import { LocationSelector } from './LocationSelector'
import { LoadingSpinner } from '../common/LoadingSpinner'
import { UserRole, SupportedLanguage, LocationData } from '../../types'

export interface RegistrationData {
    email: string
    password: string
    confirmPassword: string
    role: UserRole | ''
    preferredLanguages: SupportedLanguage[]
    phone: string
    businessName: string
    location: LocationData | null
    agreeToTerms: boolean
}

interface RegistrationFormProps {
    onSubmit: (data: RegistrationData) => Promise<void>
    onGoogleRegister?: () => Promise<void>
    isLoading?: boolean
    error?: string | null
    onClearError?: () => void
}

const steps = ['Account Details', 'Role & Preferences', 'Location & Business']

export const RegistrationForm: React.FC<RegistrationFormProps> = ({
    onSubmit,
    onGoogleRegister,
    isLoading = false,
    error = null,
    onClearError,
}) => {
    const { t } = useTranslation()
    const [activeStep, setActiveStep] = useState(0)
    const [formData, setFormData] = useState<RegistrationData>({
        email: '',
        password: '',
        confirmPassword: '',
        role: '',
        preferredLanguages: ['en'],
        phone: '',
        businessName: '',
        location: null,
        agreeToTerms: false,
    })
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

    const validateStep = (step: number) => {
        const errors: Record<string, string> = {}

        switch (step) {
            case 0: // Account Details
                if (!formData.email) {
                    errors.email = t('auth.emailRequired') || 'Email is required'
                } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
                    errors.email = t('auth.emailInvalid') || 'Please enter a valid email address'
                }

                if (!formData.password) {
                    errors.password = t('auth.passwordRequired') || 'Password is required'
                } else if (formData.password.length < 8) {
                    errors.password = t('auth.passwordTooShort') || 'Password must be at least 8 characters long'
                }

                if (!formData.confirmPassword) {
                    errors.confirmPassword = t('auth.confirmPasswordRequired') || 'Please confirm your password'
                } else if (formData.password !== formData.confirmPassword) {
                    errors.confirmPassword = t('auth.passwordsDoNotMatch') || 'Passwords do not match'
                }
                break

            case 1: // Role & Preferences
                if (!formData.role) {
                    errors.role = t('auth.roleRequired') || 'Please select your role'
                }

                if (formData.preferredLanguages.length === 0) {
                    errors.preferredLanguages = t('auth.languageRequired') || 'Please select at least one preferred language'
                }
                break

            case 2: // Location & Business
                if (!formData.location || !formData.location.address) {
                    errors.location = t('auth.locationRequired') || 'Please enter your location'
                }

                if (formData.role === 'VENDOR' && !formData.businessName.trim()) {
                    errors.businessName = t('auth.businessNameRequired') || 'Business name is required for vendors'
                }

                if (!formData.agreeToTerms) {
                    errors.agreeToTerms = t('auth.termsRequired') || 'You must agree to the terms and conditions'
                }
                break
        }

        setValidationErrors(errors)
        return Object.keys(errors).length === 0
    }

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value, checked } = event.target
        setFormData(prev => ({
            ...prev,
            [name]: event.target.type === 'checkbox' ? checked : value,
        }))

        // Clear validation error when user starts typing
        if (validationErrors[name]) {
            setValidationErrors(prev => ({
                ...prev,
                [name]: '',
            }))
        }

        // Clear auth error when user makes changes
        if (error && onClearError) {
            onClearError()
        }
    }

    const handleRoleChange = (role: UserRole) => {
        setFormData(prev => ({ ...prev, role }))
        if (validationErrors.role) {
            setValidationErrors(prev => ({ ...prev, role: '' }))
        }
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

    const handleNext = () => {
        if (validateStep(activeStep)) {
            setActiveStep(prev => prev + 1)
        }
    }

    const handleBack = () => {
        setActiveStep(prev => prev - 1)
    }

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault()

        if (!validateStep(activeStep)) {
            return
        }

        try {
            await onSubmit(formData)
        } catch (error) {
            // Error is handled by parent component
            console.error('Registration failed:', error)
        }
    }

    const renderStepContent = (step: number) => {
        switch (step) {
            case 0:
                return (
                    <Box>
                        <TextField
                            fullWidth
                            name="email"
                            label={t('auth.emailAddress')}
                            type="email"
                            value={formData.email}
                            onChange={handleInputChange}
                            error={!!validationErrors.email}
                            helperText={validationErrors.email}
                            margin="normal"
                            required
                            autoComplete="email"
                            autoFocus
                        />

                        <TextField
                            fullWidth
                            name="password"
                            label={t('auth.password')}
                            type={showPassword ? 'text' : 'password'}
                            value={formData.password}
                            onChange={handleInputChange}
                            error={!!validationErrors.password}
                            helperText={validationErrors.password || t('auth.passwordRequirements')}
                            margin="normal"
                            required
                            autoComplete="new-password"
                            InputProps={{
                                endAdornment: (
                                    <InputAdornment position="end">
                                        <IconButton
                                            onClick={() => setShowPassword(!showPassword)}
                                            edge="end"
                                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                                        >
                                            {showPassword ? <VisibilityOff /> : <Visibility />}
                                        </IconButton>
                                    </InputAdornment>
                                ),
                            }}
                        />

                        <TextField
                            fullWidth
                            name="confirmPassword"
                            label={t('auth.confirmPassword')}
                            type={showConfirmPassword ? 'text' : 'password'}
                            value={formData.confirmPassword}
                            onChange={handleInputChange}
                            error={!!validationErrors.confirmPassword}
                            helperText={validationErrors.confirmPassword}
                            margin="normal"
                            required
                            autoComplete="new-password"
                            InputProps={{
                                endAdornment: (
                                    <InputAdornment position="end">
                                        <IconButton
                                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            edge="end"
                                            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                                        >
                                            {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                                        </IconButton>
                                    </InputAdornment>
                                ),
                            }}
                        />

                        <TextField
                            fullWidth
                            name="phone"
                            label={t('auth.phoneNumber')}
                            type="tel"
                            value={formData.phone}
                            onChange={handleInputChange}
                            margin="normal"
                            placeholder="+91 9876543210"
                            autoComplete="tel"
                        />
                    </Box>
                )

            case 1:
                return (
                    <Box>
                        <RoleSelector
                            selectedRole={formData.role}
                            onChange={handleRoleChange}
                            required
                            error={!!validationErrors.role}
                            helperText={validationErrors.role}
                        />

                        <Box sx={{ mt: 3 }}>
                            <LanguageSelector
                                selectedLanguages={formData.preferredLanguages}
                                onChange={handleLanguagesChange}
                                required
                                error={!!validationErrors.preferredLanguages}
                                helperText={validationErrors.preferredLanguages || t('auth.selectAtLeastOneLanguage')}
                            />
                        </Box>
                    </Box>
                )

            case 2:
                return (
                    <Box>
                        {formData.role === 'VENDOR' && (
                            <TextField
                                fullWidth
                                name="businessName"
                                label={t('auth.businessName')}
                                value={formData.businessName}
                                onChange={handleInputChange}
                                error={!!validationErrors.businessName}
                                helperText={validationErrors.businessName}
                                margin="normal"
                                required
                                placeholder="Enter your business name"
                                sx={{ mb: 3 }}
                            />
                        )}

                        <Box sx={{ mb: 3 }}>
                            <LocationSelector
                                location={formData.location}
                                onChange={handleLocationChange}
                                required
                                error={!!validationErrors.location}
                                helperText={validationErrors.location || t('auth.enterValidLocation')}
                            />
                        </Box>

                        <FormControlLabel
                            control={
                                <Checkbox
                                    name="agreeToTerms"
                                    checked={formData.agreeToTerms}
                                    onChange={handleInputChange}
                                    color="primary"
                                />
                            }
                            label={
                                <Typography variant="body2">
                                    {t('auth.termsAndConditions')} and {t('auth.privacyPolicy')}
                                </Typography>
                            }
                            sx={{ alignItems: 'flex-start', mt: 2 }}
                        />
                        {validationErrors.agreeToTerms && (
                            <Typography variant="body2" color="error" sx={{ mt: 1, ml: 4 }}>
                                {validationErrors.agreeToTerms}
                            </Typography>
                        )}
                    </Box>
                )

            default:
                return null
        }
    }

    if (isLoading) {
        return <LoadingSpinner message={t('auth.creatingAccount') || 'Creating your account...'} />
    }

    return (
        <Box>
            <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
                {steps.map((label) => (
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

            <form onSubmit={handleSubmit}>
                {renderStepContent(activeStep)}

                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                    <Button
                        onClick={handleBack}
                        disabled={activeStep === 0}
                        startIcon={<ArrowBack />}
                    >
                        {t('common.previous') || 'Back'}
                    </Button>

                    {activeStep === steps.length - 1 ? (
                        <Button
                            type="submit"
                            variant="contained"
                            disabled={isLoading}
                            sx={{ px: 4 }}
                        >
                            {t('auth.createAccount')}
                        </Button>
                    ) : (
                        <Button
                            onClick={handleNext}
                            variant="contained"
                            endIcon={<ArrowForward />}
                        >
                            {t('common.next') || 'Next'}
                        </Button>
                    )}
                </Box>
            </form>

            {activeStep === 0 && onGoogleRegister && (
                <>
                    <Divider sx={{ my: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                            {t('auth.orContinueWith')}
                        </Typography>
                    </Divider>

                    <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<Google />}
                        onClick={onGoogleRegister}
                        sx={{ mb: 3, py: 1.5 }}
                        disabled={isLoading}
                    >
                        {t('auth.signInWith')} {t('auth.google')}
                    </Button>
                </>
            )}
        </Box>
    )
}