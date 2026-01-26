import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
    Container,
    Paper,
    Box,
    Typography,
    Button,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../hooks/useAuth'
import { RegistrationForm, RegistrationData } from '../../components/auth/RegistrationForm'
import { UserRole } from '../../types'

export const RegisterPage: React.FC = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { register, isLoading, error, clearError } = useAuth()

    const handleRegister = async (data: RegistrationData) => {
        await register({
            email: data.email,
            password: data.password,
            confirmPassword: data.confirmPassword,
            role: data.role as UserRole,
            preferredLanguages: data.preferredLanguages,
            phone: data.phone || undefined,
            businessName: data.businessName || undefined,
            location: data.location!,
        })

        // Registration successful, redirect to login
        navigate('/login', {
            state: {
                message: 'Registration successful! Please login with your credentials.'
            }
        })
    }

    const handleGoogleRegister = async () => {
        try {
            // In a real implementation, you would integrate with Google OAuth
            // For now, we'll show a placeholder
            alert('Google OAuth integration will be implemented in a future update')
        } catch (error) {
            console.error('Google registration failed:', error)
        }
    }

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
                            {t('auth.createNewAccount')}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            {t('auth.joinMarketplace')}
                        </Typography>
                    </Box>

                    <RegistrationForm
                        onSubmit={handleRegister}
                        onGoogleRegister={handleGoogleRegister}
                        isLoading={isLoading}
                        error={error}
                        onClearError={clearError}
                    />

                    <Box sx={{ textAlign: 'center', mt: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                            {t('auth.alreadyHaveAccount')}{' '}
                            <Button
                                component={Link}
                                to="/login"
                                variant="text"
                                sx={{ textTransform: 'none', p: 0, minWidth: 'auto' }}
                            >
                                {t('auth.login')}
                            </Button>
                        </Typography>
                    </Box>
                </Paper>
            </Box>
        </Container>
    )
}