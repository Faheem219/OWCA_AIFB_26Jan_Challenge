import React, { useState, useEffect } from 'react'
import {
    Container,
    Paper,
    Typography,
    Box,
    Grid,
    Card,
    CardMedia,
    CardContent,
    CardActions,
    Button,
    IconButton,
    Alert,
    Chip,
} from '@mui/material'
import {
    ShoppingCart,
    Chat,
    Refresh,
    FavoriteBorder,
    Favorite,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { productService } from '../../services/productService'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'

interface SavedItem {
    id: string
    product_id: string
    product_name: string
    product_image: string
    price: number
    unit: string
    vendor_name: string
    vendor_id: string
    saved_at: string
    is_available: boolean
}

export const SavedItemsPage: React.FC = () => {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [savedItems, setSavedItems] = useState<SavedItem[]>([])
    const [removingId, setRemovingId] = useState<string | null>(null)

    useEffect(() => {
        loadSavedItems()
    }, [])

    const loadSavedItems = async () => {
        setLoading(true)
        setError(null)
        try {
            // Try to get liked/saved items from localStorage or API
            const likedProducts = JSON.parse(localStorage.getItem('likedProducts') || '[]')
            
            // If we have liked product IDs, fetch their details
            if (likedProducts.length > 0) {
                try {
                    const productPromises = likedProducts.map(async (productId: string) => {
                        try {
                            const product = await productService.getProduct(productId)
                            if (!product) return null
                            
                            // Handle multilingual text
                            const productName = typeof product.name === 'object'
                                ? (product.name.originalText || 'Unnamed Product')
                                : (product.name || 'Unnamed Product')

                            return {
                                id: productId,
                                product_id: productId,
                                product_name: productName,
                                product_image: product.images?.[0]?.url || product.images?.[0]?.thumbnailUrl || '/placeholder-product.jpg',
                                price: product.basePrice || 0,
                                unit: product.unit || 'kg',
                                vendor_name: (product as any).vendor?.business_name || 'Unknown Vendor',
                                vendor_id: product.vendorId,
                                saved_at: new Date().toISOString(),
                                is_available: product.quantityAvailable > 0,
                            }
                        } catch {
                            return null
                        }
                    })
                    const products = await Promise.all(productPromises)
                    setSavedItems(products.filter(p => p !== null) as SavedItem[])
                } catch (err) {
                    // If API fails, show empty state
                    setSavedItems([])
                }
            } else {
                setSavedItems([])
            }
        } catch (err) {
            setError('Failed to load saved items')
        } finally {
            setLoading(false)
        }
    }

    const handleRemoveItem = async (itemId: string) => {
        setRemovingId(itemId)
        try {
            // Remove from localStorage
            const likedProducts = JSON.parse(localStorage.getItem('likedProducts') || '[]')
            const updated = likedProducts.filter((id: string) => id !== itemId)
            localStorage.setItem('likedProducts', JSON.stringify(updated))
            
            // Update state
            setSavedItems(prev => prev.filter(item => item.product_id !== itemId))
        } catch (err) {
            setError('Failed to remove item')
        } finally {
            setRemovingId(null)
        }
    }

    const handleViewProduct = (productId: string) => {
        navigate(`/products/${productId}`)
    }

    const handleContactVendor = (vendorId: string, productId: string) => {
        navigate(`/chat?vendor=${vendorId}&product=${productId}`)
    }

    const handleAddToCart = (item: SavedItem) => {
        // Get existing cart
        const cart = JSON.parse(localStorage.getItem('cart') || '[]')
        
        // Check if item already in cart
        const existingIndex = cart.findIndex((c: any) => c.product_id === item.product_id)
        
        if (existingIndex >= 0) {
            cart[existingIndex].quantity += 1
        } else {
            cart.push({
                product_id: item.product_id,
                product_name: item.product_name,
                product_image: item.product_image,
                price: item.price,
                unit: item.unit,
                quantity: 1,
                vendor_id: item.vendor_id,
                vendor_name: item.vendor_name,
            })
        }
        
        localStorage.setItem('cart', JSON.stringify(cart))
        
        // Dispatch event for cart update
        window.dispatchEvent(new Event('cartUpdated'))
    }

    if (loading) {
        return <LoadingSpinner message="Loading saved items..." />
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Box>
                    <Typography variant="h4" fontWeight="bold" gutterBottom>
                        Saved Items
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Products you've liked and saved for later
                    </Typography>
                </Box>
                <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={loadSavedItems}
                >
                    Refresh
                </Button>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {savedItems.length === 0 ? (
                <Paper sx={{ p: 6, textAlign: 'center' }}>
                    <FavoriteBorder sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                        No saved items yet
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Browse products and click the heart icon to save items for later
                    </Typography>
                    <Button
                        variant="contained"
                        onClick={() => navigate('/products')}
                    >
                        Browse Products
                    </Button>
                </Paper>
            ) : (
                <Grid container spacing={3}>
                    {savedItems.map((item) => (
                        <Grid item xs={12} sm={6} md={4} lg={3} key={item.id}>
                            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                                <Box sx={{ position: 'relative' }}>
                                    <CardMedia
                                        component="img"
                                        height="180"
                                        image={item.product_image}
                                        alt={item.product_name}
                                        sx={{ cursor: 'pointer' }}
                                        onClick={() => handleViewProduct(item.product_id)}
                                    />
                                    {!item.is_available && (
                                        <Chip
                                            label="Unavailable"
                                            color="error"
                                            size="small"
                                            sx={{ position: 'absolute', top: 8, left: 8 }}
                                        />
                                    )}
                                    <IconButton
                                        sx={{
                                            position: 'absolute',
                                            top: 8,
                                            right: 8,
                                            bgcolor: 'background.paper',
                                            '&:hover': { bgcolor: 'error.light', color: 'white' },
                                        }}
                                        onClick={() => handleRemoveItem(item.product_id)}
                                        disabled={removingId === item.product_id}
                                    >
                                        <Favorite color="error" />
                                    </IconButton>
                                </Box>
                                <CardContent sx={{ flexGrow: 1 }}>
                                    <Typography 
                                        variant="h6" 
                                        noWrap 
                                        sx={{ cursor: 'pointer' }}
                                        onClick={() => handleViewProduct(item.product_id)}
                                    >
                                        {item.product_name}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        by {item.vendor_name}
                                    </Typography>
                                    <Typography variant="h6" color="primary" sx={{ mt: 1 }}>
                                        ₹{item.price}/{item.unit}
                                    </Typography>
                                </CardContent>
                                <CardActions sx={{ px: 2, pb: 2 }}>
                                    <Button
                                        size="small"
                                        startIcon={<ShoppingCart />}
                                        onClick={() => handleAddToCart(item)}
                                        disabled={!item.is_available}
                                        variant="contained"
                                        fullWidth
                                    >
                                        Add to Cart
                                    </Button>
                                    <IconButton
                                        size="small"
                                        onClick={() => handleContactVendor(item.vendor_id, item.product_id)}
                                        color="primary"
                                    >
                                        <Chat />
                                    </IconButton>
                                </CardActions>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            )}
        </Container>
    )
}
