import React, { useState } from 'react'
import {
    Box,
    Grid,
    Typography,
    Button,
    Chip,
    Card,
    CardContent,
    IconButton,
    Dialog,
    DialogContent,
    DialogActions,
    TextField,
    Rating,
    Avatar,
    List,
    ListItem,
    ListItemText,
    Skeleton,
    Alert,
    Tabs,
    Tab
} from '@mui/material'
import {
    LocationOn as LocationIcon,
    Favorite as FavoriteIcon,
    FavoriteBorder as FavoriteBorderIcon,
    Share as ShareIcon,
    LocalOffer as OfferIcon,
    Chat as ChatIcon,
    Verified as VerifiedIcon,
    CalendarToday as CalendarIcon,
    Scale as ScaleIcon,
    Security as SecurityIcon,
    Close as CloseIcon,
    ZoomIn as ZoomIcon,
    NavigateBefore as PrevIcon,
    NavigateNext as NextIcon
} from '@mui/icons-material'
import { useLanguage } from '../../contexts/LanguageContext'
import { useAuth } from '../../hooks/useAuth'
import { Product, MultilingualText } from '../../types'

interface ProductDetailViewProps {
    product: Product
    loading?: boolean
    onFavoriteToggle?: (productId: string, isFavorited: boolean) => void
    onShare?: (product: Product) => void
    onMakeOffer?: (product: Product, offer: { amount: number; quantity: number; message: string }) => void
    onStartChat?: (vendorId: string) => void
    isFavorited?: boolean
}

interface ImageGalleryProps {
    images: Array<{ id: string; url: string; thumbnailUrl: string; alt: string; isPrimary: boolean }>
    productName: string
}

interface OfferDialogProps {
    open: boolean
    onClose: () => void
    onSubmit: (offer: { amount: number; quantity: number; message: string }) => void
    product: Product
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ images, productName }) => {
    const [selectedImage, setSelectedImage] = useState(0)
    const [zoomOpen, setZoomOpen] = useState(false)

    const primaryImage = images.find(img => img.isPrimary) || images[0]
    const currentImage = images[selectedImage] || primaryImage

    return (
        <Box>
            {/* Main image */}
            <Card sx={{ mb: 2, position: 'relative' }}>
                <Box
                    component="img"
                    src={currentImage?.url || '/placeholder-product.jpg'}
                    alt={currentImage?.alt || productName}
                    sx={{
                        width: '100%',
                        height: 400,
                        objectFit: 'cover',
                        cursor: 'zoom-in'
                    }}
                    onClick={() => setZoomOpen(true)}
                />

                {/* Navigation arrows */}
                {images.length > 1 && (
                    <>
                        <IconButton
                            sx={{
                                position: 'absolute',
                                left: 8,
                                top: '50%',
                                transform: 'translateY(-50%)',
                                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                                '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.9)' }
                            }}
                            onClick={() => setSelectedImage(prev =>
                                prev === 0 ? images.length - 1 : prev - 1
                            )}
                        >
                            <PrevIcon />
                        </IconButton>

                        <IconButton
                            sx={{
                                position: 'absolute',
                                right: 8,
                                top: '50%',
                                transform: 'translateY(-50%)',
                                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                                '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.9)' }
                            }}
                            onClick={() => setSelectedImage(prev =>
                                prev === images.length - 1 ? 0 : prev + 1
                            )}
                        >
                            <NextIcon />
                        </IconButton>
                    </>
                )}

                {/* Zoom button */}
                <IconButton
                    sx={{
                        position: 'absolute',
                        bottom: 8,
                        right: 8,
                        backgroundColor: 'rgba(255, 255, 255, 0.8)',
                        '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.9)' }
                    }}
                    onClick={() => setZoomOpen(true)}
                >
                    <ZoomIcon />
                </IconButton>
            </Card>

            {/* Thumbnail strip */}
            {images.length > 1 && (
                <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', pb: 1 }}>
                    {images.map((image, index) => (
                        <Box
                            key={image.id}
                            component="img"
                            src={image.thumbnailUrl}
                            alt={image.alt}
                            sx={{
                                width: 80,
                                height: 80,
                                objectFit: 'cover',
                                borderRadius: 1,
                                cursor: 'pointer',
                                border: selectedImage === index ? 2 : 1,
                                borderColor: selectedImage === index ? 'primary.main' : 'grey.300',
                                flexShrink: 0
                            }}
                            onClick={() => setSelectedImage(index)}
                        />
                    ))}
                </Box>
            )}

            {/* Zoom dialog */}
            <Dialog
                open={zoomOpen}
                onClose={() => setZoomOpen(false)}
                maxWidth="lg"
                fullWidth
            >
                <DialogContent sx={{ p: 0, position: 'relative' }}>
                    <IconButton
                        sx={{
                            position: 'absolute',
                            top: 8,
                            right: 8,
                            zIndex: 1,
                            backgroundColor: 'rgba(255, 255, 255, 0.8)'
                        }}
                        onClick={() => setZoomOpen(false)}
                    >
                        <CloseIcon />
                    </IconButton>
                    <Box
                        component="img"
                        src={currentImage?.url}
                        alt={currentImage?.alt}
                        sx={{
                            width: '100%',
                            height: 'auto',
                            maxHeight: '80vh',
                            objectFit: 'contain'
                        }}
                    />
                </DialogContent>
            </Dialog>
        </Box>
    )
}

const OfferDialog: React.FC<OfferDialogProps> = ({ open, onClose, onSubmit, product }) => {
    const [offer, setOffer] = useState({
        amount: product.basePrice,
        quantity: 1,
        message: ''
    })
    const [errors, setErrors] = useState<Record<string, string>>({})

    const validateOffer = () => {
        const newErrors: Record<string, string> = {}

        if (offer.amount <= 0) {
            newErrors.amount = 'Amount must be greater than 0'
        }

        if (offer.quantity <= 0) {
            newErrors.quantity = 'Quantity must be greater than 0'
        }

        if (offer.quantity > product.quantityAvailable) {
            newErrors.quantity = `Only ${product.quantityAvailable} ${product.unit} available`
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = () => {
        if (validateOffer()) {
            onSubmit(offer)
            onClose()
        }
    }

    const totalAmount = offer.amount * offer.quantity

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogContent>
                <Typography variant="h6" gutterBottom>
                    Make an Offer
                </Typography>

                <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                        Current price: ₹{product.basePrice} per {product.unit}
                    </Typography>
                </Box>

                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Your Offer Price"
                            type="number"
                            value={offer.amount}
                            onChange={(e) => setOffer(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                            error={!!errors.amount}
                            helperText={errors.amount}
                            InputProps={{
                                startAdornment: '₹'
                            }}
                        />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Quantity"
                            type="number"
                            value={offer.quantity}
                            onChange={(e) => setOffer(prev => ({ ...prev, quantity: parseInt(e.target.value) || 0 }))}
                            error={!!errors.quantity}
                            helperText={errors.quantity || `Available: ${product.quantityAvailable} ${product.unit}`}
                            InputProps={{
                                endAdornment: product.unit
                            }}
                        />
                    </Grid>

                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="Message (Optional)"
                            multiline
                            rows={3}
                            value={offer.message}
                            onChange={(e) => setOffer(prev => ({ ...prev, message: e.target.value }))}
                            placeholder="Add a message to the vendor..."
                        />
                    </Grid>
                </Grid>

                <Box sx={{ mt: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="h6">
                        Total: ₹{totalAmount.toFixed(2)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        {offer.quantity} {product.unit} × ₹{offer.amount} each
                    </Typography>
                </Box>
            </DialogContent>

            <DialogActions>
                <Button onClick={onClose}>Cancel</Button>
                <Button variant="contained" onClick={handleSubmit}>
                    Send Offer
                </Button>
            </DialogActions>
        </Dialog>
    )
}

export const ProductDetailView: React.FC<ProductDetailViewProps> = ({
    product,
    loading = false,
    onFavoriteToggle,
    onShare,
    onMakeOffer,
    onStartChat,
    isFavorited = false
}) => {
    const { currentLanguage } = useLanguage()
    const { user } = useAuth()
    const [offerDialogOpen, setOfferDialogOpen] = useState(false)
    const [tabValue, setTabValue] = useState(0)

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

    const formatDate = (dateString: string): string => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        })
    }

    const isOutOfStock = product.quantityAvailable <= 0
    const isOwnProduct = user?.id === product.vendorId

    if (loading) {
        return (
            <Grid container spacing={4}>
                <Grid item xs={12} md={6}>
                    <Skeleton variant="rectangular" height={400} />
                </Grid>
                <Grid item xs={12} md={6}>
                    <Skeleton variant="text" height={40} />
                    <Skeleton variant="text" height={60} />
                    <Skeleton variant="text" height={30} />
                    <Box sx={{ mt: 2 }}>
                        <Skeleton variant="rectangular" height={50} />
                    </Box>
                </Grid>
            </Grid>
        )
    }

    return (
        <Box>
            <Grid container spacing={4}>
                {/* Image Gallery */}
                <Grid item xs={12} md={6}>
                    <ImageGallery
                        images={product.images}
                        productName={getTranslatedText(product.name)}
                    />
                </Grid>

                {/* Product Info */}
                <Grid item xs={12} md={6}>
                    <Box sx={{ position: 'sticky', top: 20 }}>
                        {/* Header */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                            <Typography variant="h4" component="h1" sx={{ flexGrow: 1, mr: 2 }}>
                                {getTranslatedText(product.name)}
                            </Typography>

                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <IconButton
                                    onClick={() => onFavoriteToggle && onFavoriteToggle(product.id, !isFavorited)}
                                    color={isFavorited ? 'error' : 'default'}
                                >
                                    {isFavorited ? <FavoriteIcon /> : <FavoriteBorderIcon />}
                                </IconButton>

                                <IconButton onClick={() => onShare && onShare(product)}>
                                    <ShareIcon />
                                </IconButton>
                            </Box>
                        </Box>

                        {/* Badges */}
                        <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
                            {product.qualityGrade === 'organic' && (
                                <Chip
                                    label="Organic"
                                    color="success"
                                    icon={<VerifiedIcon />}
                                />
                            )}
                            {product.qualityGrade === 'premium' && (
                                <Chip label="Premium" color="primary" />
                            )}
                            {isOutOfStock && (
                                <Chip label="Out of Stock" color="error" />
                            )}
                            <Chip label={product.category} variant="outlined" />
                        </Box>

                        {/* Price */}
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="h3" color="primary" sx={{ fontWeight: 700 }}>
                                {formatPrice(product.basePrice)}
                            </Typography>
                            <Typography variant="h6" color="text.secondary">
                                per {product.unit}
                            </Typography>
                            {/* TODO: Add negotiable indicator */}
                        </Box>

                        {/* Description */}
                        <Typography variant="body1" sx={{ mb: 3, lineHeight: 1.6 }}>
                            {getTranslatedText(product.description)}
                        </Typography>

                        {/* Key Details */}
                        <Card sx={{ mb: 3 }}>
                            <CardContent>
                                <Grid container spacing={2}>
                                    <Grid item xs={6}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <ScaleIcon color="action" />
                                            <Box>
                                                <Typography variant="body2" color="text.secondary">
                                                    Available
                                                </Typography>
                                                <Typography variant="body1" fontWeight={600}>
                                                    {product.quantityAvailable} {product.unit}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </Grid>

                                    <Grid item xs={6}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <LocationIcon color="action" />
                                            <Box>
                                                <Typography variant="body2" color="text.secondary">
                                                    Location
                                                </Typography>
                                                <Typography variant="body1" fontWeight={600}>
                                                    {product.location.city}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </Grid>

                                    {product.harvestDate && (
                                        <Grid item xs={6}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <CalendarIcon color="action" />
                                                <Box>
                                                    <Typography variant="body2" color="text.secondary">
                                                        Harvested
                                                    </Typography>
                                                    <Typography variant="body1" fontWeight={600}>
                                                        {formatDate(product.harvestDate)}
                                                    </Typography>
                                                </Box>
                                            </Box>
                                        </Grid>
                                    )}

                                    <Grid item xs={6}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <SecurityIcon color="action" />
                                            <Box>
                                                <Typography variant="body2" color="text.secondary">
                                                    Quality
                                                </Typography>
                                                <Typography variant="body1" fontWeight={600}>
                                                    {product.qualityGrade}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>

                        {/* Action Buttons */}
                        {!isOwnProduct && (
                            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                                <Button
                                    variant="contained"
                                    size="large"
                                    fullWidth
                                    disabled={isOutOfStock}
                                    startIcon={<OfferIcon />}
                                    onClick={() => setOfferDialogOpen(true)}
                                >
                                    Make Offer
                                </Button>

                                <Button
                                    variant="outlined"
                                    size="large"
                                    startIcon={<ChatIcon />}
                                    onClick={() => onStartChat && onStartChat(product.vendorId)}
                                >
                                    Chat
                                </Button>
                            </Box>
                        )}

                        {/* Tags */}
                        {product.tags.length > 0 && (
                            <Box sx={{ mb: 3 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                    Tags
                                </Typography>
                                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                    {product.tags.map((tag, index) => (
                                        <Chip
                                            key={index}
                                            label={tag}
                                            size="small"
                                            variant="outlined"
                                        />
                                    ))}
                                </Box>
                            </Box>
                        )}
                    </Box>
                </Grid>
            </Grid>

            {/* Additional Details Tabs */}
            <Box sx={{ mt: 6 }}>
                <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
                    <Tab label="Details" />
                    <Tab label="Vendor Info" />
                    <Tab label="Reviews" />
                </Tabs>

                {/* Details Tab */}
                {tabValue === 0 && (
                    <Box sx={{ mt: 3 }}>
                        <Grid container spacing={3}>
                            <Grid item xs={12} md={6}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Product Specifications
                                        </Typography>
                                        <List>
                                            <ListItem>
                                                <ListItemText
                                                    primary="Category"
                                                    secondary={product.category}
                                                />
                                            </ListItem>
                                            {product.subcategory && (
                                                <ListItem>
                                                    <ListItemText
                                                        primary="Subcategory"
                                                        secondary={product.subcategory}
                                                    />
                                                </ListItem>
                                            )}
                                            <ListItem>
                                                <ListItemText
                                                    primary="Quality Grade"
                                                    secondary={product.qualityGrade}
                                                />
                                            </ListItem>
                                            <ListItem>
                                                <ListItemText
                                                    primary="Unit"
                                                    secondary={product.unit}
                                                />
                                            </ListItem>
                                        </List>
                                    </CardContent>
                                </Card>
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Location Details
                                        </Typography>
                                        <List>
                                            <ListItem>
                                                <ListItemText
                                                    primary="City"
                                                    secondary={product.location.city}
                                                />
                                            </ListItem>
                                            <ListItem>
                                                <ListItemText
                                                    primary="State"
                                                    secondary={product.location.state}
                                                />
                                            </ListItem>
                                            {product.location.pincode && (
                                                <ListItem>
                                                    <ListItemText
                                                        primary="Pincode"
                                                        secondary={product.location.pincode}
                                                    />
                                                </ListItem>
                                            )}
                                        </List>
                                    </CardContent>
                                </Card>
                            </Grid>
                        </Grid>
                    </Box>
                )}

                {/* Vendor Info Tab */}
                {tabValue === 1 && (
                    <Box sx={{ mt: 3 }}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Vendor Information
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                                    <Avatar sx={{ width: 60, height: 60 }}>
                                        V
                                    </Avatar>
                                    <Box>
                                        <Typography variant="h6">
                                            Vendor Name {/* TODO: Add actual vendor name */}
                                        </Typography>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Rating value={4.5} precision={0.1} size="small" readOnly />
                                            <Typography variant="body2" color="text.secondary">
                                                4.5 (123 reviews)
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Box>
                                <Typography variant="body2" color="text.secondary">
                                    Member since: January 2023
                                </Typography>
                            </CardContent>
                        </Card>
                    </Box>
                )}

                {/* Reviews Tab */}
                {tabValue === 2 && (
                    <Box sx={{ mt: 3 }}>
                        <Alert severity="info">
                            Reviews feature coming soon!
                        </Alert>
                    </Box>
                )}
            </Box>

            {/* Offer Dialog */}
            <OfferDialog
                open={offerDialogOpen}
                onClose={() => setOfferDialogOpen(false)}
                onSubmit={(offer) => onMakeOffer && onMakeOffer(product, offer)}
                product={product}
            />
        </Box>
    )
}