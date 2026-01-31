import React, { useState } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import {
    AppBar,
    Toolbar,
    Typography,
    Button,
    IconButton,
    Menu,
    MenuItem,
    Box,
    Avatar,
    Chip,
    useTheme,
    useMediaQuery,
} from '@mui/material'
import {
    Menu as MenuIcon,
    ShoppingCart,
    Chat,
    Notifications,
} from '@mui/icons-material'
import { useAuth } from '../../hooks/useAuth'
import { LanguageSelectorDropdown } from '../common/LanguageSelectorDropdown'
import useTranslation from '../../hooks/useTranslation'

export const Header: React.FC = () => {
    const navigate = useNavigate()
    const theme = useTheme()
    const isMobile = useMediaQuery(theme.breakpoints.down('md'))
    const { user, logout } = useAuth()
    const { t } = useTranslation()

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
    const [mobileMenuAnchor, setMobileMenuAnchor] = useState<null | HTMLElement>(null)

    const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget)
    }

    const handleMobileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
        setMobileMenuAnchor(event.currentTarget)
    }

    const handleMenuClose = () => {
        setAnchorEl(null)
        setMobileMenuAnchor(null)
    }

    const handleLogout = async () => {
        await logout()
        handleMenuClose()
        navigate('/')
    }

    const renderDesktopMenu = () => (
        <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 2 }}>
            <Button
                color="inherit"
                component={RouterLink}
                to="/products"
                sx={{ textTransform: 'none' }}
            >
                {t('navigation.products')}
            </Button>

            {user && (
                <>
                    <IconButton color="inherit" component={RouterLink} to="/chat">
                        <Chat />
                    </IconButton>
                    <IconButton color="inherit">
                        <Notifications />
                    </IconButton>
                    {user.role !== 'VENDOR' && (
                        <IconButton color="inherit" component={RouterLink} to="/buyer/orders">
                            <ShoppingCart />
                        </IconButton>
                    )}
                </>
            )}

            <LanguageSelectorDropdown variant="minimal" />

            {user ? (
                <IconButton onClick={handleProfileMenuOpen} color="inherit">
                    <Avatar sx={{ width: 32, height: 32 }}>
                        {user.email.charAt(0).toUpperCase()}
                    </Avatar>
                </IconButton>
            ) : (
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                        color="inherit"
                        component={RouterLink}
                        to="/login"
                        sx={{ textTransform: 'none' }}
                    >
                        {t('navigation.login')}
                    </Button>
                    <Button
                        variant="outlined"
                        color="inherit"
                        component={RouterLink}
                        to="/register"
                        sx={{ textTransform: 'none' }}
                    >
                        {t('navigation.register')}
                    </Button>
                </Box>
            )}
        </Box>
    )

    const renderMobileMenu = () => (
        <Box sx={{ display: { xs: 'flex', md: 'none' } }}>
            <IconButton color="inherit" onClick={handleMobileMenuOpen}>
                <MenuIcon />
            </IconButton>
        </Box>
    )

    return (
        <>
            <AppBar position="sticky" elevation={1}>
                <Toolbar>
                    <Typography
                        variant="h6"
                        component={RouterLink}
                        to="/"
                        sx={{
                            flexGrow: 1,
                            textDecoration: 'none',
                            color: 'inherit',
                            fontWeight: 600,
                        }}
                    >
                        Mandi Market
                    </Typography>

                    {user && (
                        <Chip
                            label={user.role}
                            size="small"
                            color="secondary"
                            sx={{ mr: 2, display: { xs: 'none', sm: 'flex' } }}
                        />
                    )}

                    {isMobile ? renderMobileMenu() : renderDesktopMenu()}
                </Toolbar>
            </AppBar>

            {/* Profile Menu */}
            <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
            >
                <MenuItem onClick={() => { navigate('/profile'); handleMenuClose() }}>
                    {t('navigation.profile')}
                </MenuItem>
                <MenuItem onClick={() => { navigate('/dashboard'); handleMenuClose() }}>
                    {t('navigation.dashboard')}
                </MenuItem>
                {user?.role === 'BUYER' && (
                    <MenuItem onClick={() => { navigate('/buyer/orders'); handleMenuClose() }}>
                        My Orders
                    </MenuItem>
                )}
                {user?.role === 'VENDOR' && (
                    <>
                        <MenuItem onClick={() => { navigate('/orders'); handleMenuClose() }}>
                            Manage Orders
                        </MenuItem>
                        <MenuItem onClick={() => { navigate('/products/create'); handleMenuClose() }}>
                            {t('products.addProduct', 'Add Product')}
                        </MenuItem>
                    </>
                )}
                <MenuItem onClick={handleLogout}>
                    {t('navigation.logout')}
                </MenuItem>
            </Menu>

            {/* Mobile Menu */}
            <Menu
                anchorEl={mobileMenuAnchor}
                open={Boolean(mobileMenuAnchor)}
                onClose={handleMenuClose}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
            >
                <MenuItem onClick={() => { navigate('/products'); handleMenuClose() }}>
                    {t('navigation.products')}
                </MenuItem>
                {user ? (
                    <>
                        <MenuItem onClick={() => { navigate('/dashboard'); handleMenuClose() }}>
                            {t('navigation.dashboard')}
                        </MenuItem>
                        <MenuItem onClick={() => { navigate('/chat'); handleMenuClose() }}>
                            {t('navigation.chat')}
                        </MenuItem>
                        <MenuItem onClick={() => { navigate('/profile'); handleMenuClose() }}>
                            {t('navigation.profile')}
                        </MenuItem>
                        {user.role === 'BUYER' && (
                            <MenuItem onClick={() => { navigate('/buyer/orders'); handleMenuClose() }}>
                                My Orders
                            </MenuItem>
                        )}
                        {user.role === 'VENDOR' && (
                            <>
                                <MenuItem onClick={() => { navigate('/orders'); handleMenuClose() }}>
                                    Manage Orders
                                </MenuItem>
                                <MenuItem onClick={() => { navigate('/products/create'); handleMenuClose() }}>
                                    {t('products.addProduct', 'Add Product')}
                                </MenuItem>
                            </>
                        )}
                        <MenuItem onClick={handleLogout}>
                            {t('navigation.logout')}
                        </MenuItem>
                    </>
                ) : (
                    <>
                        <MenuItem onClick={() => { navigate('/login'); handleMenuClose() }}>
                            {t('navigation.login')}
                        </MenuItem>
                        <MenuItem onClick={() => { navigate('/register'); handleMenuClose() }}>
                            {t('navigation.register')}
                        </MenuItem>
                    </>
                )}
            </Menu>
        </>
    )
}