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
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Alert,
    Tabs,
    Tab,
    Avatar,
    TextField,
    Grid,
    Divider,
} from '@mui/material'
import {
    Visibility,
    LocalShipping,
    CheckCircle,
    Cancel,
    Refresh,
    Chat,
    ShoppingBag,
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

export const ManageOrdersPage: React.FC = () => {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [orders, setOrders] = useState<Order[]>([])
    const [tabValue, setTabValue] = useState(0)
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
    const [detailsOpen, setDetailsOpen] = useState(false)
    const [statusFilter, setStatusFilter] = useState('all')
    const [actionLoading, setActionLoading] = useState(false)
    const [trackingNumber, setTrackingNumber] = useState('')
    const [estimatedDelivery, setEstimatedDelivery] = useState('')

    useEffect(() => {
        loadOrders()
    }, [])

    const loadOrders = async () => {
        setLoading(true)
        setError(null)
        try {
            const response = await orderService.getVendorOrders()
            setOrders(response.orders)
        } catch (err) {
            console.error('Failed to load orders:', err)
            setError(err instanceof Error ? err.message : 'Failed to load orders')
        } finally {
            setLoading(false)
        }
    }

    const handleUpdateStatus = async (orderId: string, newStatus: string) => {
        setActionLoading(true)
        try {
            const trackingInfo = newStatus === 'shipped' ? {
                tracking_number: trackingNumber || undefined,
                estimated_delivery: estimatedDelivery || undefined,
            } : undefined
            
            await orderService.updateOrderStatus(orderId, newStatus, trackingInfo)
            setDetailsOpen(false)
            setTrackingNumber('')
            setEstimatedDelivery('')
            loadOrders()
        } catch (err) {
            console.error('Failed to update order:', err)
            setError(err instanceof Error ? err.message : 'Failed to update order status')
        } finally {
            setActionLoading(false)
        }
    }

    const handleContactBuyer = (order: Order) => {
        navigate(`/chat?buyer=${order.buyer_id}&product=${order.product_id}`)
    }

    const filteredOrders = orders.filter(order => {
        if (statusFilter !== 'all' && order.status !== statusFilter) return false
        if (tabValue === 1 && order.status !== 'pending') return false
        if (tabValue === 2 && !['confirmed', 'shipped'].includes(order.status)) return false
        if (tabValue === 3 && order.status !== 'delivered') return false
        return true
    })

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
    }

    if (loading) {
        return <LoadingSpinner message="Loading orders..." />
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Box>
                    <Typography variant="h4" fontWeight="bold" gutterBottom>
                        Manage Orders
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Track and manage your customer orders
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
                    <Tab label={`Pending (${orders.filter(o => o.status === 'pending').length})`} />
                    <Tab label={`In Progress (${orders.filter(o => ['confirmed', 'shipped'].includes(o.status)).length})`} />
                    <Tab label={`Completed (${orders.filter(o => o.status === 'delivered').length})`} />
                </Tabs>
            </Paper>

            {/* Filter */}
            <Box sx={{ mb: 3 }}>
                <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Status Filter</InputLabel>
                    <Select
                        value={statusFilter}
                        label="Status Filter"
                        onChange={(e) => setStatusFilter(e.target.value)}
                    >
                        <MenuItem value="all">All</MenuItem>
                        <MenuItem value="pending">Pending</MenuItem>
                        <MenuItem value="confirmed">Confirmed</MenuItem>
                        <MenuItem value="shipped">Shipped</MenuItem>
                        <MenuItem value="delivered">Delivered</MenuItem>
                        <MenuItem value="cancelled">Cancelled</MenuItem>
                    </Select>
                </FormControl>
            </Box>

            {/* Orders Table */}
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Order ID</TableCell>
                            <TableCell>Customer</TableCell>
                            <TableCell>Product</TableCell>
                            <TableCell>Quantity</TableCell>
                            <TableCell>Offer</TableCell>
                            <TableCell>Total</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Date</TableCell>
                            <TableCell>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredOrders.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={9} align="center" sx={{ py: 8 }}>
                                    <ShoppingBag sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                                    <Typography color="text.secondary" variant="h6">
                                        No orders found
                                    </Typography>
                                    <Typography color="text.secondary" variant="body2">
                                        Orders from buyers will appear here
                                    </Typography>
                                </TableCell>
                            </TableRow>
                        ) : (
                            filteredOrders.map((order) => (
                                <TableRow key={order.id} hover>
                                    <TableCell>
                                        <Typography variant="body2" fontWeight={500}>
                                            #{order.id.slice(0, 8)}
                                        </Typography>
                                    </TableCell>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Avatar sx={{ width: 32, height: 32 }}>
                                                {order.buyer_name?.charAt(0) || 'B'}
                                            </Avatar>
                                            <Box>
                                                <Typography variant="body2">{order.buyer_name || 'Unknown'}</Typography>
                                                <Typography variant="caption" color="text.secondary">
                                                    {order.buyer_email}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </TableCell>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Avatar 
                                                src={order.product_image} 
                                                variant="rounded"
                                                sx={{ width: 40, height: 40 }}
                                            >
                                                <ShoppingBag />
                                            </Avatar>
                                            <Typography variant="body2">{order.product_name}</Typography>
                                        </Box>
                                    </TableCell>
                                    <TableCell>{order.quantity} {order.unit}</TableCell>
                                    <TableCell>₹{order.offered_price}/{order.unit}</TableCell>
                                    <TableCell>
                                        <Typography fontWeight={500}>₹{order.total_amount.toLocaleString()}</Typography>
                                    </TableCell>
                                    <TableCell>
                                        <Chip 
                                            label={order.status.charAt(0).toUpperCase() + order.status.slice(1)} 
                                            color={getStatusColor(order.status)}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>{formatDate(order.created_at)}</TableCell>
                                    <TableCell>
                                        <IconButton
                                            size="small"
                                            onClick={() => {
                                                setSelectedOrder(order)
                                                setDetailsOpen(true)
                                            }}
                                            title="View Details"
                                        >
                                            <Visibility />
                                        </IconButton>
                                        <IconButton
                                            size="small"
                                            onClick={() => handleContactBuyer(order)}
                                            title="Contact Buyer"
                                        >
                                            <Chat />
                                        </IconButton>
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
                                    <Chip
                                        label={selectedOrder.status.charAt(0).toUpperCase() + selectedOrder.status.slice(1)}
                                        color={getStatusColor(selectedOrder.status)}
                                        size="small"
                                    />
                                </Box>
                            </Box>
                            
                            <Divider sx={{ my: 2 }} />

                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Order ID</Typography>
                                    <Typography variant="body1">#{selectedOrder.id.slice(0, 8)}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Customer</Typography>
                                    <Typography variant="body1">{selectedOrder.buyer_name}</Typography>
                                    <Typography variant="caption" color="text.secondary">{selectedOrder.buyer_email}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Quantity</Typography>
                                    <Typography variant="body1">{selectedOrder.quantity} {selectedOrder.unit}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Original Price</Typography>
                                    <Typography variant="body1">₹{selectedOrder.original_price}/{selectedOrder.unit}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Offered Price</Typography>
                                    <Typography variant="body1" color="primary.main" fontWeight={500}>
                                        ₹{selectedOrder.offered_price}/{selectedOrder.unit}
                                    </Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Total Amount</Typography>
                                    <Typography variant="h6" color="success.main">₹{selectedOrder.total_amount.toLocaleString()}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Ordered On</Typography>
                                    <Typography variant="body1">{formatDate(selectedOrder.created_at)}</Typography>
                                </Grid>
                                {selectedOrder.message && (
                                    <Grid item xs={12}>
                                        <Typography variant="body2" color="text.secondary">Buyer's Message</Typography>
                                        <Typography variant="body1">{selectedOrder.message}</Typography>
                                    </Grid>
                                )}
                            </Grid>

                            {selectedOrder.status !== 'delivered' && selectedOrder.status !== 'cancelled' && (
                                <Box sx={{ mt: 3 }}>
                                    <Divider sx={{ mb: 2 }} />
                                    <Typography variant="subtitle1" fontWeight={500} sx={{ mb: 2 }}>Update Status</Typography>
                                    
                                    {selectedOrder.status === 'confirmed' && (
                                        <Box sx={{ mb: 2 }}>
                                            <TextField
                                                fullWidth
                                                size="small"
                                                label="Tracking Number (optional)"
                                                value={trackingNumber}
                                                onChange={(e) => setTrackingNumber(e.target.value)}
                                                sx={{ mb: 2 }}
                                            />
                                            <TextField
                                                fullWidth
                                                size="small"
                                                label="Estimated Delivery (optional)"
                                                value={estimatedDelivery}
                                                onChange={(e) => setEstimatedDelivery(e.target.value)}
                                                placeholder="e.g., 2-3 business days"
                                            />
                                        </Box>
                                    )}
                                    
                                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                        {selectedOrder.status === 'pending' && (
                                            <>
                                                <Button
                                                    variant="contained"
                                                    color="success"
                                                    startIcon={<CheckCircle />}
                                                    onClick={() => handleUpdateStatus(selectedOrder.id, 'confirmed')}
                                                    disabled={actionLoading}
                                                >
                                                    Accept Order
                                                </Button>
                                                <Button
                                                    variant="outlined"
                                                    color="error"
                                                    startIcon={<Cancel />}
                                                    onClick={() => handleUpdateStatus(selectedOrder.id, 'cancelled')}
                                                    disabled={actionLoading}
                                                >
                                                    Reject
                                                </Button>
                                            </>
                                        )}
                                        {selectedOrder.status === 'confirmed' && (
                                            <Button
                                                variant="contained"
                                                startIcon={<LocalShipping />}
                                                onClick={() => handleUpdateStatus(selectedOrder.id, 'shipped')}
                                                disabled={actionLoading}
                                            >
                                                Mark as Shipped
                                            </Button>
                                        )}
                                        {selectedOrder.status === 'shipped' && (
                                            <Button
                                                variant="contained"
                                                color="success"
                                                startIcon={<CheckCircle />}
                                                onClick={() => handleUpdateStatus(selectedOrder.id, 'delivered')}
                                                disabled={actionLoading}
                                            >
                                                Mark as Delivered
                                            </Button>
                                        )}
                                    </Box>
                                </Box>
                            )}
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => selectedOrder && handleContactBuyer(selectedOrder)}>
                        <Chat sx={{ mr: 1 }} /> Contact Buyer
                    </Button>
                    <Button onClick={() => setDetailsOpen(false)}>Close</Button>
                </DialogActions>
            </Dialog>
        </Container>
    )
}
