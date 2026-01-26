import React from 'react'
import { Container, Box } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { ProductUploadForm } from '../../components/products/ProductUploadForm'

export const CreateProductPage: React.FC = () => {
    const navigate = useNavigate()

    const handleSuccess = (productId: string) => {
        // Navigate to the product detail page
        navigate(`/products/${productId}`)
    }

    const handleCancel = () => {
        // Navigate back to dashboard
        navigate('/dashboard')
    }

    return (
        <Container maxWidth="lg">
            <Box sx={{ py: 4 }}>
                <ProductUploadForm
                    onSuccess={handleSuccess}
                    onCancel={handleCancel}
                />
            </Box>
        </Container>
    )
}