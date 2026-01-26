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
    Divider,
    Typography,
} from '@mui/material'
import { Visibility, VisibilityOff, Google } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface LoginFormProps {
    onSubmit: (email: string, password: string, rememberMe: boolean) => Promise<void>
    onGoogleLogin?: () => Promise<void>
    onAadhaarLogin?: () => Promise<void>
    isLoading?: boolean
    error?: string | null
    onClearError?: () => void
}

export const LoginForm: React.FC<LoginFormProps> = ({
    onSubmit,
    onGoogleLogin,
    onAadhaarLogin,
    isLoading = false,
    error = null,
    onClearError,
}) => {
    const { t } = useTranslation()
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        rememberMe: false,
    })
    const [showPassword, setShowPassword] = useState(false)
    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

    const validateForm = () => {
        const errors: Record<string, string> = {}

        if (!formData.email) {
            errors.email = t('auth.emailRequired') || 'Email is required'
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            errors.email = t('auth.emailInvalid') || 'Please enter a valid email address'
        }

        if (!formData.password) {
            errors.password = t('auth.passwordRequired') || 'Password is required'
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

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault()

        if (!validateForm()) {
            return
        }

        try {
            await onSubmit(formData.email, formData.password, formData.rememberMe)
        } catch (error) {
            // Error is handled by parent component
            console.error('Login failed:', error)
        }
    }

    if (isLoading) {
        return <LoadingSpinner message={t('auth.loggingIn')} />
    }

    return (
        <Box>
            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            <form onSubmit={handleSubmit}>
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
                    helperText={validationErrors.password}
                    margin="normal"
                    required
                    autoComplete="current-password"
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

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2, mb: 3 }}>
                    <FormControlLabel
                        control={
                            <Checkbox
                                name="rememberMe"
                                checked={formData.rememberMe}
                                onChange={handleInputChange}
                                color="primary"
                            />
                        }
                        label={t('auth.rememberMe')}
                    />
                </Box>

                <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    size="large"
                    disabled={isLoading}
                    sx={{ mb: 3, py: 1.5 }}
                >
                    {t('auth.login')}
                </Button>
            </form>

            {(onGoogleLogin || onAadhaarLogin) && (
                <>
                    <Divider sx={{ my: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                            {t('auth.orContinueWith')}
                        </Typography>
                    </Divider>

                    {onGoogleLogin && (
                        <Button
                            fullWidth
                            variant="outlined"
                            startIcon={<Google />}
                            onClick={onGoogleLogin}
                            sx={{ mb: 2, py: 1.5 }}
                            disabled={isLoading}
                        >
                            {t('auth.signInWith')} {t('auth.google')}
                        </Button>
                    )}

                    {onAadhaarLogin && (
                        <Button
                            fullWidth
                            variant="outlined"
                            onClick={onAadhaarLogin}
                            sx={{ mb: 2, py: 1.5 }}
                            disabled={isLoading}
                        >
                            {t('auth.signInWith')} {t('auth.aadhaar')}
                        </Button>
                    )}
                </>
            )}
        </Box>
    )
}