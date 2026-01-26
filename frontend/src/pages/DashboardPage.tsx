import React from 'react'
import { Container, Typography, Box } from '@mui/material'

export const DashboardPage: React.FC = () => {
    return (
        <Container maxWidth="lg">
            <Box sx={{ py: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Dashboard
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Dashboard functionality will be implemented in later tasks
                </Typography>
            </Box>
        </Container>
    )
}