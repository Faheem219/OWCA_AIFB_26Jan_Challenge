import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Box, Typography, Button } from '@mui/material'
import { useAuth } from '../../hooks/useAuth'
import { LoadingSpinner } from '../common/LoadingSpinner'
import { UserRole } from '../../types'

interface ProtectedRouteProps {
    requiredRole?: UserRole
    redirectTo?: string
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
    requiredRole,
    redirectTo = '/login'
}) => {
    const { user, isAuthenticated, isLoading } = useAuth()
    const location = useLocation()

    // Show loading spinner while checking authentication
    if (isLoading) {
        return (
            <Box
                display="flex"
                justifyContent="center"
                alignItems="center"
                minHeight="60vh"
            >
                <LoadingSpinner message="Checking authentication..." />
            </Box>
        )
    }

    // Redirect to login if not authenticated
    if (!isAuthenticated || !user) {
        return <Navigate to={redirectTo} state={{ from: location }} replace />
    }

    // Check role-based access
    if (requiredRole && user.role !== requiredRole) {
        const allowedRole = requiredRole.toLowerCase()
        const userRole = user.role.toLowerCase()

        return (
            <Box
                display="flex"
                flexDirection="column"
                alignItems="center"
                justifyContent="center"
                minHeight="60vh"
                textAlign="center"
                p={4}
            >
                <Typography variant="h4" color="error" gutterBottom>
                    Access Denied
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                    You don't have permission to access this page.
                    <br />
                    This page requires <strong>{allowedRole}</strong> access, but you are logged in as a <strong>{userRole}</strong>.
                </Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                        variant="contained"
                        onClick={() => window.history.back()}
                    >
                        Go Back
                    </Button>
                    <Button
                        variant="outlined"
                        onClick={() => window.location.href = '/dashboard'}
                    >
                        Go to Dashboard
                    </Button>
                </Box>
            </Box>
        )
    }

    // Render the protected content
    return <Outlet />
}