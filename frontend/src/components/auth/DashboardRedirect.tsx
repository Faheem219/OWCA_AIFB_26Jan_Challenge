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
            // Check if profile setup was already completed (stored in localStorage)
            const profileSetupCompleted = localStorage.getItem('profileSetupCompleted') === 'true'
            
            // Only require profile setup if it hasn't been completed and essential info is missing
            // For vendors: only check businessName if they explicitly haven't set up profile
            // For buyers: don't require any special setup
            const needsProfileSetup = !profileSetupCompleted && (
                user.role === 'VENDOR' && 
                !(user as any).businessName && 
                !(user as any).business_name &&
                !localStorage.getItem(`vendor_setup_${user.id}`)
            )

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