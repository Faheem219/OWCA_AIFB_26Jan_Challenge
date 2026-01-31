import React, { useState, useEffect } from 'react'
import {
    Container,
    Paper,
    Typography,
    Box,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    Button,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Tabs,
    Tab,
    Avatar,
    Rating,
    TextField,
    Alert,
} from '@mui/material'
import {
    Visibility,
    Refresh,
    Chat,
    Star,
    LocalShipping,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'

interface Order {
    id: string
    product_name: string
    product_image: string
    vendor_name: string
    vendor_id: string
    quantity: number
    unit: string
    total_amount: number
    status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled'
    created_at: string
    updated_at: string
    tracking_number?: string
    estimated_delivery?: string
}

const getStatusColor = (status: string) => {
    switch (status) {
        case 'pending': return 'warning'
        case 'confirmed': return 'info'
        case 'shipped': return 'primary'
        case 'delivered': return 'success'
        case 'cancelled': return 'error'
        default: return 'default'
    }
}

export const OrderHistoryPage: React.FC = () => {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [orders, setOrders] = useState<Order[]>([])
    const [tabValue, setTabValue] = useState(0)
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
    const [detailsOpen, setDetailsOpen] = useState(false)
    const [reviewOpen, setReviewOpen] = useState(false)
    const [rating, setRating] = useState(0)
    const [reviewText, setReviewText] = useState('')

    useEffect(() => {
        loadOrders()
    }, [])

    const loadOrders = async () => {
        setLoading(true)
        setError(null)
        try {
            // Mock orders - in production this would come from API
            const mockOrders: Order[] = [
                {
                    id: 'ORD001',
                    product_name: 'Fresh Tomatoes',
                    product_image: '/placeholder-product.jpg',
                    vendor_name: 'Green Farm Fresh',
                    vendor_id: 'v1',
                    quantity: 5,
                    unit: 'kg',
                    total_amount: 250,
                    status: 'delivered',
                    created_at: new Date(Date.now() - 604800000).toISOString(),
                    updated_at: new Date(Date.now() - 172800000).toISOString(),
                },
                {
                    id: 'ORD002',
                    product_name: 'Organic Potatoes',
                    product_image: '/placeholder-product.jpg',
                    vendor_name: 'Farm Direct',
                    vendor_id: 'v2',
                    quantity: 10,
                    unit: 'kg',
                    total_amount: 400,
                    status: 'shipped',
                    created_at: new Date(Date.now() - 259200000).toISOString(),
                    updated_at: new Date(Date.now() - 86400000).toISOString(),
                    tracking_number: 'TRK123456789',
                    estimated_delivery: new Date(Date.now() + 172800000).toISOString(),
                },
                {
                    id: 'ORD003',
                    product_name: 'Green Chilies',
                    product_image: '/placeholder-product.jpg',
                    vendor_name: 'Spice Garden',
                    vendor_id: 'v3',
                    quantity: 2,
                    unit: 'kg',
                    total_amount: 100,
                    status: 'confirmed',
                    created_at: new Date(Date.now() - 86400000).toISOString(),
                    updated_at: new Date().toISOString(),
                },
                {
                    id: 'ORD004',
                    product_name: 'Fresh Onions',
                    product_image: '/placeholder-product.jpg',
                    vendor_name: 'Village Produce',
                    vendor_id: 'v4',
                    quantity: 8,
                    unit: 'kg',
                    total_amount: 320,
                    status: 'pending',
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                },
            ]
            setOrders(mockOrders)
        } catch (err) {
            setError('Failed to load order history')
        } finally {
            setLoading(false)
        }
    }

    const filteredOrders = orders.filter(order => {
        if (tabValue === 1 && !['pending', 'confirmed'].includes(order.status)) return false
        if (tabValue === 2 && order.status !== 'shipped') return false
        if (tabValue === 3 && order.status !== 'delivered') return false
        return true
    })

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        })
    }

    const handleSubmitReview = () => {
        // In production, this would submit to API
        console.log('Submitting review:', { orderId: selectedOrder?.id, rating, reviewText })
        setReviewOpen(false)
        setRating(0)
        setReviewText('')
    }

    const handleContactVendor = (vendorId: string) => {
        navigate(`/chat?vendor=${vendorId}`)
    }

    if (loading) {
        return <LoadingSpinner message="Loading order history..." />
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Box>
                    <Typography variant="h4" fontWeight="bold" gutterBottom>
                        Order History
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Track your orders and view past purchases
                    </Typography>
                </Box>
                <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={loadOrders}
                >
                    Refresh
                </Button>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* Tabs */}
            <Paper sx={{ mb: 3 }}>
                <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
                    <Tab label={`All Orders (${orders.length})`} />
                    <Tab label={`Processing (${orders.filter(o => ['pending', 'confirmed'].includes(o.status)).length})`} />
                    <Tab label={`In Transit (${orders.filter(o => o.status === 'shipped').length})`} />
                    <Tab label={`Delivered (${orders.filter(o => o.status === 'delivered').length})`} />
                </Tabs>
            </Paper>

            {/* Orders Table */}
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Product</TableCell>
                            <TableCell>Vendor</TableCell>
                            <TableCell>Quantity</TableCell>
                            <TableCell>Amount</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Date</TableCell>
                            <TableCell>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredOrders.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                                    <Typography color="text.secondary">
                                        No orders found
                                    </Typography>
                                </TableCell>
                            </TableRow>
                        ) : (
                            filteredOrders.map((order) => (
                                <TableRow key={order.id}>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                            <Avatar 
                                                src={order.product_image} 
                                                variant="rounded"
                                                sx={{ width: 48, height: 48 }}
                                            />
                                            <Typography>{order.product_name}</Typography>
                                        </Box>
                                    </TableCell>
                                    <TableCell>{order.vendor_name}</TableCell>
                                    <TableCell>{order.quantity} {order.unit}</TableCell>
                                    <TableCell>₹{order.total_amount}</TableCell>
                                    <TableCell>
                                        <Chip 
                                            label={order.status.charAt(0).toUpperCase() + order.status.slice(1)} 
                                            color={getStatusColor(order.status) as any}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>{formatDate(order.created_at)}</TableCell>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', gap: 1 }}>
                                            <IconButton
                                                size="small"
                                                onClick={() => {
                                                    setSelectedOrder(order)
                                                    setDetailsOpen(true)
                                                }}
                                            >
                                                <Visibility />
                                            </IconButton>
                                            <IconButton
                                                size="small"
                                                onClick={() => handleContactVendor(order.vendor_id)}
                                            >
                                                <Chat />
                                            </IconButton>
                                            {order.status === 'delivered' && (
                                                <IconButton
                                                    size="small"
                                                    color="warning"
                                                    onClick={() => {
                                                        setSelectedOrder(order)
                                                        setReviewOpen(true)
                                                    }}
                                                >
                                                    <Star />
                                                </IconButton>
                                            )}
                                        </Box>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Order Details Dialog */}
            <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Order Details</DialogTitle>
                <DialogContent>
                    {selectedOrder && (
                        <Box>
                            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                                <Avatar 
                                    src={selectedOrder.product_image} 
                                    variant="rounded"
                                    sx={{ width: 80, height: 80 }}
                                />
                                <Box>
                                    <Typography variant="h6">{selectedOrder.product_name}</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        by {selectedOrder.vendor_name}
                                    </Typography>
                                </Box>
                            </Box>

                            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Order ID</Typography>
                                    <Typography variant="body1">{selectedOrder.id}</Typography>
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                                    <Chip 
                                        label={selectedOrder.status.charAt(0).toUpperCase() + selectedOrder.status.slice(1)} 
                                        color={getStatusColor(selectedOrder.status) as any}
                                        size="small"
                                    />
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Quantity</Typography>
                                    <Typography variant="body1">{selectedOrder.quantity} {selectedOrder.unit}</Typography>
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Total Amount</Typography>
                                    <Typography variant="body1">₹{selectedOrder.total_amount}</Typography>
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Order Date</Typography>
                                    <Typography variant="body1">{formatDate(selectedOrder.created_at)}</Typography>
                                </Box>
                                {selectedOrder.tracking_number && (
                                    <Box>
                                        <Typography variant="subtitle2" color="text.secondary">Tracking Number</Typography>
                                        <Typography variant="body1">{selectedOrder.tracking_number}</Typography>
                                    </Box>
                                )}
                            </Box>

                            {selectedOrder.status === 'shipped' && selectedOrder.estimated_delivery && (
                                <Paper sx={{ p: 2, mt: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <LocalShipping />
                                        <Box>
                                            <Typography variant="subtitle2">Estimated Delivery</Typography>
                                            <Typography variant="body1">
                                                {formatDate(selectedOrder.estimated_delivery)}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Paper>
                            )}
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDetailsOpen(false)}>Close</Button>
                    {selectedOrder && (
                        <Button 
                            variant="contained"
                            onClick={() => handleContactVendor(selectedOrder.vendor_id)}
                            startIcon={<Chat />}
                        >
                            Contact Vendor
                        </Button>
                    )}
                </DialogActions>
            </Dialog>

            {/* Review Dialog */}
            <Dialog open={reviewOpen} onClose={() => setReviewOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Write a Review</DialogTitle>
                <DialogContent>
                    {selectedOrder && (
                        <Box sx={{ pt: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>
                                {selectedOrder.product_name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                from {selectedOrder.vendor_name}
                            </Typography>
                            
                            <Box sx={{ my: 3 }}>
                                <Typography variant="subtitle2" gutterBottom>Rating</Typography>
                                <Rating
                                    value={rating}
                                    onChange={(_, newValue) => setRating(newValue || 0)}
                                    size="large"
                                />
                            </Box>

                            <TextField
                                label="Your Review"
                                multiline
                                rows={4}
                                fullWidth
                                value={reviewText}
                                onChange={(e) => setReviewText(e.target.value)}
                                placeholder="Share your experience with this product..."
                            />
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setReviewOpen(false)}>Cancel</Button>
                    <Button 
                        variant="contained"
                        onClick={handleSubmitReview}
                        disabled={rating === 0}
                    >
                        Submit Review
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    )
}
