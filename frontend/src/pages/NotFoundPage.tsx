import React from 'react'
import { Box, Container, Typography, Button } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'
import { Home, ArrowBack } from '@mui/icons-material'

export const NotFoundPage: React.FC = () => {
    return (
        <Container maxWidth="md">
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '60vh',
                    textAlign: 'center',
                    py: 8,
                }}
            >
                <Typography
                    variant="h1"
                    sx={{
                        fontSize: '6rem',
                        fontWeight: 'bold',
                        color: 'primary.main',
                        mb: 2,
                    }}
                >
                    404
                </Typography>

                <Typography variant="h4" gutterBottom>
                    Page Not Found
                </Typography>

                <Typography variant="body1" color="text.secondary" paragraph>
                    The page you're looking for doesn't exist or has been moved.
                </Typography>

                <Box sx={{ display: 'flex', gap: 2, mt: 4 }}>
                    <Button
                        variant="contained"
                        startIcon={<Home />}
                        component={RouterLink}
                        to="/"
                        size="large"
                    >
                        Go Home
                    </Button>

                    <Button
                        variant="outlined"
                        startIcon={<ArrowBack />}
                        onClick={() => window.history.back()}
                        size="large"
                    >
                        Go Back
                    </Button>
                </Box>
            </Box>
        </Container>
    )
}