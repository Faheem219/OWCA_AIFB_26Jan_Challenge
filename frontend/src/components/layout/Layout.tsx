import React from 'react'
import { Outlet } from 'react-router-dom'
import { Box } from '@mui/material'
import { Header } from './Header'
import { Footer } from './Footer'

export const Layout: React.FC = () => {
    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                minHeight: '100vh',
            }}
        >
            <Header />
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                <Outlet />
            </Box>
            <Footer />
        </Box>
    )
}