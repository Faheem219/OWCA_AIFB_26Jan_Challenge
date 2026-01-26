import React from 'react'
import { CircularProgress, Box, Typography } from '@mui/material'

interface LoadingSpinnerProps {
    size?: number
    message?: string
    color?: 'primary' | 'secondary' | 'inherit'
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
    size = 40,
    message,
    color = 'primary'
}) => {
    return (
        <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            gap={2}
            p={2}
        >
            <CircularProgress size={size} color={color} />
            {message && (
                <Typography variant="body2" color="text.secondary" textAlign="center">
                    {message}
                </Typography>
            )}
        </Box>
    )
}