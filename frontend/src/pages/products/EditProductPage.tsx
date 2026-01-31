import React, { useState, useEffect } from 'react'
import { Container, Box, Typography, Alert, Button } from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowBack } from '@mui/icons-material'
import { ProductUploadForm } from '../../components/products/ProductUploadForm'
import { productService } from '../../services/productService'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { Product } from '../../types'

export const EditProductPage: React.FC = () => {
    const navigate = useNavigate()
    const { id } = useParams<{ id: string }>()
    const [product, setProduct] = useState<Product | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (id) {
            loadProduct(id)
        }
    }, [id])

    const loadProduct = async (productId: string) => {
        setLoading(true)
        setError(null)
        try {
            const productData = await productService.getProduct(productId)
            setProduct(productData)
        } catch (err) {
            console.error('Failed to load product:', err)
            setError('Failed to load product. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    const handleSuccess = (productId: string) => {
        // Navigate to the product detail page after successful update
        navigate(`/products/${productId}`)
    }

    const handleCancel = () => {
        // Navigate back to dashboard
        navigate('/dashboard/vendor')
    }

    if (loading) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ py: 4, display: 'flex', justifyContent: 'center' }}>
                    <LoadingSpinner message="Loading product..." />
                </Box>
            </Container>
        )
    }

    if (error || !product) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ py: 4 }}>
                    <Button
                        startIcon={<ArrowBack />}
                        onClick={() => navigate('/dashboard/vendor')}
                        sx={{ mb: 2 }}
                    >
                        Back to Dashboard
                    </Button>
                    <Alert severity="error">
                        {error || 'Product not found'}
                    </Alert>
                </Box>
            </Container>
        )
    }

    return (
        <Container maxWidth="lg">
            <Box sx={{ py: 4 }}>
                <Button
                    startIcon={<ArrowBack />}
                    onClick={() => navigate('/dashboard/vendor')}
                    sx={{ mb: 2 }}
                >
                    Back to Dashboard
                </Button>
                
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                    Edit Product
                </Typography>
                
                <ProductUploadForm
                    editMode={true}
                    existingProduct={product}
                    onSuccess={handleSuccess}
                    onCancel={handleCancel}
                />
            </Box>
        </Container>
    )
}
