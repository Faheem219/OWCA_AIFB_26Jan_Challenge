import React from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import {
    Container,
    Paper,
    Box,
    Typography,
    Button,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../hooks/useAuth'
import { LoginForm } from '../../components/auth/LoginForm'

export const LoginPage: React.FC = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const location = useLocation()
    const { login, isLoading, error, clearError } = useAuth()

    // Get the intended destination from location state
    const from = (location.state as any)?.from?.pathname || '/dashboard'

    const handleLogin = async (email: string, password: string, _rememberMe: boolean = false) => {
        await login(email, password)
        navigate(from, { replace: true })
    }

    const handleGoogleLogin = async () => {
        try {
            // In a real implementation, you would integrate with Google OAuth
            // For now, we'll show a placeholder
            alert('Google OAuth integration will be implemented in a future update')
        } catch (error) {
            console.error('Google login failed:', error)
        }
    }

    const handleAadhaarLogin = async () => {
        try {
            // In a real implementation, you would integrate with Aadhaar OAuth
            // For now, we'll show a placeholder
            alert('Aadhaar OAuth integration will be implemented in a future update')
        } catch (error) {
            console.error('Aadhaar login failed:', error)
        }
    }

    return (
        <Container maxWidth="sm">
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
                        maxWidth: 400,
                        borderRadius: 2,
                    }}
                >
                    <Box sx={{ textAlign: 'center', mb: 4 }}>
                        <Typography variant="h4" gutterBottom fontWeight="bold">
                            {t('auth.loginToAccount')}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            {t('auth.welcomeBack')}
                        </Typography>
                    </Box>

                    <LoginForm
                        onSubmit={handleLogin}
                        onGoogleLogin={handleGoogleLogin}
                        onAadhaarLogin={handleAadhaarLogin}
                        isLoading={isLoading}
                        error={error}
                        onClearError={clearError}
                    />

                    <Box sx={{ textAlign: 'center', mt: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                            {t('auth.dontHaveAccount')}{' '}
                            <Button
                                component={Link}
                                to="/register"
                                variant="text"
                                sx={{ textTransform: 'none', p: 0, minWidth: 'auto' }}
                            >
                                {t('auth.register')}
                            </Button>
                        </Typography>
                    </Box>
                </Paper>
            </Box>
        </Container>
    )
}