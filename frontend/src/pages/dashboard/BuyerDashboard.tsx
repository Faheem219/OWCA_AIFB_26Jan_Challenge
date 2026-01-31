import React, { useState, useEffect } from 'react'
import {
    Container,
    Grid,
    Paper,
    Typography,
    Box,
    Card,
    CardContent,
    CardMedia,
    CardActions,
    Button,
    Chip,
    Avatar,
    List,
    ListItem,
    ListItemAvatar,
    ListItemText,
    Divider,
    IconButton,
    Tooltip,
    Alert,
    TextField,
    InputAdornment,
} from '@mui/material'
import {
    ShoppingCart,
    Favorite,
    Search,
    LocalOffer,
    History,
    Store,
    Refresh,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { productService } from '../../services/productService'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'

interface DashboardStats {
    totalPurchases: number
    savedItems: number
    recentlyViewed: number
    activeDeals: number
}

interface ProductCard {
    id: string
    name: string
    price: number
    unit: string
    vendorName: string
    category: string
    imageUrl?: string
}

export const BuyerDashboard: React.FC = () => {
    const navigate = useNavigate()
    const { user } = useAuth()
    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState<DashboardStats>({
        totalPurchases: 0,
        savedItems: 0,
        recentlyViewed: 0,
        activeDeals: 0,
    })
    const [featuredProducts, setFeaturedProducts] = useState<ProductCard[]>([])
    const [searchQuery, setSearchQuery] = useState('')
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadDashboardData()
    }, [])

    const loadDashboardData = async () => {
        setLoading(true)
        setError(null)
        try {
            // Load featured/recent products
            const response = await productService.searchProducts({
                limit: 8,
                available_only: true,
            })

            const products = response.products || []

            setFeaturedProducts(products.map((p: any) => {
                // Handle both transformed Product type and raw backend response
                const productName = typeof p.name === 'object'
                    ? (p.name.originalText || p.name.original_text || 'Unnamed Product')
                    : (p.name || 'Unnamed Product')

                return {
                    id: p.id || p._id || p.product_id,
                    name: productName,
                    price: p.basePrice || p.price_info?.base_price || 0,
                    unit: p.unit || p.price_info?.unit || 'kg',
                    vendorName: p.vendor?.business_name || p.vendor?.businessName || 'Vendor',
                    category: p.category || 'uncategorized',
                    imageUrl: p.images?.[0]?.url || p.images?.[0]?.image_url,
                }
            }))

            // Mock stats for buyer
            setStats({
                totalPurchases: (user as any)?.total_purchases || 0,
                savedItems: Math.floor(Math.random() * 10),
                recentlyViewed: products.length,
                activeDeals: Math.floor(Math.random() * 5) + 1,
            })
        } catch (err) {
            console.error('Failed to load dashboard data:', err)
            setError('Failed to load dashboard data')
        } finally {
            setLoading(false)
        }
    }

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (searchQuery.trim()) {
            navigate(`/products?search=${encodeURIComponent(searchQuery)}`)
        }
    }

    const categories = [
        { name: 'Vegetables', icon: '🥬', color: '#4caf50' },
        { name: 'Fruits', icon: '🍎', color: '#f44336' },
        { name: 'Grains', icon: '🌾', color: '#ff9800' },
        { name: 'Spices', icon: '🌶️', color: '#e91e63' },
        { name: 'Dairy', icon: '🥛', color: '#2196f3' },
    ]

    const StatCard: React.FC<{
        title: string
        value: string | number
        icon: React.ReactNode
        color: string
    }> = ({ title, value, icon, color }) => (
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
                        Buyer Dashboard
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Welcome back! Find the freshest produce from local vendors.
                    </Typography>
                </Box>
                <Tooltip title="Refresh Data">
                    <IconButton onClick={loadDashboardData} color="primary">
                        <Refresh />
                    </IconButton>
                </Tooltip>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* Search Bar */}
            <Paper sx={{ p: 2, mb: 4 }}>
                <form onSubmit={handleSearch}>
                    <TextField
                        fullWidth
                        placeholder="Search for products, vendors, or categories..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        InputProps={{
                            startAdornment: (
                                <InputAdornment position="start">
                                    <Search />
                                </InputAdornment>
                            ),
                            endAdornment: (
                                <InputAdornment position="end">
                                    <Button
                                        variant="contained"
                                        type="submit"
                                        sx={{ borderRadius: 2 }}
                                    >
                                        Search
                                    </Button>
                                </InputAdornment>
                            ),
                        }}
                        sx={{
                            '& .MuiOutlinedInput-root': {
                                borderRadius: 3,
                            },
                        }}
                    />
                </form>
            </Paper>

            {/* Stats Grid */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Total Purchases"
                        value={stats.totalPurchases}
                        icon={<ShoppingCart />}
                        color="#1976d2"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Saved Items"
                        value={stats.savedItems}
                        icon={<Favorite />}
                        color="#e91e63"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Recently Viewed"
                        value={stats.recentlyViewed}
                        icon={<History />}
                        color="#ff9800"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Active Deals"
                        value={stats.activeDeals}
                        icon={<LocalOffer />}
                        color="#4caf50"
                    />
                </Grid>
            </Grid>

            {/* Categories */}
            <Paper sx={{ p: 3, mb: 4 }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Browse Categories
                </Typography>
                <Grid container spacing={2}>
                    {categories.map((category) => (
                        <Grid item xs={6} sm={4} md={2.4} key={category.name}>
                            <Card
                                sx={{
                                    textAlign: 'center',
                                    cursor: 'pointer',
                                    transition: 'transform 0.2s, box-shadow 0.2s',
                                    '&:hover': {
                                        transform: 'translateY(-4px)',
                                        boxShadow: 4,
                                    },
                                }}
                                onClick={() => navigate(`/products?category=${category.name.toLowerCase()}`)}
                            >
                                <CardContent>
                                    <Typography variant="h3" sx={{ mb: 1 }}>
                                        {category.icon}
                                    </Typography>
                                    <Typography variant="body2" fontWeight="medium">
                                        {category.name}
                                    </Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            </Paper>

            {/* Featured Products */}
            <Box sx={{ mb: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" fontWeight="bold">
                        Featured Products
                    </Typography>
                    <Button onClick={() => navigate('/products')}>
                        View All
                    </Button>
                </Box>
                {featuredProducts.length === 0 ? (
                    <Paper sx={{ p: 4, textAlign: 'center' }}>
                        <Store sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                        <Typography color="text.secondary">
                            No products available at the moment.
                        </Typography>
                    </Paper>
                ) : (
                    <Grid container spacing={3}>
                        {featuredProducts.slice(0, 4).map((product) => (
                            <Grid item xs={12} sm={6} md={3} key={product.id}>
                                <Card
                                    sx={{
                                        height: '100%',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        cursor: 'pointer',
                                        transition: 'transform 0.2s',
                                        '&:hover': {
                                            transform: 'translateY(-4px)',
                                        },
                                    }}
                                    onClick={() => navigate(`/products/${product.id}`)}
                                >
                                    <CardMedia
                                        component="div"
                                        sx={{
                                            height: 140,
                                            bgcolor: '#f5f5f5',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                        }}
                                    >
                                        {product.imageUrl ? (
                                            <img
                                                src={product.imageUrl}
                                                alt={product.name}
                                                style={{ maxHeight: '100%', maxWidth: '100%' }}
                                            />
                                        ) : (
                                            <Store sx={{ fontSize: 48, color: 'text.secondary' }} />
                                        )}
                                    </CardMedia>
                                    <CardContent sx={{ flexGrow: 1 }}>
                                        <Typography variant="subtitle1" fontWeight="medium" noWrap>
                                            {product.name}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" gutterBottom>
                                            by {product.vendorName}
                                        </Typography>
                                        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5 }}>
                                            <Typography variant="h6" color="primary" fontWeight="bold">
                                                ₹{product.price}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                /{product.unit}
                                            </Typography>
                                        </Box>
                                        <Chip
                                            label={product.category}
                                            size="small"
                                            sx={{ mt: 1 }}
                                            variant="outlined"
                                        />
                                    </CardContent>
                                    <CardActions>
                                        <Button size="small" fullWidth variant="contained">
                                            View Details
                                        </Button>
                                    </CardActions>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                )}
            </Box>

            {/* Quick Actions */}
            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                            Quick Actions
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <Button
                                variant="outlined"
                                fullWidth
                                startIcon={<Search />}
                                onClick={() => navigate('/products')}
                            >
                                Browse All Products
                            </Button>
                            <Button
                                variant="outlined"
                                fullWidth
                                startIcon={<Store />}
                                onClick={() => navigate('/vendors')}
                            >
                                Find Vendors Near Me
                            </Button>
                            <Button
                                variant="outlined"
                                fullWidth
                                startIcon={<History />}
                                onClick={() => navigate('/orders')}
                            >
                                View Order History
                            </Button>
                            <Button
                                variant="outlined"
                                fullWidth
                                startIcon={<Favorite />}
                                onClick={() => navigate('/wishlist')}
                            >
                                My Wishlist
                            </Button>
                        </Box>
                    </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, height: '100%' }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                            Today's Deals
                        </Typography>
                        <List>
                            {featuredProducts.slice(0, 3).map((product, index) => (
                                <React.Fragment key={product.id}>
                                    <ListItem
                                        sx={{ cursor: 'pointer' }}
                                        onClick={() => navigate(`/products/${product.id}`)}
                                    >
                                        <ListItemAvatar>
                                            <Avatar sx={{ bgcolor: '#e8f5e9' }}>
                                                <LocalOffer color="success" />
                                            </Avatar>
                                        </ListItemAvatar>
                                        <ListItemText
                                            primary={product.name}
                                            secondary={`₹${product.price}/${product.unit}`}
                                        />
                                        <Chip
                                            label={`${Math.floor(Math.random() * 20 + 5)}% OFF`}
                                            color="success"
                                            size="small"
                                        />
                                    </ListItem>
                                    {index < 2 && <Divider />}
                                </React.Fragment>
                            ))}
                        </List>
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    )
}
