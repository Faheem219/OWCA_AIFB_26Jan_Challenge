import React from 'react'
import {
    Grid,
    Card,
    CardMedia,
    CardContent,
    CardActions,
    Typography,
    Button,
    Chip,
    Box,
    IconButton,
    Rating,
    Skeleton,
    Tooltip
} from '@mui/material'
import {
    LocationOn as LocationIcon,
    Favorite as FavoriteIcon,
    FavoriteBorder as FavoriteBorderIcon,
    Share as ShareIcon,
    Visibility as ViewIcon,
    LocalOffer as OfferIcon,
    Verified as VerifiedIcon
} from '@mui/icons-material'
import { useTranslation } from '../../hooks/useTranslation'
import { useLanguage } from '../../contexts/LanguageContext'
import { Product, MultilingualText } from '../../types'

interface ProductGridProps {
    products: Product[]
    loading?: boolean
    onProductClick?: (product: Product) => void
    onFavoriteToggle?: (productId: string, isFavorited: boolean) => void
    onShare?: (product: Product) => void
    onMakeOffer?: (product: Product) => void
    favoriteProductIds?: Set<string>
    showVendorInfo?: boolean
    columns?: { xs?: number; sm?: number; md?: number; lg?: number; xl?: number }
}

interface ProductCardProps {
    product: Product
    onProductClick?: (product: Product) => void
    onFavoriteToggle?: (productId: string, isFavorited: boolean) => void
    onShare?: (product: Product) => void
    onMakeOffer?: (product: Product) => void
    isFavorited?: boolean
    showVendorInfo?: boolean
}

const ProductCard: React.FC<ProductCardProps> = ({
    product,
    onProductClick,
    onFavoriteToggle,
    onShare,
    onMakeOffer,
    isFavorited = false,
    showVendorInfo = true
}) => {
    const t = useTranslation()
    const { currentLanguage } = useLanguage()

    const getTranslatedText = (multilingualText: MultilingualText): string => {
        return multilingualText.translations[currentLanguage] || multilingualText.originalText
    }

    const formatPrice = (price: number): string => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(price)
    }

    const formatDistance = (coordinates: [number, number]): string => {
        // TODO: Calculate actual distance based on user location
        return '2.5 km'
    }

    const primaryImage = product.images.find(img => img.isPrimary) || product.images[0]
    const isOutOfStock = product.quantityAvailable <= 0

    return (
        <Card
            sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',
                cursor: onProductClick ? 'pointer' : 'default',
                transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                '&:hover': onProductClick ? {
                    transform: 'translateY(-4px)',
                    boxShadow: 4
                } : {}
            }}
            onClick={() => onProductClick && onProductClick(product)}
        >
            {/* Image */}
            <Box sx={{ position: 'relative' }}>
                <CardMedia
                    component="img"
                    height="200"
                    image={primaryImage?.url || '/placeholder-product.jpg'}
                    alt={getTranslatedText(product.name)}
                    sx={{
                        objectFit: 'cover',
                        filter: isOutOfStock ? 'grayscale(50%)' : 'none'
                    }}
                />

                {/* Overlay badges */}
                <Box
                    sx={{
                        position: 'absolute',
                        top: 8,
                        left: 8,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 0.5
                    }}
                >
                    {product.qualityGrade === 'organic' && (
                        <Chip
                            label="Organic"
                            size="small"
                            color="success"
                            icon={<VerifiedIcon />}
                        />
                    )}
                    {product.qualityGrade === 'premium' && (
                        <Chip
                            label="Premium"
                            size="small"
                            color="primary"
                        />
                    )}
                    {isOutOfStock && (
                        <Chip
                            label="Out of Stock"
                            size="small"
                            color="error"
                        />
                    )}
                </Box>

                {/* Action buttons */}
                <Box
                    sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 0.5
                    }}
                >
                    <IconButton
                        size="small"
                        onClick={(e) => {
                            e.stopPropagation()
                            onFavoriteToggle && onFavoriteToggle(product.id, !isFavorited)
                        }}
                        sx={{
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            '&:hover': { backgroundColor: 'rgba(255, 255, 255, 1)' }
                        }}
                    >
                        {isFavorited ? (
                            <FavoriteIcon color="error" />
                        ) : (
                            <FavoriteBorderIcon />
                        )}
                    </IconButton>

                    <IconButton
                        size="small"
                        onClick={(e) => {
                            e.stopPropagation()
                            onShare && onShare(product)
                        }}
                        sx={{
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            '&:hover': { backgroundColor: 'rgba(255, 255, 255, 1)' }
                        }}
                    >
                        <ShareIcon />
                    </IconButton>
                </Box>
            </Box>

            <CardContent sx={{ flexGrow: 1, pb: 1 }}>
                {/* Product name */}
                <Typography
                    variant="h6"
                    component="h3"
                    gutterBottom
                    sx={{
                        fontSize: '1.1rem',
                        fontWeight: 600,
                        lineHeight: 1.3,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden'
                    }}
                >
                    {getTranslatedText(product.name)}
                </Typography>

                {/* Description */}
                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                        mb: 2,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden'
                    }}
                >
                    {getTranslatedText(product.description)}
                </Typography>

                {/* Price */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Typography
                        variant="h6"
                        color="primary"
                        sx={{ fontWeight: 700 }}
                    >
                        {formatPrice(product.basePrice)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        per {product.unit}
                    </Typography>
                    {/* TODO: Add negotiable indicator */}
                </Box>

                {/* Location and availability */}
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <LocationIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
                        {product.location.city}, {product.location.state}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                        {formatDistance(product.location.coordinates)}
                    </Typography>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {product.quantityAvailable} {product.unit} available
                </Typography>

                {/* Tags */}
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 2 }}>
                    {product.tags.slice(0, 3).map((tag, index) => (
                        <Chip
                            key={index}
                            label={tag}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.75rem' }}
                        />
                    ))}
                    {product.tags.length > 3 && (
                        <Chip
                            label={`+${product.tags.length - 3}`}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.75rem' }}
                        />
                    )}
                </Box>

                {/* Vendor info */}
                {showVendorInfo && (
                    <Box sx={{ pt: 2, borderTop: 1, borderColor: 'divider' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Typography variant="body2" color="text.secondary">
                                Vendor: {/* TODO: Add vendor name */}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <Rating
                                    value={4.5} // TODO: Add actual vendor rating
                                    precision={0.1}
                                    size="small"
                                    readOnly
                                />
                                <Typography variant="caption" color="text.secondary">
                                    (4.5)
                                </Typography>
                            </Box>
                        </Box>
                    </Box>
                )}
            </CardContent>

            <CardActions sx={{ pt: 0, px: 2, pb: 2 }}>
                <Button
                    fullWidth
                    variant="contained"
                    disabled={isOutOfStock}
                    onClick={(e) => {
                        e.stopPropagation()
                        onProductClick && onProductClick(product)
                    }}
                >
                    {isOutOfStock ? 'Out of Stock' : 'View Details'}
                </Button>

                {!isOutOfStock && onMakeOffer && (
                    <Button
                        variant="outlined"
                        startIcon={<OfferIcon />}
                        onClick={(e) => {
                            e.stopPropagation()
                            onMakeOffer(product)
                        }}
                        sx={{ ml: 1 }}
                    >
                        Offer
                    </Button>
                )}
            </CardActions>
        </Card>
    )
}

const ProductCardSkeleton: React.FC = () => (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Skeleton variant="rectangular" height={200} />
        <CardContent sx={{ flexGrow: 1 }}>
            <Skeleton variant="text" height={32} />
            <Skeleton variant="text" height={20} />
            <Skeleton variant="text" height={20} />
            <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                <Skeleton variant="rectangular" width={60} height={24} />
                <Skeleton variant="rectangular" width={60} height={24} />
            </Box>
        </CardContent>
        <CardActions sx={{ px: 2, pb: 2 }}>
            <Skeleton variant="rectangular" width="100%" height={36} />
        </CardActions>
    </Card>
)

export const ProductGrid: React.FC<ProductGridProps> = ({
    products,
    loading = false,
    onProductClick,
    onFavoriteToggle,
    onShare,
    onMakeOffer,
    favoriteProductIds = new Set(),
    showVendorInfo = true,
    columns = { xs: 1, sm: 2, md: 3, lg: 4, xl: 5 }
}) => {
    if (loading) {
        return (
            <Grid container spacing={3}>
                {Array.from({ length: 12 }).map((_, index) => (
                    <Grid item key={index} {...columns}>
                        <ProductCardSkeleton />
                    </Grid>
                ))}
            </Grid>
        )
    }

    if (products.length === 0) {
        return (
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    py: 8,
                    textAlign: 'center'
                }}
            >
                <Typography variant="h6" gutterBottom>
                    No products found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Try adjusting your search criteria or browse different categories
                </Typography>
            </Box>
        )
    }

    return (
        <Grid container spacing={3}>
            {products.map((product) => (
                <Grid item key={product.id} {...columns}>
                    <ProductCard
                        product={product}
                        onProductClick={onProductClick}
                        onFavoriteToggle={onFavoriteToggle}
                        onShare={onShare}
                        onMakeOffer={onMakeOffer}
                        isFavorited={favoriteProductIds.has(product.id)}
                        showVendorInfo={showVendorInfo}
                    />
                </Grid>
            ))}
        </Grid>
    )
}