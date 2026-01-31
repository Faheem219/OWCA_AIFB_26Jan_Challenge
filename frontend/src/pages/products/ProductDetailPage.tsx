import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Container, Box, Alert, CircularProgress, Snackbar } from '@mui/material'
import { ProductDetailView } from '../../components/products/ProductDetailView'
import { productService } from '../../services/productService'
import { orderService } from '../../services/orderService'
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
    const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
        open: false,
        message: '',
        severity: 'success'
    })

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

    // Check if product is already favorited on load
    useEffect(() => {
        if (product) {
            const likedProducts = JSON.parse(localStorage.getItem('likedProducts') || '[]')
            setIsFavorited(likedProducts.includes(product.id))
        }
    }, [product])

    const handleFavoriteToggle = async (productId: string, favorited: boolean) => {
        try {
            // Update localStorage for liked products
            const likedProducts = JSON.parse(localStorage.getItem('likedProducts') || '[]')
            if (favorited) {
                if (!likedProducts.includes(productId)) {
                    likedProducts.push(productId)
                }
            } else {
                const index = likedProducts.indexOf(productId)
                if (index > -1) {
                    likedProducts.splice(index, 1)
                }
            }
            localStorage.setItem('likedProducts', JSON.stringify(likedProducts))
            setIsFavorited(favorited)
            setSnackbar({
                open: true,
                message: favorited ? 'Added to saved items' : 'Removed from saved items',
                severity: 'success'
            })
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
            setSnackbar({
                open: true,
                message: 'Link copied to clipboard',
                severity: 'success'
            })
        }
    }

    const handleMakeOffer = async (offerProduct: Product, offer: { amount: number; quantity: number; message: string }) => {
        try {
            // Create actual order with the offer
            await orderService.createOrder({
                product_id: offerProduct.id,
                vendor_id: offerProduct.vendorId,
                quantity: offer.quantity,
                offered_price: offer.amount,
                message: offer.message || '',
            })
            
            setSnackbar({
                open: true,
                message: 'Order placed successfully! The vendor will review your offer.',
                severity: 'success'
            })
            
            // Navigate to buyer orders page after a short delay
            setTimeout(() => {
                navigate('/buyer/orders')
            }, 1500)
        } catch (err) {
            console.error('Failed to place order:', err)
            setSnackbar({
                open: true,
                message: 'Failed to place order. Please try again.',
                severity: 'error'
            })
        }
    }

    const handleStartChat = (vendorId: string) => {
        // Navigate to chat with vendor
        navigate(`/chat?vendor=${vendorId}${product ? `&product=${product.id}` : ''}`)
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
            <Snackbar
                open={snackbar.open}
                autoHideDuration={4000}
                onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert 
                    onClose={() => setSnackbar(prev => ({ ...prev, open: false }))} 
                    severity={snackbar.severity}
                    sx={{ width: '100%' }}
                >
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Container>
    )
}