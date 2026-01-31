import React from 'react'
import { useAuth } from '../hooks/useAuth'
import { VendorDashboard, BuyerDashboard } from './dashboard'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { Navigate } from 'react-router-dom'

export const DashboardPage: React.FC = () => {
    const { user, isLoading } = useAuth()

    if (isLoading) {
        return <LoadingSpinner message="Loading..." />
    }

    if (!user) {
        return <Navigate to="/login" replace />
    }

    // Check user role and render appropriate dashboard
    const role = (user as any).role?.toLowerCase() || user.role?.toLowerCase()

    if (role === 'vendor') {
        return <VendorDashboard />
    } else if (role === 'buyer') {
        return <BuyerDashboard />
    }

    // Default to buyer dashboard if role is unknown
    return <BuyerDashboard />
}