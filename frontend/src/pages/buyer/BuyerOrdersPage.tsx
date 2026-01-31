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
    Alert,
    Card,
    CardContent,
    Grid,
    Divider,
} from '@mui/material'
import {
    Visibility,
    Refresh,
    Chat,
    Cancel,
    LocalShipping,
    ShoppingBag,
    AccessTime,
    CheckCircle,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { orderService, Order } from '../../services/orderService'

const getStatusColor = (status: string): 'warning' | 'info' | 'primary' | 'success' | 'error' | 'default' => {
    switch (status) {
        case 'pending': return 'warning'
        case 'confirmed': return 'info'
        case 'shipped': return 'primary'
        case 'delivered': return 'success'
        case 'cancelled': return 'error'
        default: return 'default'
    }
}

const getStatusIcon = (status: string) => {
    switch (status) {
        case 'pending': return <AccessTime />
        case 'confirmed': return <CheckCircle />
        case 'shipped': return <LocalShipping />
        case 'delivered': return <ShoppingBag />
        case 'cancelled': return <Cancel />
        default: return <ShoppingBag />
    }
}

export const BuyerOrdersPage: React.FC = () => {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [orders, setOrders] = useState<Order[]>([])
    const [tabValue, setTabValue] = useState(0)
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
    const [detailsOpen, setDetailsOpen] = useState(false)
    const [cancelDialogOpen, setCancelDialogOpen] = useState(false)
    const [actionLoading, setActionLoading] = useState(false)

    const tabStatuses = ['all', 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled']

    useEffect(() => {
        loadOrders()
    }, [tabValue])

    const loadOrders = async () => {
        setLoading(true)
        setError(null)
        try {
            const status = tabStatuses[tabValue] === 'all' ? undefined : tabStatuses[tabValue]
            const response = await orderService.getBuyerOrders(status)
            setOrders(response.orders)
        } catch (err) {
            console.error('Failed to load orders:', err)
            setError(err instanceof Error ? err.message : 'Failed to load orders')
        } finally {
            setLoading(false)
        }
    }

    const handleViewDetails = (order: Order) => {
        setSelectedOrder(order)
        setDetailsOpen(true)
    }

    const handleCancelOrder = async () => {
        if (!selectedOrder) return
        
        setActionLoading(true)
        try {
            await orderService.cancelOrder(selectedOrder.id)
            setCancelDialogOpen(false)
            setDetailsOpen(false)
            loadOrders()
        } catch (err) {
            console.error('Failed to cancel order:', err)
            setError(err instanceof Error ? err.message : 'Failed to cancel order')
        } finally {
            setActionLoading(false)
        }
    }

    const handleContactVendor = (order: Order) => {
        navigate(`/chat?vendor=${order.vendor_id}&product=${order.product_id}`)
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
    }

    const filteredOrders = orders

    // Order statistics
    const stats = {
        total: orders.length,
        pending: orders.filter(o => o.status === 'pending').length,
        active: orders.filter(o => ['confirmed', 'shipped'].includes(o.status)).length,
        completed: orders.filter(o => o.status === 'delivered').length,
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" fontWeight={600} gutterBottom>
                    My Orders
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Track and manage your orders
                </Typography>
            </Box>

            {/* Stats Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={6} md={3}>
                    <Card sx={{ bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                        <CardContent>
                            <Typography variant="h3" fontWeight={700}>{stats.total}</Typography>
                            <Typography variant="body2">Total Orders</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                    <Card sx={{ bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                        <CardContent>
                            <Typography variant="h3" fontWeight={700}>{stats.pending}</Typography>
                            <Typography variant="body2">Pending</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                    <Card sx={{ bgcolor: 'info.light', color: 'info.contrastText' }}>
                        <CardContent>
                            <Typography variant="h3" fontWeight={700}>{stats.active}</Typography>
                            <Typography variant="body2">Active</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                    <Card sx={{ bgcolor: 'success.light', color: 'success.contrastText' }}>
                        <CardContent>
                            <Typography variant="h3" fontWeight={700}>{stats.completed}</Typography>
                            <Typography variant="body2">Completed</Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            <Paper sx={{ mb: 4 }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
                    <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
                        <Tab label="All Orders" />
                        <Tab label="Pending" />
                        <Tab label="Confirmed" />
                        <Tab label="Shipped" />
                        <Tab label="Delivered" />
                        <Tab label="Cancelled" />
                    </Tabs>
                </Box>

                <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button startIcon={<Refresh />} onClick={loadOrders}>
                        Refresh
                    </Button>
                </Box>

                {loading ? (
                    <Box sx={{ py: 8, display: 'flex', justifyContent: 'center' }}>
                        <LoadingSpinner message="Loading orders..." />
                    </Box>
                ) : filteredOrders.length === 0 ? (
                    <Box sx={{ py: 8, textAlign: 'center' }}>
                        <ShoppingBag sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                            No orders found
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            Start shopping to see your orders here
                        </Typography>
                        <Button 
                            variant="contained" 
                            onClick={() => navigate('/products')}
                        >
                            Browse Products
                        </Button>
                    </Box>
                ) : (
                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Order ID</TableCell>
                                    <TableCell>Product</TableCell>
                                    <TableCell>Vendor</TableCell>
                                    <TableCell>Quantity</TableCell>
                                    <TableCell>Total</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>Date</TableCell>
                                    <TableCell align="right">Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {filteredOrders.map((order) => (
                                    <TableRow key={order.id} hover>
                                        <TableCell>
                                            <Typography variant="body2" fontWeight={500}>
                                                #{order.id.slice(0, 8)}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                                <Avatar 
                                                    src={order.product_image} 
                                                    variant="rounded"
                                                    sx={{ width: 48, height: 48 }}
                                                >
                                                    <ShoppingBag />
                                                </Avatar>
                                                <Typography variant="body2">
                                                    {order.product_name}
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>{order.vendor_name}</TableCell>
                                        <TableCell>
                                            {order.quantity} {order.unit}
                                        </TableCell>
                                        <TableCell>₹{order.total_amount.toLocaleString()}</TableCell>
                                        <TableCell>
                                            <Chip
                                                icon={getStatusIcon(order.status)}
                                                label={order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                                                color={getStatusColor(order.status)}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            {formatDate(order.created_at)}
                                        </TableCell>
                                        <TableCell align="right">
                                            <IconButton
                                                size="small"
                                                onClick={() => handleViewDetails(order)}
                                                title="View Details"
                                            >
                                                <Visibility />
                                            </IconButton>
                                            <IconButton
                                                size="small"
                                                onClick={() => handleContactVendor(order)}
                                                title="Contact Vendor"
                                            >
                                                <Chat />
                                            </IconButton>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                )}
            </Paper>

            {/* Order Details Dialog */}
            <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Order Details</DialogTitle>
                <DialogContent>
                    {selectedOrder && (
                        <Box sx={{ pt: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                <Avatar 
                                    src={selectedOrder.product_image} 
                                    variant="rounded"
                                    sx={{ width: 80, height: 80 }}
                                >
                                    <ShoppingBag />
                                </Avatar>
                                <Box>
                                    <Typography variant="h6">{selectedOrder.product_name}</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        from {selectedOrder.vendor_name}
                                    </Typography>
                                </Box>
                            </Box>

                            <Divider sx={{ my: 2 }} />

                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Order ID</Typography>
                                    <Typography variant="body1">#{selectedOrder.id.slice(0, 8)}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Status</Typography>
                                    <Chip
                                        label={selectedOrder.status.charAt(0).toUpperCase() + selectedOrder.status.slice(1)}
                                        color={getStatusColor(selectedOrder.status)}
                                        size="small"
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Quantity</Typography>
                                    <Typography variant="body1">{selectedOrder.quantity} {selectedOrder.unit}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Your Offer</Typography>
                                    <Typography variant="body1">₹{selectedOrder.offered_price}/{selectedOrder.unit}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Original Price</Typography>
                                    <Typography variant="body1">₹{selectedOrder.original_price}/{selectedOrder.unit}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Total Amount</Typography>
                                    <Typography variant="h6" color="primary">₹{selectedOrder.total_amount.toLocaleString()}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Ordered On</Typography>
                                    <Typography variant="body1">{formatDate(selectedOrder.created_at)}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Last Updated</Typography>
                                    <Typography variant="body1">{formatDate(selectedOrder.updated_at)}</Typography>
                                </Grid>
                                {selectedOrder.tracking_number && (
                                    <Grid item xs={12}>
                                        <Typography variant="body2" color="text.secondary">Tracking Number</Typography>
                                        <Typography variant="body1">{selectedOrder.tracking_number}</Typography>
                                    </Grid>
                                )}
                                {selectedOrder.estimated_delivery && (
                                    <Grid item xs={12}>
                                        <Typography variant="body2" color="text.secondary">Estimated Delivery</Typography>
                                        <Typography variant="body1">{selectedOrder.estimated_delivery}</Typography>
                                    </Grid>
                                )}
                                {selectedOrder.message && (
                                    <Grid item xs={12}>
                                        <Typography variant="body2" color="text.secondary">Your Message</Typography>
                                        <Typography variant="body1">{selectedOrder.message}</Typography>
                                    </Grid>
                                )}
                            </Grid>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    {selectedOrder?.status === 'pending' && (
                        <Button 
                            color="error" 
                            onClick={() => setCancelDialogOpen(true)}
                            startIcon={<Cancel />}
                        >
                            Cancel Order
                        </Button>
                    )}
                    <Button onClick={() => handleContactVendor(selectedOrder!)}>
                        <Chat sx={{ mr: 1 }} /> Contact Vendor
                    </Button>
                    <Button onClick={() => setDetailsOpen(false)}>Close</Button>
                </DialogActions>
            </Dialog>

            {/* Cancel Confirmation Dialog */}
            <Dialog open={cancelDialogOpen} onClose={() => setCancelDialogOpen(false)}>
                <DialogTitle>Cancel Order?</DialogTitle>
                <DialogContent>
                    <Typography>
                        Are you sure you want to cancel this order? This action cannot be undone.
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCancelDialogOpen(false)}>Keep Order</Button>
                    <Button 
                        color="error" 
                        variant="contained" 
                        onClick={handleCancelOrder}
                        disabled={actionLoading}
                    >
                        {actionLoading ? 'Cancelling...' : 'Yes, Cancel Order'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    )
}

export default BuyerOrdersPage
