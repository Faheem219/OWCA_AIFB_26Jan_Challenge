import React from 'react'
import { Box, Container, Typography, Link, Grid, Divider } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'

export const Footer: React.FC = () => {
    return (
        <Box
            component="footer"
            sx={{
                bgcolor: 'background.paper',
                borderTop: 1,
                borderColor: 'divider',
                mt: 'auto',
                py: 4,
            }}
        >
            <Container maxWidth="lg">
                <Grid container spacing={4}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="h6" color="text.primary" gutterBottom>
                            Mandi Market
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            AI-powered multilingual marketplace connecting vendors and buyers
                            across Indian local markets.
                        </Typography>
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="h6" color="text.primary" gutterBottom>
                            For Vendors
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <Link component={RouterLink} to="/products/create" color="text.secondary">
                                List Products
                            </Link>
                            <Link component={RouterLink} to="/dashboard" color="text.secondary">
                                Vendor Dashboard
                            </Link>
                            <Link href="#" color="text.secondary">
                                Pricing Guide
                            </Link>
                            <Link href="#" color="text.secondary">
                                Seller Support
                            </Link>
                        </Box>
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="h6" color="text.primary" gutterBottom>
                            For Buyers
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <Link component={RouterLink} to="/products" color="text.secondary">
                                Browse Products
                            </Link>
                            <Link href="#" color="text.secondary">
                                How to Buy
                            </Link>
                            <Link href="#" color="text.secondary">
                                Payment Methods
                            </Link>
                            <Link href="#" color="text.secondary">
                                Buyer Protection
                            </Link>
                        </Box>
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="h6" color="text.primary" gutterBottom>
                            Support
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <Link href="#" color="text.secondary">
                                Help Center
                            </Link>
                            <Link href="#" color="text.secondary">
                                Contact Us
                            </Link>
                            <Link href="#" color="text.secondary">
                                Language Support
                            </Link>
                            <Link href="#" color="text.secondary">
                                Community Forum
                            </Link>
                        </Box>
                    </Grid>
                </Grid>

                <Divider sx={{ my: 3 }} />

                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="text.secondary">
                            © 2024 Multilingual Mandi Marketplace. All rights reserved.
                        </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Box
                            sx={{
                                display: 'flex',
                                gap: 2,
                                justifyContent: { xs: 'flex-start', md: 'flex-end' },
                                flexWrap: 'wrap',
                            }}
                        >
                            <Link href="#" color="text.secondary" variant="body2">
                                Privacy Policy
                            </Link>
                            <Link href="#" color="text.secondary" variant="body2">
                                Terms of Service
                            </Link>
                            <Link href="#" color="text.secondary" variant="body2">
                                Cookie Policy
                            </Link>
                            <Link href="#" color="text.secondary" variant="body2">
                                Accessibility
                            </Link>
                        </Box>
                    </Grid>
                </Grid>

                <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary" align="center">
                        Supporting 10+ Indian languages • Secure payments • AI-powered translations
                    </Typography>
                </Box>
            </Container>
        </Box>
    )
}