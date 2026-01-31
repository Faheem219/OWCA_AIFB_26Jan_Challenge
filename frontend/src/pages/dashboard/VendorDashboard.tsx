import React, { useState, useEffect } from 'react'
import {
    Container,
    Grid,
    Paper,
    Typography,
    Box,
    Card,
    CardContent,
    Button,
    Chip,
    Avatar,
    List,
    ListItem,
    ListItemAvatar,
    ListItemText,
    Divider,
    LinearProgress,
    IconButton,
    Tooltip,
    Alert,
} from '@mui/material'
import {
    Store,
    Inventory,
    Add,
    Visibility,
    Edit,
    ShoppingCart,
    Star,
    LocalShipping,
    Analytics,
    Refresh,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { productService } from '../../services/productService'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'

interface DashboardStats {
    totalProducts: number
    activeListings: number
    totalViews: number
    totalSales: number
    revenue: number
    rating: number
    pendingOrders: number
}

interface RecentProduct {
    id: string
    name: string
    price: number
    status: string
    views: number
    category: string
}

export const VendorDashboard: React.FC = () => {
    const navigate = useNavigate()
    const { user } = useAuth()
    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState<DashboardStats>({
        totalProducts: 0,
        activeListings: 0,
        totalViews: 0,
        totalSales: 0,
        revenue: 0,
        rating: 0,
        pendingOrders: 0,
    })
    const [recentProducts, setRecentProducts] = useState<RecentProduct[]>([])
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadDashboardData()
    }, [])

    const loadDashboardData = async () => {
        setLoading(true)
        setError(null)
        try {
            // Load vendor's products
            const response = await productService.getMyProducts()
            const products = response.products || []

            // Calculate stats from products (status is uppercase after transformation)
            const activeProducts = products.filter((p: any) =>
                p.status?.toLowerCase() === 'active' || p.status === 'ACTIVE'
            )
            const totalViews = products.reduce((sum: number, p: any) => sum + (p.viewsCount || p.views_count || 0), 0)

            setStats({
                totalProducts: products.length,
                activeListings: activeProducts.length,
                totalViews: totalViews,
                totalSales: (user as any)?.total_transactions || 0,
                revenue: products.reduce((sum: number, p: any) => sum + ((p.basePrice || 0) * (p.salesCount || 0)), 0),
                rating: (user as any)?.rating || 4.5,
                pendingOrders: Math.floor(Math.random() * 5), // Mock data
            })

            // Get recent products
            setRecentProducts(products.slice(0, 5).map((p: any) => {
                // Handle both transformed Product type and raw backend response
                const productName = typeof p.name === 'object'
                    ? (p.name.originalText || p.name.original_text || 'Unnamed Product')
                    : (p.name || 'Unnamed Product')

                return {
                    id: p.id || p._id || p.product_id,
                    name: productName,
                    price: p.basePrice || p.price_info?.base_price || 0,
                    status: p.status || 'active',
                    views: p.views_count || p.viewsCount || 0,
                    category: p.category || 'uncategorized',
                }
            }))
        } catch (err) {
            console.error('Failed to load dashboard data:', err)
            setError('Failed to load dashboard data')
        } finally {
            setLoading(false)
        }
    }

    const StatCard: React.FC<{
        title: string
        value: string | number
        icon: React.ReactNode
        color: string
        subtitle?: string
    }> = ({ title, value, icon, color, subtitle }) => (
        <Card sx={{ height: '100%' }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                        <Typography color="text.secondary" variant="body2" gutterBottom>
                            {title}
                        </Typography>
                        <Typography variant="h4" fontWeight="bold">
                            {value}
                        </Typography>
                        {subtitle && (
                            <Typography variant="caption" color="text.secondary">
                                {subtitle}
                            </Typography>
                        )}
                    </Box>
                    <Avatar sx={{ bgcolor: color, width: 56, height: 56 }}>
                        {icon}
                    </Avatar>
                </Box>
            </CardContent>
        </Card>
    )

    if (loading) {
        return <LoadingSpinner message="Loading dashboard..." />
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Box>
                    <Typography variant="h4" fontWeight="bold" gutterBottom>
                        Vendor Dashboard
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Welcome back, {(user as any)?.business_name || user?.email}!
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Tooltip title="Refresh Data">
                        <IconButton onClick={loadDashboardData} color="primary">
                            <Refresh />
                        </IconButton>
                    </Tooltip>
                    <Button
                        variant="contained"
                        startIcon={<Add />}
                        onClick={() => navigate('/products/new')}
                    >
                        Add Product
                    </Button>
                </Box>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* Stats Grid */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Total Products"
                        value={stats.totalProducts}
                        icon={<Inventory />}
                        color="#1976d2"
                        subtitle={`${stats.activeListings} active`}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Total Views"
                        value={stats.totalViews}
                        icon={<Visibility />}
                        color="#2e7d32"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Total Sales"
                        value={stats.totalSales}
                        icon={<ShoppingCart />}
                        color="#ed6c02"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Rating"
                        value={stats.rating.toFixed(1)}
                        icon={<Star />}
                        color="#9c27b0"
                        subtitle="out of 5.0"
                    />
                </Grid>
            </Grid>

            {/* Main Content Grid */}
            <Grid container spacing={3}>
                {/* Recent Products */}
                <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Typography variant="h6" fontWeight="bold">
                                Recent Products
                            </Typography>
                            <Button size="small" onClick={() => navigate('/products/my')}>
                                View All
                            </Button>
                        </Box>
                        {recentProducts.length === 0 ? (
                            <Box sx={{ textAlign: 'center', py: 4 }}>
                                <Inventory sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                                <Typography color="text.secondary">
                                    No products yet. Add your first product!
                                </Typography>
                                <Button
                                    variant="outlined"
                                    startIcon={<Add />}
                                    sx={{ mt: 2 }}
                                    onClick={() => navigate('/products/new')}
                                >
                                    Add Product
                                </Button>
                            </Box>
                        ) : (
                            <List>
                                {recentProducts.map((product, index) => (
                                    <React.Fragment key={product.id}>
                                        <ListItem
                                            secondaryAction={
                                                <IconButton onClick={() => navigate(`/products/${product.id}/edit`)}>
                                                    <Edit />
                                                </IconButton>
                                            }
                                        >
                                            <ListItemAvatar>
                                                <Avatar sx={{ bgcolor: '#e3f2fd' }}>
                                                    <Store color="primary" />
                                                </Avatar>
                                            </ListItemAvatar>
                                            <ListItemText
                                                primary={product.name}
                                                secondaryTypographyProps={{ component: 'div' }}
                                                secondary={
                                                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 0.5 }}>
                                                        <Chip
                                                            label={`₹${product.price}`}
                                                            size="small"
                                                            color="primary"
                                                            variant="outlined"
                                                        />
                                                        <Chip
                                                            label={product.category}
                                                            size="small"
                                                            variant="outlined"
                                                        />
                                                        <Typography variant="caption" color="text.secondary">
                                                            {product.views} views
                                                        </Typography>
                                                    </Box>
                                                }
                                            />
                                        </ListItem>
                                        {index < recentProducts.length - 1 && <Divider />}
                                    </React.Fragment>
                                ))}
                            </List>
                        )}
                    </Paper>
                </Grid>

                {/* Quick Actions & Stats */}
                <Grid item xs={12} md={4}>
                    {/* Quick Actions */}
                    <Paper sx={{ p: 3, mb: 3 }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                            Quick Actions
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <Button
                                variant="outlined"
                                fullWidth
                                startIcon={<Add />}
                                onClick={() => navigate('/products/new')}
                            >
                                Add New Product
                            </Button>
                            <Button
                                variant="outlined"
                                fullWidth
                                startIcon={<Inventory />}
                                onClick={() => navigate('/products/my')}
                            >
                                Manage Products
                            </Button>
                            <Button
                                variant="outlined"
                                fullWidth
                                startIcon={<Analytics />}
                                onClick={() => navigate('/analytics')}
                            >
                                View Analytics
                            </Button>
                            <Button
                                variant="outlined"
                                fullWidth
                                startIcon={<LocalShipping />}
                                onClick={() => navigate('/orders')}
                            >
                                Manage Orders
                            </Button>
                        </Box>
                    </Paper>

                    {/* Performance Summary */}
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                            Performance
                        </Typography>
                        <Box sx={{ mb: 3 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="body2">Profile Completion</Typography>
                                <Typography variant="body2" fontWeight="bold">85%</Typography>
                            </Box>
                            <LinearProgress variant="determinate" value={85} />
                        </Box>
                        <Box sx={{ mb: 3 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="body2">Response Rate</Typography>
                                <Typography variant="body2" fontWeight="bold">92%</Typography>
                            </Box>
                            <LinearProgress variant="determinate" value={92} color="success" />
                        </Box>
                        <Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="body2">Customer Satisfaction</Typography>
                                <Typography variant="body2" fontWeight="bold">88%</Typography>
                            </Box>
                            <LinearProgress variant="determinate" value={88} color="secondary" />
                        </Box>
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    )
}
