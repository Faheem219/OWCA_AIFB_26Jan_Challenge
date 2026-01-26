import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Divider,
    Typography,
    Box,
} from '@mui/material'
import {
    Dashboard,
    Person,
    Chat,
    Store,
    ShoppingCart,
    Add,
    Inventory,
    Analytics,
    Settings,
    Help,
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../hooks/useAuth'
import { UserRole } from '../../types'

interface NavigationItem {
    key: string
    label: string
    icon: React.ReactNode
    path: string
    roles?: UserRole[]
    divider?: boolean
}

export const RoleBasedNavigation: React.FC = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const location = useLocation()
    const { user } = useAuth()

    if (!user) return null

    const navigationItems: NavigationItem[] = [
        {
            key: 'dashboard',
            label: t('navigation.dashboard'),
            icon: <Dashboard />,
            path: '/dashboard',
        },
        {
            key: 'profile',
            label: t('navigation.profile'),
            icon: <Person />,
            path: '/profile',
        },
        {
            key: 'chat',
            label: t('navigation.chat'),
            icon: <Chat />,
            path: '/chat',
        },
        {
            key: 'divider1',
            label: '',
            icon: null,
            path: '',
            divider: true,
        },
        // Vendor-specific items
        {
            key: 'my-products',
            label: t('products.myProducts') || 'My Products',
            icon: <Inventory />,
            path: '/products/my-products',
            roles: ['VENDOR'],
        },
        {
            key: 'add-product',
            label: t('products.addProduct') || 'Add Product',
            icon: <Add />,
            path: '/products/create',
            roles: ['VENDOR'],
        },
        {
            key: 'vendor-analytics',
            label: t('analytics.title') || 'Analytics',
            icon: <Analytics />,
            path: '/analytics',
            roles: ['VENDOR'],
        },
        // Buyer-specific items
        {
            key: 'browse-products',
            label: t('products.browse') || 'Browse Products',
            icon: <Store />,
            path: '/products',
            roles: ['BUYER'],
        },
        {
            key: 'my-orders',
            label: t('orders.myOrders') || 'My Orders',
            icon: <ShoppingCart />,
            path: '/orders',
            roles: ['BUYER'],
        },
        {
            key: 'divider2',
            label: '',
            icon: null,
            path: '',
            divider: true,
        },
        // Common items
        {
            key: 'settings',
            label: t('common.settings') || 'Settings',
            icon: <Settings />,
            path: '/settings',
        },
        {
            key: 'help',
            label: t('common.help') || 'Help & Support',
            icon: <Help />,
            path: '/help',
        },
    ]

    const filteredItems = navigationItems.filter(item => {
        if (item.divider) return true
        if (!item.roles) return true
        return item.roles.includes(user.role)
    })

    const handleNavigation = (path: string) => {
        if (path) {
            navigate(path)
        }
    }

    const isActive = (path: string) => {
        if (!path) return false
        return location.pathname === path || location.pathname.startsWith(path + '/')
    }

    return (
        <Box>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <Typography variant="h6" color="primary" gutterBottom>
                    {user.role === 'VENDOR' ? t('auth.vendor') : t('auth.buyer')}
                </Typography>
                <Typography variant="body2" color="text.secondary" noWrap>
                    {user.email}
                </Typography>
            </Box>

            <List sx={{ py: 0 }}>
                {filteredItems.map((item) => {
                    if (item.divider) {
                        return <Divider key={item.key} sx={{ my: 1 }} />
                    }

                    return (
                        <ListItem key={item.key} disablePadding>
                            <ListItemButton
                                selected={isActive(item.path)}
                                onClick={() => handleNavigation(item.path)}
                                sx={{
                                    py: 1.5,
                                    '&.Mui-selected': {
                                        backgroundColor: 'primary.light',
                                        color: 'primary.contrastText',
                                        '&:hover': {
                                            backgroundColor: 'primary.main',
                                        },
                                        '& .MuiListItemIcon-root': {
                                            color: 'primary.contrastText',
                                        },
                                    },
                                }}
                            >
                                <ListItemIcon
                                    sx={{
                                        minWidth: 40,
                                        color: isActive(item.path) ? 'inherit' : 'text.secondary',
                                    }}
                                >
                                    {item.icon}
                                </ListItemIcon>
                                <ListItemText
                                    primary={item.label}
                                    primaryTypographyProps={{
                                        fontSize: '0.875rem',
                                        fontWeight: isActive(item.path) ? 600 : 400,
                                    }}
                                />
                            </ListItemButton>
                        </ListItem>
                    )
                })}
            </List>
        </Box>
    )
}