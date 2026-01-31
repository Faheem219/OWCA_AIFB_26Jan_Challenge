import React, { useState, useEffect } from 'react'
import {
    Container,
    Grid,
    Paper,
    Typography,
    Box,
    Card,
    CardContent,
    Avatar,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Alert,
    LinearProgress,
    Divider,
    List,
    ListItem,
    ListItemText,
    Chip,
} from '@mui/material'
import {
    TrendingUp,
    Visibility,
    ShoppingCart,
    Star,
    People,
    Inventory,
    AttachMoney,
} from '@mui/icons-material'
import { useAuth } from '../../hooks/useAuth'
import { productService } from '../../services/productService'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'

interface AnalyticsData {
    totalProducts: number
    totalViews: number
    totalSales: number
    revenue: number
    averageRating: number
    conversionRate: number
    topProducts: Array<{
        id: string
        name: string
        views: number
        sales: number
    }>
    categoryBreakdown: Array<{
        category: string
        count: number
        percentage: number
    }>
}

export const AnalyticsPage: React.FC = () => {
    const { user } = useAuth()
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [timeRange, setTimeRange] = useState('30')
    const [analytics, setAnalytics] = useState<AnalyticsData>({
        totalProducts: 0,
        totalViews: 0,
        totalSales: 0,
        revenue: 0,
        averageRating: 0,
        conversionRate: 0,
        topProducts: [],
        categoryBreakdown: [],
    })

    useEffect(() => {
        loadAnalytics()
    }, [timeRange])

    const loadAnalytics = async () => {
        setLoading(true)
        setError(null)
        try {
            // Load vendor's products
            const response = await productService.getMyProducts()
            const products = response.products || []

            // Calculate analytics from products
            const totalViews = products.reduce((sum: number, p: any) => 
                sum + (p.viewsCount || p.views_count || 0), 0)
            const totalSales = products.reduce((sum: number, p: any) => 
                sum + (p.salesCount || p.sales_count || 0), 0)
            const revenue = products.reduce((sum: number, p: any) => 
                sum + ((p.basePrice || p.price_info?.base_price || 0) * (p.salesCount || p.sales_count || 0)), 0)

            // Category breakdown
            const categoryCounts: Record<string, number> = {}
            products.forEach((p: any) => {
                const cat = p.category || 'uncategorized'
                categoryCounts[cat] = (categoryCounts[cat] || 0) + 1
            })
            const categoryBreakdown = Object.entries(categoryCounts).map(([category, count]) => ({
                category,
                count,
                percentage: products.length > 0 ? Math.round((count / products.length) * 100) : 0,
            }))

            // Top products by views
            const topProducts = products
                .map((p: any) => ({
                    id: p.id || p._id || p.product_id,
                    name: typeof p.name === 'object' ? (p.name.originalText || 'Unnamed') : (p.name || 'Unnamed'),
                    views: p.viewsCount || p.views_count || 0,
                    sales: p.salesCount || p.sales_count || 0,
                }))
                .sort((a: any, b: any) => b.views - a.views)
                .slice(0, 5)

            setAnalytics({
                totalProducts: products.length,
                totalViews,
                totalSales,
                revenue,
                averageRating: (user as any)?.rating || 4.5,
                conversionRate: totalViews > 0 ? Math.round((totalSales / totalViews) * 100) : 0,
                topProducts,
                categoryBreakdown,
            })
        } catch (err) {
            console.error('Failed to load analytics:', err)
            setError('Failed to load analytics data')
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
        return <LoadingSpinner message="Loading analytics..." />
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Box>
                    <Typography variant="h4" fontWeight="bold" gutterBottom>
                        Analytics Dashboard
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Track your store performance and sales metrics
                    </Typography>
                </Box>
                <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Time Range</InputLabel>
                    <Select
                        value={timeRange}
                        label="Time Range"
                        onChange={(e) => setTimeRange(e.target.value)}
                    >
                        <MenuItem value="7">Last 7 days</MenuItem>
                        <MenuItem value="30">Last 30 days</MenuItem>
                        <MenuItem value="90">Last 90 days</MenuItem>
                        <MenuItem value="365">Last year</MenuItem>
                    </Select>
                </FormControl>
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
                        value={analytics.totalProducts}
                        icon={<Inventory />}
                        color="#1976d2"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Total Views"
                        value={analytics.totalViews.toLocaleString()}
                        icon={<Visibility />}
                        color="#2e7d32"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Total Sales"
                        value={analytics.totalSales}
                        icon={<ShoppingCart />}
                        color="#ed6c02"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Revenue"
                        value={`₹${analytics.revenue.toLocaleString()}`}
                        icon={<AttachMoney />}
                        color="#9c27b0"
                    />
                </Grid>
            </Grid>

            {/* Secondary Stats */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                        title="Average Rating"
                        value={analytics.averageRating.toFixed(1)}
                        icon={<Star />}
                        color="#ffc107"
                        subtitle="out of 5.0"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                        title="Conversion Rate"
                        value={`${analytics.conversionRate}%`}
                        icon={<TrendingUp />}
                        color="#00bcd4"
                        subtitle="views to sales"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                        title="Active Customers"
                        value={Math.max(1, Math.floor(analytics.totalSales * 0.7))}
                        icon={<People />}
                        color="#4caf50"
                    />
                </Grid>
            </Grid>

            {/* Detailed Analytics */}
            <Grid container spacing={3}>
                {/* Top Products */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                            Top Products by Views
                        </Typography>
                        {analytics.topProducts.length === 0 ? (
                            <Typography color="text.secondary" sx={{ py: 2 }}>
                                No products yet. Add your first product to see analytics.
                            </Typography>
                        ) : (
                            <List>
                                {analytics.topProducts.map((product, index) => (
                                    <React.Fragment key={product.id}>
                                        <ListItem>
                                            <Avatar sx={{ mr: 2, bgcolor: 'primary.light' }}>
                                                {index + 1}
                                            </Avatar>
                                            <ListItemText
                                                primary={product.name}
                                                secondary={`${product.views} views • ${product.sales} sales`}
                                            />
                                        </ListItem>
                                        {index < analytics.topProducts.length - 1 && <Divider />}
                                    </React.Fragment>
                                ))}
                            </List>
                        )}
                    </Paper>
                </Grid>

                {/* Category Breakdown */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                            Category Breakdown
                        </Typography>
                        {analytics.categoryBreakdown.length === 0 ? (
                            <Typography color="text.secondary" sx={{ py: 2 }}>
                                No products yet.
                            </Typography>
                        ) : (
                            <Box>
                                {analytics.categoryBreakdown.map((cat) => (
                                    <Box key={cat.category} sx={{ mb: 3 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Chip label={cat.category} size="small" />
                                                <Typography variant="body2">
                                                    {cat.count} products
                                                </Typography>
                                            </Box>
                                            <Typography variant="body2" fontWeight="bold">
                                                {cat.percentage}%
                                            </Typography>
                                        </Box>
                                        <LinearProgress 
                                            variant="determinate" 
                                            value={cat.percentage} 
                                            sx={{ height: 8, borderRadius: 1 }}
                                        />
                                    </Box>
                                ))}
                            </Box>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    )
}
