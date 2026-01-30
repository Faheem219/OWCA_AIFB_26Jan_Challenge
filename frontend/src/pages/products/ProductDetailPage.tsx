import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Container, Box, Alert, CircularProgress } from '@mui/material'
import { ProductDetailView } from '../../components/products/ProductDetailView'
import { productService } from '../../services/productService'
import { useLanguage } from '../../contexts/LanguageContext'
import { Product } from '../../types'

export const ProductDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const { currentLanguage } = useLanguage()

    const [product, setProduct] = useState<Product | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [isFavorited, setIsFavorited] = useState(false)

    useEffect(() => {
        const fetchProduct = async () => {
            if (!id) {
                setError('Product ID not provided')
                setLoading(false)
                return
            }

            try {
                setLoading(true)
                const productData = await productService.getProduct(id, currentLanguage)

                if (!productData) {
                    setError('Product not found')
                } else {
                    setProduct(productData)
                    // TODO: Check if product is favorited by current user
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load product')
            } finally {
                setLoading(false)
            }
        }

        fetchProduct()
    }, [id, currentLanguage])

    const handleFavoriteToggle = async (_productId: string, isFavorited: boolean) => {
        try {
            // TODO: Implement favorite/unfavorite API call
            setIsFavorited(isFavorited)
        } catch (err) {
            console.error('Failed to toggle favorite:', err)
        }
    }

    const handleShare = (product: Product) => {
        if (navigator.share) {
            navigator.share({
                title: product.name.originalText,
                text: product.description.originalText,
                url: window.location.href
            })
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(window.location.href)
        }
    }

    const handleMakeOffer = (_product: Product, offer: { amount: number; quantity: number; message: string }) => {
        // TODO: Implement make offer functionality
        console.log('Making offer:', offer)
    }

    const handleStartChat = (vendorId: string) => {
        // Navigate to chat with vendor
        navigate(`/chat?vendor=${vendorId}`)
    }

    if (loading) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                    <CircularProgress size={60} />
                </Box>
            </Container>
        )
    }

    if (error) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ py: 4 }}>
                    <Alert severity="error">{error}</Alert>
                </Box>
            </Container>
        )
    }

    if (!product) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ py: 4 }}>
                    <Alert severity="info">Product not found</Alert>
                </Box>
            </Container>
        )
    }

    return (
        <Container maxWidth="lg">
            <Box sx={{ py: 4 }}>
                <ProductDetailView
                    product={product}
                    loading={loading}
                    onFavoriteToggle={handleFavoriteToggle}
                    onShare={handleShare}
                    onMakeOffer={handleMakeOffer}
                    onStartChat={handleStartChat}
                    isFavorited={isFavorited}
                />
            </Box>
        </Container>
    )
}