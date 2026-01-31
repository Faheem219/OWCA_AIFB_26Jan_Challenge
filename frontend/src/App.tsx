import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'
import { useAuth } from './hooks/useAuth'
import { LoadingSpinner } from './components/common/LoadingSpinner'
import { Layout } from './components/layout/Layout'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { DashboardRedirect } from './components/auth/DashboardRedirect'

// Pages
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { ProfileSetupPage } from './pages/auth/ProfileSetupPage'
import { DashboardPage } from './pages/DashboardPage'
import { VendorDashboard, BuyerDashboard } from './pages/dashboard'
import { ProductsPage } from './pages/products/ProductsPage'
import { ProductDetailPage } from './pages/products/ProductDetailPage'
import { CreateProductPage } from './pages/products/CreateProductPage'
import { EditProductPage } from './pages/products/EditProductPage'
import { ChatPage } from './pages/chat/ChatPage'
import { ProfilePage } from './pages/profile/ProfilePage'
import { NotFoundPage } from './pages/NotFoundPage'

function App() {
    const { isLoading } = useAuth()

    if (isLoading) {
        return (
            <Box
                display="flex"
                justifyContent="center"
                alignItems="center"
                minHeight="100vh"
            >
                <LoadingSpinner size={60} />
            </Box>
        )
    }

    return (
        <Routes>
            {/* Public routes */}
            <Route path="/" element={<Layout />}>
                <Route index element={<HomePage />} />
                <Route path="login" element={<LoginPage />} />
                <Route path="register" element={<RegisterPage />} />
                <Route path="products" element={<ProductsPage />} />
                <Route path="products/:id" element={<ProductDetailPage />} />

                {/* Protected routes */}
                <Route element={<ProtectedRoute />}>
                    <Route path="dashboard" element={<DashboardRedirect><DashboardPage /></DashboardRedirect>} />
                    <Route path="dashboard/vendor" element={<VendorDashboard />} />
                    <Route path="dashboard/buyer" element={<BuyerDashboard />} />
                    <Route path="profile" element={<ProfilePage />} />
                    <Route path="profile/setup" element={<ProfileSetupPage />} />
                    <Route path="chat" element={<ChatPage />} />
                    <Route path="chat/:conversationId" element={<ChatPage />} />

                    {/* Vendor-only routes */}
                    <Route element={<ProtectedRoute requiredRole="VENDOR" />}>
                        <Route path="products/new" element={<CreateProductPage />} />
                        <Route path="products/create" element={<CreateProductPage />} />
                        <Route path="products/:id/edit" element={<EditProductPage />} />
                        <Route path="products/my" element={<ProductsPage />} />
                    </Route>
                </Route>

                {/* Catch all route */}
                <Route path="*" element={<NotFoundPage />} />
            </Route>
        </Routes>
    )
}

export default App