import React, { useState, useEffect } from 'react'
import {
    Container,
    Paper,
    Typography,
    Box,
    Grid,
    Card,
    CardContent,
    CardMedia,
    CardActions,
    Button,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Alert,
    Chip,
    Switch,
    FormControlLabel,
    Slider,
} from '@mui/material'
import {
    LocalOffer,
    Edit,
    Delete,
    Add,
    Refresh,
    Store,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { productService } from '../../services/productService'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { Product } from '../../types'

interface Deal {
    product_id: string
    product_name: string
    product_image?: string
    original_price: number
    discount_percentage: number
    deal_price: number
    unit: string
    start_date: string
    end_date: string
    is_active: boolean
}

export const DealsManagementPage: React.FC = () => {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)
    const [products, setProducts] = useState<Product[]>([])
    const [deals, setDeals] = useState<Deal[]>([])
    const [dialogOpen, setDialogOpen] = useState(false)
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
    const [dealForm, setDealForm] = useState({
        discount_percentage: 10,
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        is_active: true,
    })

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        setLoading(true)
        setError(null)
        try {
            // Load vendor's products
            const { products: vendorProducts } = await productService.getMyProducts()
            setProducts(vendorProducts)

            // Load existing deals from localStorage (in production, this would come from backend)
            const savedDeals = JSON.parse(localStorage.getItem('vendorDeals') || '[]')
            setDeals(savedDeals.filter((d: Deal) => vendorProducts.some(p => p.id === d.product_id)))
        } catch (err) {
            setError('Failed to load products')
        } finally {
            setLoading(false)
        }
    }

    const handleCreateDeal = (product: Product) => {
        setSelectedProduct(product)
        setDealForm({
            discount_percentage: 10,
            start_date: new Date().toISOString().split('T')[0],
            end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            is_active: true,
        })
        setDialogOpen(true)
    }

    const handleSaveDeal = () => {
        if (!selectedProduct) return

        const productName = typeof selectedProduct.name === 'object'
            ? selectedProduct.name.originalText
            : selectedProduct.name

        const newDeal: Deal = {
            product_id: selectedProduct.id,
            product_name: productName,
            product_image: selectedProduct.images?.[0]?.url,
            original_price: selectedProduct.basePrice,
            discount_percentage: dealForm.discount_percentage,
            deal_price: selectedProduct.basePrice * (1 - dealForm.discount_percentage / 100),
            unit: selectedProduct.unit,
            start_date: dealForm.start_date,
            end_date: dealForm.end_date,
            is_active: dealForm.is_active,
        }

        // Update deals (replace if exists, add if new)
        const updatedDeals = deals.filter(d => d.product_id !== selectedProduct.id)
        updatedDeals.push(newDeal)
        
        // Save to localStorage (in production, this would be saved to backend)
        localStorage.setItem('vendorDeals', JSON.stringify(updatedDeals))
        setDeals(updatedDeals)
        
        setDialogOpen(false)
        setSelectedProduct(null)
        setSuccess('Deal saved successfully!')
        setTimeout(() => setSuccess(null), 3000)
    }

    const handleRemoveDeal = (productId: string) => {
        const updatedDeals = deals.filter(d => d.product_id !== productId)
        localStorage.setItem('vendorDeals', JSON.stringify(updatedDeals))
        setDeals(updatedDeals)
        setSuccess('Deal removed successfully!')
        setTimeout(() => setSuccess(null), 3000)
    }

    const handleToggleDeal = (productId: string) => {
        const updatedDeals = deals.map(d => 
            d.product_id === productId ? { ...d, is_active: !d.is_active } : d
        )
        localStorage.setItem('vendorDeals', JSON.stringify(updatedDeals))
        setDeals(updatedDeals)
    }

    const productsWithoutDeals = products.filter(
        p => !deals.some(d => d.product_id === p.id)
    )

    if (loading) {
        return <LoadingSpinner message="Loading deals..." />
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Box>
                    <Typography variant="h4" fontWeight="bold" gutterBottom>
                        Deals Management
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Create and manage special offers on your products
                    </Typography>
                </Box>
                <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={loadData}
                >
                    Refresh
                </Button>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {success && (
                <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
                    {success}
                </Alert>
            )}

            {/* Active Deals */}
            <Paper sx={{ p: 3, mb: 4 }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Active Deals ({deals.filter(d => d.is_active).length})
                </Typography>
                
                {deals.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                        <LocalOffer sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography color="text.secondary">
                            No deals created yet. Create your first deal below!
                        </Typography>
                    </Box>
                ) : (
                    <Grid container spacing={3}>
                        {deals.map((deal) => (
                            <Grid item xs={12} sm={6} md={4} key={deal.product_id}>
                                <Card>
                                    <Box sx={{ position: 'relative' }}>
                                        {deal.product_image ? (
                                            <CardMedia
                                                component="img"
                                                height="140"
                                                image={deal.product_image}
                                                alt={deal.product_name}
                                            />
                                        ) : (
                                            <Box sx={{ height: 140, bgcolor: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                <Store sx={{ fontSize: 48, color: 'text.secondary' }} />
                                            </Box>
                                        )}
                                        <Chip
                                            label={`${deal.discount_percentage}% OFF`}
                                            color="error"
                                            sx={{ position: 'absolute', top: 8, left: 8 }}
                                        />
                                        <Chip
                                            label={deal.is_active ? 'Active' : 'Paused'}
                                            color={deal.is_active ? 'success' : 'default'}
                                            size="small"
                                            sx={{ position: 'absolute', top: 8, right: 8 }}
                                        />
                                    </Box>
                                    <CardContent>
                                        <Typography variant="subtitle1" fontWeight="bold" noWrap>
                                            {deal.product_name}
                                        </Typography>
                                        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, mt: 1 }}>
                                            <Typography variant="h6" color="error">
                                                ₹{deal.deal_price.toFixed(0)}
                                            </Typography>
                                            <Typography
                                                variant="body2"
                                                color="text.secondary"
                                                sx={{ textDecoration: 'line-through' }}
                                            >
                                                ₹{deal.original_price}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                /{deal.unit}
                                            </Typography>
                                        </Box>
                                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                                            Valid: {new Date(deal.start_date).toLocaleDateString()} - {new Date(deal.end_date).toLocaleDateString()}
                                        </Typography>
                                    </CardContent>
                                    <CardActions>
                                        <FormControlLabel
                                            control={
                                                <Switch
                                                    checked={deal.is_active}
                                                    onChange={() => handleToggleDeal(deal.product_id)}
                                                    size="small"
                                                />
                                            }
                                            label={deal.is_active ? 'Active' : 'Paused'}
                                        />
                                        <Box sx={{ flexGrow: 1 }} />
                                        <IconButton
                                            size="small"
                                            onClick={() => {
                                                const product = products.find(p => p.id === deal.product_id)
                                                if (product) {
                                                    setSelectedProduct(product)
                                                    setDealForm({
                                                        discount_percentage: deal.discount_percentage,
                                                        start_date: deal.start_date,
                                                        end_date: deal.end_date,
                                                        is_active: deal.is_active,
                                                    })
                                                    setDialogOpen(true)
                                                }
                                            }}
                                        >
                                            <Edit />
                                        </IconButton>
                                        <IconButton
                                            size="small"
                                            color="error"
                                            onClick={() => handleRemoveDeal(deal.product_id)}
                                        >
                                            <Delete />
                                        </IconButton>
                                    </CardActions>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                )}
            </Paper>

            {/* Products Without Deals */}
            <Paper sx={{ p: 3 }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Add Deal to Product
                </Typography>
                
                {productsWithoutDeals.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                        <Typography color="text.secondary">
                            {products.length === 0 
                                ? 'No products available. Add products first.'
                                : 'All products have deals. Edit existing deals above.'}
                        </Typography>
                        {products.length === 0 && (
                            <Button
                                variant="contained"
                                sx={{ mt: 2 }}
                                onClick={() => navigate('/products/new')}
                            >
                                Add Product
                            </Button>
                        )}
                    </Box>
                ) : (
                    <Grid container spacing={2}>
                        {productsWithoutDeals.map((product) => {
                            const productName = typeof product.name === 'object'
                                ? product.name.originalText
                                : product.name

                            return (
                                <Grid item xs={12} sm={6} md={4} lg={3} key={product.id}>
                                    <Card variant="outlined">
                                        <CardContent sx={{ pb: 1 }}>
                                            <Typography variant="subtitle2" noWrap>
                                                {productName}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                ₹{product.basePrice}/{product.unit}
                                            </Typography>
                                        </CardContent>
                                        <CardActions>
                                            <Button
                                                size="small"
                                                startIcon={<Add />}
                                                onClick={() => handleCreateDeal(product)}
                                                fullWidth
                                            >
                                                Create Deal
                                            </Button>
                                        </CardActions>
                                    </Card>
                                </Grid>
                            )
                        })}
                    </Grid>
                )}
            </Paper>

            {/* Create/Edit Deal Dialog */}
            <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>
                    {selectedProduct ? `Create Deal for ${typeof selectedProduct.name === 'object' ? selectedProduct.name.originalText : selectedProduct.name}` : 'Create Deal'}
                </DialogTitle>
                <DialogContent>
                    {selectedProduct && (
                        <Box sx={{ pt: 2 }}>
                            <Box sx={{ mb: 3 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                    Original Price: ₹{selectedProduct.basePrice}/{selectedProduct.unit}
                                </Typography>
                            </Box>

                            <Box sx={{ mb: 3 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                    Discount Percentage: {dealForm.discount_percentage}%
                                </Typography>
                                <Slider
                                    value={dealForm.discount_percentage}
                                    onChange={(_, value) => setDealForm(prev => ({
                                        ...prev,
                                        discount_percentage: value as number
                                    }))}
                                    min={5}
                                    max={50}
                                    step={5}
                                    marks={[
                                        { value: 5, label: '5%' },
                                        { value: 25, label: '25%' },
                                        { value: 50, label: '50%' },
                                    ]}
                                />
                                <Typography variant="body1" color="primary" sx={{ mt: 1 }}>
                                    Deal Price: ₹{(selectedProduct.basePrice * (1 - dealForm.discount_percentage / 100)).toFixed(0)}/{selectedProduct.unit}
                                </Typography>
                            </Box>

                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <TextField
                                        label="Start Date"
                                        type="date"
                                        fullWidth
                                        value={dealForm.start_date}
                                        onChange={(e) => setDealForm(prev => ({
                                            ...prev,
                                            start_date: e.target.value
                                        }))}
                                        InputLabelProps={{ shrink: true }}
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <TextField
                                        label="End Date"
                                        type="date"
                                        fullWidth
                                        value={dealForm.end_date}
                                        onChange={(e) => setDealForm(prev => ({
                                            ...prev,
                                            end_date: e.target.value
                                        }))}
                                        InputLabelProps={{ shrink: true }}
                                    />
                                </Grid>
                            </Grid>

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={dealForm.is_active}
                                        onChange={(e) => setDealForm(prev => ({
                                            ...prev,
                                            is_active: e.target.checked
                                        }))}
                                    />
                                }
                                label="Activate deal immediately"
                                sx={{ mt: 2 }}
                            />
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
                    <Button variant="contained" onClick={handleSaveDeal}>
                        Save Deal
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    )
}
