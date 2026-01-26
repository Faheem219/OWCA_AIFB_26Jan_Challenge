import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box } from '@mui/material'
import { useAuth } from '../../hooks/useAuth'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface DashboardRedirectProps {
    children?: React.ReactNode
}

/**
 * Component that redirects users to their role-appropriate dashboard
 * or renders children if user is already on the correct path
 */
export const DashboardRedirect: React.FC<DashboardRedirectProps> = ({ children }) => {
    const { user, isAuthenticated, isLoading } = useAuth()
    const navigate = useNavigate()

    useEffect(() => {
        if (!isLoading && isAuthenticated && user) {
            // Check if user needs to complete profile setup
            const needsProfileSetup = !user.location?.address ||
                (user.role === 'VENDOR' && !(user as any).businessName) ||
                user.preferredLanguages.length === 0

            if (needsProfileSetup) {
                navigate('/profile/setup', { replace: true })
                return
            }

            // If we're on the generic dashboard route, redirect to role-specific dashboard
            if (window.location.pathname === '/dashboard') {
                const dashboardPath = user.role === 'VENDOR' ? '/dashboard/vendor' : '/dashboard/buyer'
                navigate(dashboardPath, { replace: true })
            }
        }
    }, [user, isAuthenticated, isLoading, navigate])

    if (isLoading) {
        return (
            <Box
                display="flex"
                justifyContent="center"
                alignItems="center"
                minHeight="60vh"
            >
                <LoadingSpinner message="Loading dashboard..." />
            </Box>
        )
    }

    if (!isAuthenticated || !user) {
        navigate('/login', { replace: true })
        return null
    }

    return <>{children}</>
}