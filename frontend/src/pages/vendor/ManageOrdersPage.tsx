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
} from '@mui/material'
import {
    Visibility,
    LocalShipping,
    CheckCircle,
    Cancel,
    Refresh,
} from '@mui/icons-material'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'

interface Order {
    id: string
    buyer_name: string
    buyer_email: string
    product_name: string
    quantity: number
    unit: string
    total_amount: number
    status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled'
    created_at: string
    updated_at: string
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

export const ManageOrdersPage: React.FC = () => {
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [orders, setOrders] = useState<Order[]>([])
    const [tabValue, setTabValue] = useState(0)
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
    const [detailsOpen, setDetailsOpen] = useState(false)
    const [statusFilter, setStatusFilter] = useState('all')

    useEffect(() => {
        loadOrders()
    }, [])

    const loadOrders = async () => {
        setLoading(true)
        setError(null)
        try {
            // Mock orders data - in production, this would come from an API
            const mockOrders: Order[] = [
                {
                    id: 'ORD001',
                    buyer_name: 'Rahul Kumar',
                    buyer_email: 'rahul@example.com',
                    product_name: 'Fresh Tomatoes',
                    quantity: 10,
                    unit: 'kg',
                    total_amount: 500,
                    status: 'pending',
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                },
                {
                    id: 'ORD002',
                    buyer_name: 'Priya Sharma',
                    buyer_email: 'priya@example.com',
                    product_name: 'Organic Potatoes',
                    quantity: 20,
                    unit: 'kg',
                    total_amount: 800,
                    status: 'confirmed',
                    created_at: new Date(Date.now() - 86400000).toISOString(),
                    updated_at: new Date().toISOString(),
                },
                {
                    id: 'ORD003',
                    buyer_name: 'Amit Patel',
                    buyer_email: 'amit@example.com',
                    product_name: 'Green Chilies',
                    quantity: 5,
                    unit: 'kg',
                    total_amount: 250,
                    status: 'shipped',
                    created_at: new Date(Date.now() - 172800000).toISOString(),
                    updated_at: new Date().toISOString(),
                },
                {
                    id: 'ORD004',
                    buyer_name: 'Sneha Gupta',
                    buyer_email: 'sneha@example.com',
                    product_name: 'Fresh Carrots',
                    quantity: 15,
                    unit: 'kg',
                    total_amount: 600,
                    status: 'delivered',
                    created_at: new Date(Date.now() - 259200000).toISOString(),
                    updated_at: new Date().toISOString(),
                },
            ]
            setOrders(mockOrders)
        } catch (err) {
            setError('Failed to load orders')
        } finally {
            setLoading(false)
        }
    }

    const handleUpdateStatus = async (orderId: string, newStatus: string) => {
        try {
            // In production, this would be an API call
            setOrders(prev => prev.map(order => 
                order.id === orderId 
                    ? { ...order, status: newStatus as Order['status'], updated_at: new Date().toISOString() }
                    : order
            ))
            setDetailsOpen(false)
        } catch (err) {
            setError('Failed to update order status')
        }
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
                            <TableCell>Amount</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Date</TableCell>
                            <TableCell>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredOrders.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                                    <Typography color="text.secondary">
                                        No orders found
                                    </Typography>
                                </TableCell>
                            </TableRow>
                        ) : (
                            filteredOrders.map((order) => (
                                <TableRow key={order.id}>
                                    <TableCell>{order.id}</TableCell>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Avatar sx={{ width: 32, height: 32 }}>
                                                {order.buyer_name.charAt(0)}
                                            </Avatar>
                                            {order.buyer_name}
                                        </Box>
                                    </TableCell>
                                    <TableCell>{order.product_name}</TableCell>
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
                                        <IconButton
                                            size="small"
                                            onClick={() => {
                                                setSelectedOrder(order)
                                                setDetailsOpen(true)
                                            }}
                                        >
                                            <Visibility />
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
                        <Box>
                            <Typography variant="subtitle2" color="text.secondary">Order ID</Typography>
                            <Typography variant="body1" sx={{ mb: 2 }}>{selectedOrder.id}</Typography>

                            <Typography variant="subtitle2" color="text.secondary">Customer</Typography>
                            <Typography variant="body1" sx={{ mb: 2 }}>
                                {selectedOrder.buyer_name} ({selectedOrder.buyer_email})
                            </Typography>

                            <Typography variant="subtitle2" color="text.secondary">Product</Typography>
                            <Typography variant="body1" sx={{ mb: 2 }}>
                                {selectedOrder.product_name} - {selectedOrder.quantity} {selectedOrder.unit}
                            </Typography>

                            <Typography variant="subtitle2" color="text.secondary">Total Amount</Typography>
                            <Typography variant="body1" sx={{ mb: 2 }}>₹{selectedOrder.total_amount}</Typography>

                            <Typography variant="subtitle2" color="text.secondary">Current Status</Typography>
                            <Chip 
                                label={selectedOrder.status.charAt(0).toUpperCase() + selectedOrder.status.slice(1)} 
                                color={getStatusColor(selectedOrder.status) as any}
                                sx={{ mb: 2 }}
                            />

                            {selectedOrder.status !== 'delivered' && selectedOrder.status !== 'cancelled' && (
                                <Box sx={{ mt: 3 }}>
                                    <Typography variant="subtitle2" sx={{ mb: 1 }}>Update Status</Typography>
                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                        {selectedOrder.status === 'pending' && (
                                            <>
                                                <Button
                                                    variant="contained"
                                                    color="success"
                                                    startIcon={<CheckCircle />}
                                                    onClick={() => handleUpdateStatus(selectedOrder.id, 'confirmed')}
                                                >
                                                    Confirm
                                                </Button>
                                                <Button
                                                    variant="outlined"
                                                    color="error"
                                                    startIcon={<Cancel />}
                                                    onClick={() => handleUpdateStatus(selectedOrder.id, 'cancelled')}
                                                >
                                                    Cancel
                                                </Button>
                                            </>
                                        )}
                                        {selectedOrder.status === 'confirmed' && (
                                            <Button
                                                variant="contained"
                                                startIcon={<LocalShipping />}
                                                onClick={() => handleUpdateStatus(selectedOrder.id, 'shipped')}
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
                    <Button onClick={() => setDetailsOpen(false)}>Close</Button>
                </DialogActions>
            </Dialog>
        </Container>
    )
}
