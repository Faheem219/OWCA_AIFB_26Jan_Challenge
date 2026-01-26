import React from 'react'
import {
    Box,
    Container,
    Typography,
    Button,
    Grid,
    Card,
    CardContent,
    Chip,
    useTheme,
} from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'
import {
    Translate,
    TrendingUp,
    Security,
    Language,
    LocalShipping,
    Support,
} from '@mui/icons-material'

export const HomePage: React.FC = () => {
    const theme = useTheme()

    const features = [
        {
            icon: <Translate />,
            title: 'Multilingual Support',
            description: 'Communicate in 10+ Indian languages with real-time AI translation',
        },
        {
            icon: <TrendingUp />,
            title: 'AI Price Discovery',
            description: 'Get fair market prices powered by real-time data and ML algorithms',
        },
        {
            icon: <Security />,
            title: 'Secure Payments',
            description: 'Multiple payment options with fraud detection and buyer protection',
        },
        {
            icon: <Language />,
            title: 'Cultural Sensitivity',
            description: 'Context-aware translations that respect regional expressions',
        },
        {
            icon: <LocalShipping />,
            title: 'Local Markets',
            description: 'Connect with vendors in your area and nearby mandis',
        },
        {
            icon: <Support />,
            title: '24/7 Support',
            description: 'Get help in your preferred language whenever you need it',
        },
    ]

    const stats = [
        { label: 'Languages Supported', value: '10+' },
        { label: 'Active Vendors', value: '1000+' },
        { label: 'Products Listed', value: '5000+' },
        { label: 'Successful Transactions', value: '10000+' },
    ]

    return (
        <Box>
            {/* Hero Section */}
            <Box
                sx={{
                    background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                    color: 'white',
                    py: 8,
                }}
            >
                <Container maxWidth="lg">
                    <Grid container spacing={4} alignItems="center">
                        <Grid item xs={12} md={6}>
                            <Typography variant="h2" component="h1" gutterBottom>
                                Bridge Language Barriers in Indian Markets
                            </Typography>
                            <Typography variant="h5" paragraph sx={{ opacity: 0.9 }}>
                                AI-powered multilingual marketplace connecting vendors and buyers
                                across India with real-time translation and fair pricing.
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 4 }}>
                                <Button
                                    variant="contained"
                                    size="large"
                                    color="secondary"
                                    component={RouterLink}
                                    to="/register"
                                    sx={{ px: 4, py: 1.5 }}
                                >
                                    Get Started
                                </Button>
                                <Button
                                    variant="outlined"
                                    size="large"
                                    sx={{
                                        px: 4,
                                        py: 1.5,
                                        borderColor: 'white',
                                        color: 'white',
                                        '&:hover': {
                                            borderColor: 'white',
                                            backgroundColor: 'rgba(255,255,255,0.1)',
                                        }
                                    }}
                                    component={RouterLink}
                                    to="/products"
                                >
                                    Browse Products
                                </Button>
                            </Box>
                            <Box sx={{ display: 'flex', gap: 1, mt: 3, flexWrap: 'wrap' }}>
                                {['Hindi', 'Tamil', 'Telugu', 'Bengali', 'Gujarati'].map((lang) => (
                                    <Chip
                                        key={lang}
                                        label={lang}
                                        size="small"
                                        sx={{
                                            backgroundColor: 'rgba(255,255,255,0.2)',
                                            color: 'white',
                                        }}
                                    />
                                ))}
                                <Chip
                                    label="+5 more"
                                    size="small"
                                    sx={{
                                        backgroundColor: 'rgba(255,255,255,0.2)',
                                        color: 'white',
                                    }}
                                />
                            </Box>
                        </Grid>
                        <Grid item xs={12} md={6}>
                            <Box
                                sx={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    height: 400,
                                    backgroundColor: 'rgba(255,255,255,0.1)',
                                    borderRadius: 2,
                                }}
                            >
                                <Typography variant="h4" sx={{ opacity: 0.7 }}>
                                    Hero Image Placeholder
                                </Typography>
                            </Box>
                        </Grid>
                    </Grid>
                </Container>
            </Box>

            {/* Stats Section */}
            <Box sx={{ py: 6, backgroundColor: 'background.paper' }}>
                <Container maxWidth="lg">
                    <Grid container spacing={4}>
                        {stats.map((stat, index) => (
                            <Grid item xs={6} md={3} key={index}>
                                <Box sx={{ textAlign: 'center' }}>
                                    <Typography variant="h3" color="primary" fontWeight="bold">
                                        {stat.value}
                                    </Typography>
                                    <Typography variant="body1" color="text.secondary">
                                        {stat.label}
                                    </Typography>
                                </Box>
                            </Grid>
                        ))}
                    </Grid>
                </Container>
            </Box>

            {/* Features Section */}
            <Box sx={{ py: 8 }}>
                <Container maxWidth="lg">
                    <Typography variant="h3" align="center" gutterBottom>
                        Why Choose Mandi Market?
                    </Typography>
                    <Typography variant="h6" align="center" color="text.secondary" paragraph>
                        Empowering Indian agriculture through technology and unity in diversity
                    </Typography>

                    <Grid container spacing={4} sx={{ mt: 4 }}>
                        {features.map((feature, index) => (
                            <Grid item xs={12} md={4} key={index}>
                                <Card
                                    sx={{
                                        height: '100%',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        transition: 'transform 0.2s',
                                        '&:hover': {
                                            transform: 'translateY(-4px)',
                                        },
                                    }}
                                >
                                    <CardContent sx={{ flexGrow: 1 }}>
                                        <Box
                                            sx={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                mb: 2,
                                                color: 'primary.main',
                                            }}
                                        >
                                            {feature.icon}
                                            <Typography variant="h6" sx={{ ml: 1 }}>
                                                {feature.title}
                                            </Typography>
                                        </Box>
                                        <Typography variant="body2" color="text.secondary">
                                            {feature.description}
                                        </Typography>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                </Container>
            </Box>

            {/* CTA Section */}
            <Box
                sx={{
                    py: 8,
                    backgroundColor: 'primary.main',
                    color: 'white',
                }}
            >
                <Container maxWidth="md">
                    <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h3" gutterBottom>
                            Ready to Start Trading?
                        </Typography>
                        <Typography variant="h6" paragraph sx={{ opacity: 0.9 }}>
                            Join thousands of vendors and buyers already using our platform
                            to break language barriers and grow their business.
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 4 }}>
                            <Button
                                variant="contained"
                                size="large"
                                color="secondary"
                                component={RouterLink}
                                to="/register?role=vendor"
                                sx={{ px: 4, py: 1.5 }}
                            >
                                Become a Vendor
                            </Button>
                            <Button
                                variant="outlined"
                                size="large"
                                component={RouterLink}
                                to="/register?role=buyer"
                                sx={{
                                    px: 4,
                                    py: 1.5,
                                    borderColor: 'white',
                                    color: 'white',
                                    '&:hover': {
                                        borderColor: 'white',
                                        backgroundColor: 'rgba(255,255,255,0.1)',
                                    },
                                }}
                            >
                                Start Buying
                            </Button>
                        </Box>
                    </Box>
                </Container>
            </Box>
        </Box>
    )
}