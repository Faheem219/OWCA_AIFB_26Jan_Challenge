import React, { useState, useCallback, useEffect } from 'react'
import {
    Box,
    Card,
    CardContent,
    Typography,
    TextField,
    Button,
    Grid,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Chip,
    Alert,
    CircularProgress,
    InputAdornment,
    FormControlLabel,
    Switch,
    Autocomplete,
    ImageList,
    ImageListItem,
    ImageListItemBar,
    IconButton,
    LinearProgress
} from '@mui/material'
import {
    CloudUpload as UploadIcon,
    Delete as DeleteIcon,
    Star as StarIcon,
    StarBorder as StarBorderIcon,
    Add as AddIcon,
    PhotoCamera as CameraIcon
} from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import { useTranslation } from '../../hooks/useTranslation'
import { useLanguage } from '../../contexts/LanguageContext'
import { productService, ProductCreateRequest } from '../../services/productService'
import { ProductCategory, MeasurementUnit, QualityGrade, Product } from '../../types'

interface ProductUploadFormProps {
    onSuccess?: (productId: string) => void
    onCancel?: () => void
    editMode?: boolean
    existingProduct?: Product | null
}

interface ImageFile {
    file: File
    preview: string
    isPrimary: boolean
    uploading: boolean
    uploaded: boolean
    url?: string
    error?: string
}

const CATEGORIES: ProductCategory[] = ['VEGETABLES', 'FRUITS', 'GRAINS', 'SPICES', 'DAIRY']

const QUALITY_GRADES = [
    { value: 'premium', label: 'Premium' },
    { value: 'grade_a', label: 'Grade A' },
    { value: 'grade_b', label: 'Grade B' },
    { value: 'standard', label: 'Standard' },
    { value: 'organic', label: 'Organic' }
]

const UNITS = [
    { value: 'kg', label: 'Kilogram (kg)' },
    { value: 'gram', label: 'Gram (g)' },
    { value: 'quintal', label: 'Quintal' },
    { value: 'ton', label: 'Ton' },
    { value: 'liter', label: 'Liter (L)' },
    { value: 'piece', label: 'Piece' },
    { value: 'dozen', label: 'Dozen' },
    { value: 'bag', label: 'Bag' },
    { value: 'box', label: 'Box' }
]

const COMMON_CERTIFICATIONS = [
    'Organic',
    'Fair Trade',
    'Non-GMO',
    'Pesticide Free',
    'Natural',
    'Fresh',
    'Local',
    'Seasonal'
]

export const ProductUploadForm: React.FC<ProductUploadFormProps> = ({
    onSuccess,
    onCancel,
    editMode = false,
    existingProduct = null
}) => {
    const { t } = useTranslation()
    const { currentLanguage } = useLanguage()

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        category: '' as ProductCategory | '',
        subcategory: '',
        basePrice: '',
        unit: 'kg' as MeasurementUnit,
        quantityAvailable: '',
        minimumOrder: '1',
        maximumOrder: '',
        qualityGrade: 'standard' as QualityGrade,
        harvestDate: '',
        expiryDate: '',
        origin: '',
        variety: '',
        marketName: '',
        negotiable: true,
        tags: [] as string[],
        certifications: [] as string[]
    })

    const [images, setImages] = useState<ImageFile[]>([])
    const [tagInput, setTagInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState(false)
    const [uploadProgress, setUploadProgress] = useState(0)

    // Populate form data when editing
    useEffect(() => {
        if (editMode && existingProduct) {
            const productName = typeof existingProduct.name === 'object'
                ? (existingProduct.name.originalText || '')
                : (existingProduct.name || '')
            const productDescription = typeof existingProduct.description === 'object'
                ? (existingProduct.description.originalText || '')
                : (existingProduct.description || '')

            // Cast to any to access dynamic properties from backend
            const product = existingProduct as any

            setFormData({
                name: productName,
                description: productDescription,
                category: existingProduct.category || '',
                subcategory: existingProduct.subcategory || '',
                basePrice: existingProduct.basePrice?.toString() || '',
                unit: (existingProduct.unit || 'kg') as MeasurementUnit,
                quantityAvailable: existingProduct.quantityAvailable?.toString() || '',
                minimumOrder: product.minimumOrder?.toString() || product.minimum_order?.toString() || '1',
                maximumOrder: product.maximumOrder?.toString() || product.maximum_order?.toString() || '',
                qualityGrade: (existingProduct.qualityGrade || product.quality_grade || 'standard') as QualityGrade,
                harvestDate: existingProduct.harvestDate || product.harvest_date || '',
                expiryDate: product.expiryDate || product.expiry_date || '',
                origin: product.origin || '',
                variety: product.variety || '',
                marketName: product.marketName || product.market_name || '',
                negotiable: product.negotiable !== false,
                tags: existingProduct.tags || [],
                certifications: product.certifications || []
            })

            // Load existing images if available
            if (existingProduct.images && existingProduct.images.length > 0) {
                const existingImages: ImageFile[] = existingProduct.images.map((img, index) => ({
                    file: null as any, // Existing images don't have a file
                    preview: img.url,
                    isPrimary: img.isPrimary || index === 0,
                    uploading: false,
                    uploaded: true,
                    url: img.url
                }))
                setImages(existingImages)
            }
        }
    }, [editMode, existingProduct])

    // Image upload handling
    const onDrop = useCallback((acceptedFiles: File[]) => {
        const newImages: ImageFile[] = acceptedFiles.map(file => ({
            file,
            preview: URL.createObjectURL(file),
            isPrimary: images.length === 0, // First image is primary by default
            uploading: false,
            uploaded: false
        }))

        setImages(prev => [...prev, ...newImages])
    }, [images.length])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'image/*': ['.jpeg', '.jpg', '.png', '.webp']
        },
        maxFiles: 10,
        maxSize: 5 * 1024 * 1024 // 5MB
    })

    const removeImage = (index: number) => {
        setImages(prev => {
            const newImages = prev.filter((_, i) => i !== index)
            // If we removed the primary image, make the first remaining image primary
            if (prev[index].isPrimary && newImages.length > 0) {
                newImages[0].isPrimary = true
            }
            return newImages
        })
    }

    const setPrimaryImage = (index: number) => {
        setImages(prev => prev.map((img, i) => ({
            ...img,
            isPrimary: i === index
        })))
    }

    const uploadImages = async (productId: string): Promise<string[]> => {
        const uploadedUrls: string[] = []

        for (let i = 0; i < images.length; i++) {
            const image = images[i]
            try {
                setImages(prev => prev.map((img, idx) =>
                    idx === i ? { ...img, uploading: true } : img
                ))

                const result = await productService.uploadProductImage(
                    productId,
                    image.file,
                    `${formData.name} - Image ${i + 1}`,
                    image.isPrimary
                )

                uploadedUrls.push(result.image_url)

                setImages(prev => prev.map((img, idx) =>
                    idx === i ? { ...img, uploading: false, uploaded: true, url: result.image_url } : img
                ))
            } catch (error) {
                setImages(prev => prev.map((img, idx) =>
                    idx === i ? { ...img, uploading: false, error: 'Upload failed' } : img
                ))
                throw error
            }
        }

        return uploadedUrls
    }

    const handleInputChange = (field: string, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        setError(null)
    }

    const addTag = () => {
        if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
            setFormData(prev => ({
                ...prev,
                tags: [...prev.tags, tagInput.trim()]
            }))
            setTagInput('')
        }
    }

    const removeTag = (tagToRemove: string) => {
        setFormData(prev => ({
            ...prev,
            tags: prev.tags.filter(tag => tag !== tagToRemove)
        }))
    }

    const validateForm = (): string | null => {
        if (!formData.name.trim()) return 'Product name is required'
        if (!formData.description.trim()) return 'Product description is required'
        if (!formData.category) return 'Category is required'
        if (!formData.basePrice || parseFloat(formData.basePrice) <= 0) return 'Valid base price is required'
        if (!formData.quantityAvailable || parseInt(formData.quantityAvailable) <= 0) return 'Valid quantity is required'
        if (images.length === 0) return 'At least one product image is required'
        if (formData.maximumOrder && parseInt(formData.maximumOrder) < parseInt(formData.minimumOrder)) {
            return 'Maximum order cannot be less than minimum order'
        }
        return null
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        const validationError = validateForm()
        if (validationError) {
            setError(validationError)
            return
        }

        setLoading(true)
        setError(null)
        setUploadProgress(0)

        try {
            // Build product data
            const productData: ProductCreateRequest = {
                name_text: formData.name,
                name_language: currentLanguage,
                description_text: formData.description,
                description_language: currentLanguage,
                category: formData.category as ProductCategory,
                subcategory: formData.subcategory || undefined,
                tags: formData.tags,
                base_price: parseFloat(formData.basePrice),
                negotiable: formData.negotiable,
                quantity_available: parseInt(formData.quantityAvailable),
                unit: formData.unit,
                minimum_order: parseInt(formData.minimumOrder),
                maximum_order: formData.maximumOrder ? parseInt(formData.maximumOrder) : undefined,
                quality_grade: formData.qualityGrade,
                harvest_date: formData.harvestDate || undefined,
                expiry_date: formData.expiryDate || undefined,
                certifications: formData.certifications,
                origin: formData.origin || undefined,
                variety: formData.variety || undefined,
                market_name: formData.marketName || undefined,
                image_urls: [] // Will be updated after image upload
            }

            setUploadProgress(20)

            let productId: string

            if (editMode && existingProduct) {
                // Update existing product
                await productService.updateProduct(existingProduct.id, productData)
                productId = existingProduct.id
                setUploadProgress(40)

                // Upload new images (only those without URLs)
                const newImages = images.filter(img => !img.url)
                if (newImages.length > 0) {
                    await uploadImages(productId)
                }
            } else {
                // Create new product
                const product = await productService.createProduct(productData)
                productId = product.id
                setUploadProgress(40)

                // Upload images
                await uploadImages(productId)
            }

            setUploadProgress(80)

            // Update product with image URLs
            await productService.updateProduct(productId, {
                // Note: The backend should handle image association through the upload endpoint
            })

            setUploadProgress(100)
            setSuccess(true)

            // Call success callback
            if (onSuccess) {
                onSuccess(productId)
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : editMode ? 'Failed to update product' : 'Failed to create product')
        } finally {
            setLoading(false)
        }
    }

    if (success) {
        return (
            <Card>
                <CardContent>
                    <Box textAlign="center" py={4}>
                        <Typography variant="h5" color="primary" gutterBottom>
                            {editMode ? 'Product Updated Successfully!' : 'Product Created Successfully!'}
                        </Typography>
                        <Typography variant="body1" color="text.secondary" gutterBottom>
                            {editMode ? 'Your product has been updated.' : 'Your product has been listed in the marketplace.'}
                        </Typography>
                        <Button
                            variant="contained"
                            onClick={() => onSuccess && onSuccess('')}
                            sx={{ mt: 2 }}
                        >
                            View Product
                        </Button>
                    </Box>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card>
            <CardContent>
                <Typography variant="h5" gutterBottom>
                    {editMode ? 'Edit Product' : 'Add New Product'}
                </Typography>

                {error && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                        {error}
                    </Alert>
                )}

                {loading && (
                    <Box sx={{ mb: 3 }}>
                        <LinearProgress variant="determinate" value={uploadProgress} />
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            {uploadProgress < 40 ? 'Creating product...' :
                                uploadProgress < 80 ? 'Uploading images...' : 'Finalizing...'}
                        </Typography>
                    </Box>
                )}

                <form onSubmit={handleSubmit}>
                    <Grid container spacing={3}>
                        {/* Basic Information */}
                        <Grid item xs={12}>
                            <Typography variant="h6" gutterBottom>
                                Basic Information
                            </Typography>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Product Name"
                                value={formData.name}
                                onChange={(e) => handleInputChange('name', e.target.value)}
                                required
                                disabled={loading}
                            />
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <FormControl fullWidth required>
                                <InputLabel>Category</InputLabel>
                                <Select
                                    value={formData.category}
                                    onChange={(e) => handleInputChange('category', e.target.value)}
                                    disabled={loading}
                                >
                                    {CATEGORIES.map(category => (
                                        <MenuItem key={category} value={category}>
                                            {t(`products.${category.toLowerCase()}`)}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Subcategory (Optional)"
                                value={formData.subcategory}
                                onChange={(e) => handleInputChange('subcategory', e.target.value)}
                                disabled={loading}
                            />
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Variety (Optional)"
                                value={formData.variety}
                                onChange={(e) => handleInputChange('variety', e.target.value)}
                                disabled={loading}
                                placeholder="e.g., Basmati, Red Onion, etc."
                            />
                        </Grid>

                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Description"
                                value={formData.description}
                                onChange={(e) => handleInputChange('description', e.target.value)}
                                multiline
                                rows={4}
                                required
                                disabled={loading}
                                placeholder="Describe your product in detail..."
                            />
                        </Grid>

                        {/* Pricing and Quantity */}
                        <Grid item xs={12}>
                            <Typography variant="h6" gutterBottom>
                                Pricing & Quantity
                            </Typography>
                        </Grid>

                        <Grid item xs={12} md={4}>
                            <TextField
                                fullWidth
                                label="Base Price"
                                type="number"
                                value={formData.basePrice}
                                onChange={(e) => handleInputChange('basePrice', e.target.value)}
                                required
                                disabled={loading}
                                InputProps={{
                                    startAdornment: <InputAdornment position="start">₹</InputAdornment>
                                }}
                            />
                        </Grid>

                        <Grid item xs={12} md={4}>
                            <FormControl fullWidth required>
                                <InputLabel>Unit</InputLabel>
                                <Select
                                    value={formData.unit}
                                    onChange={(e) => handleInputChange('unit', e.target.value)}
                                    disabled={loading}
                                >
                                    {UNITS.map(unit => (
                                        <MenuItem key={unit.value} value={unit.value}>
                                            {unit.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>

                        <Grid item xs={12} md={4}>
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={formData.negotiable}
                                        onChange={(e) => handleInputChange('negotiable', e.target.checked)}
                                        disabled={loading}
                                    />
                                }
                                label="Price Negotiable"
                            />
                        </Grid>

                        <Grid item xs={12} md={4}>
                            <TextField
                                fullWidth
                                label="Available Quantity"
                                type="number"
                                value={formData.quantityAvailable}
                                onChange={(e) => handleInputChange('quantityAvailable', e.target.value)}
                                required
                                disabled={loading}
                            />
                        </Grid>

                        <Grid item xs={12} md={4}>
                            <TextField
                                fullWidth
                                label="Minimum Order"
                                type="number"
                                value={formData.minimumOrder}
                                onChange={(e) => handleInputChange('minimumOrder', e.target.value)}
                                required
                                disabled={loading}
                            />
                        </Grid>

                        <Grid item xs={12} md={4}>
                            <TextField
                                fullWidth
                                label="Maximum Order (Optional)"
                                type="number"
                                value={formData.maximumOrder}
                                onChange={(e) => handleInputChange('maximumOrder', e.target.value)}
                                disabled={loading}
                            />
                        </Grid>

                        {/* Quality and Details */}
                        <Grid item xs={12}>
                            <Typography variant="h6" gutterBottom>
                                Quality & Details
                            </Typography>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <FormControl fullWidth required>
                                <InputLabel>Quality Grade</InputLabel>
                                <Select
                                    value={formData.qualityGrade}
                                    onChange={(e) => handleInputChange('qualityGrade', e.target.value)}
                                    disabled={loading}
                                >
                                    {QUALITY_GRADES.map(grade => (
                                        <MenuItem key={grade.value} value={grade.value}>
                                            {grade.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Origin (Optional)"
                                value={formData.origin}
                                onChange={(e) => handleInputChange('origin', e.target.value)}
                                disabled={loading}
                                placeholder="e.g., Punjab, Maharashtra, etc."
                            />
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Harvest Date (Optional)"
                                type="date"
                                value={formData.harvestDate}
                                onChange={(e) => handleInputChange('harvestDate', e.target.value)}
                                disabled={loading}
                                InputLabelProps={{ shrink: true }}
                            />
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Expiry Date (Optional)"
                                type="date"
                                value={formData.expiryDate}
                                onChange={(e) => handleInputChange('expiryDate', e.target.value)}
                                disabled={loading}
                                InputLabelProps={{ shrink: true }}
                            />
                        </Grid>

                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Market Name (Optional)"
                                value={formData.marketName}
                                onChange={(e) => handleInputChange('marketName', e.target.value)}
                                disabled={loading}
                                placeholder="e.g., Azadpur Mandi, Crawford Market, etc."
                            />
                        </Grid>

                        {/* Certifications */}
                        <Grid item xs={12}>
                            <Typography variant="subtitle1" gutterBottom>
                                Certifications
                            </Typography>
                            <Autocomplete
                                multiple
                                options={COMMON_CERTIFICATIONS}
                                value={formData.certifications}
                                onChange={(_, newValue) => handleInputChange('certifications', newValue)}
                                disabled={loading}
                                renderTags={(value, getTagProps) =>
                                    value.map((option, index) => (
                                        <Chip
                                            variant="outlined"
                                            label={option}
                                            {...getTagProps({ index })}
                                            key={option}
                                        />
                                    ))
                                }
                                renderInput={(params) => (
                                    <TextField
                                        {...params}
                                        placeholder="Select or add certifications"
                                    />
                                )}
                                freeSolo
                            />
                        </Grid>

                        {/* Tags */}
                        <Grid item xs={12}>
                            <Typography variant="subtitle1" gutterBottom>
                                Tags
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                                {formData.tags.map((tag) => (
                                    <Chip
                                        key={tag}
                                        label={tag}
                                        onDelete={() => removeTag(tag)}
                                        disabled={loading}
                                    />
                                ))}
                            </Box>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <TextField
                                    fullWidth
                                    placeholder="Add tags to help buyers find your product"
                                    value={tagInput}
                                    onChange={(e) => setTagInput(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                                    disabled={loading}
                                />
                                <Button
                                    variant="outlined"
                                    onClick={addTag}
                                    disabled={!tagInput.trim() || loading}
                                    startIcon={<AddIcon />}
                                >
                                    Add
                                </Button>
                            </Box>
                        </Grid>

                        {/* Images */}
                        <Grid item xs={12}>
                            <Typography variant="h6" gutterBottom>
                                Product Images
                            </Typography>

                            {images.length > 0 && (
                                <ImageList sx={{ mb: 2 }} cols={4} rowHeight={200}>
                                    {images.map((image, index) => (
                                        <ImageListItem key={index}>
                                            <img
                                                src={image.preview}
                                                alt={`Product ${index + 1}`}
                                                loading="lazy"
                                                style={{ objectFit: 'cover' }}
                                            />
                                            <ImageListItemBar
                                                title={image.isPrimary ? 'Primary Image' : `Image ${index + 1}`}
                                                actionIcon={
                                                    <Box>
                                                        <IconButton
                                                            sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                                                            onClick={() => setPrimaryImage(index)}
                                                            disabled={loading}
                                                        >
                                                            {image.isPrimary ? <StarIcon /> : <StarBorderIcon />}
                                                        </IconButton>
                                                        <IconButton
                                                            sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                                                            onClick={() => removeImage(index)}
                                                            disabled={loading}
                                                        >
                                                            <DeleteIcon />
                                                        </IconButton>
                                                    </Box>
                                                }
                                            />
                                            {image.uploading && (
                                                <Box
                                                    sx={{
                                                        position: 'absolute',
                                                        top: 0,
                                                        left: 0,
                                                        right: 0,
                                                        bottom: 0,
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        backgroundColor: 'rgba(0, 0, 0, 0.5)'
                                                    }}
                                                >
                                                    <CircularProgress size={40} />
                                                </Box>
                                            )}
                                        </ImageListItem>
                                    ))}
                                </ImageList>
                            )}

                            <Box
                                {...getRootProps()}
                                sx={{
                                    border: '2px dashed',
                                    borderColor: isDragActive ? 'primary.main' : 'grey.300',
                                    borderRadius: 2,
                                    p: 4,
                                    textAlign: 'center',
                                    cursor: 'pointer',
                                    backgroundColor: isDragActive ? 'action.hover' : 'transparent',
                                    '&:hover': {
                                        backgroundColor: 'action.hover'
                                    }
                                }}
                            >
                                <input {...getInputProps()} disabled={loading} />
                                <CameraIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                                <Typography variant="h6" gutterBottom>
                                    {isDragActive ? 'Drop images here' : 'Upload Product Images'}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Drag and drop images here, or click to select files
                                </Typography>
                                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                                    Maximum 10 images, 5MB each. Supported formats: JPEG, PNG, WebP
                                </Typography>
                            </Box>
                        </Grid>

                        {/* Submit Buttons */}
                        <Grid item xs={12}>
                            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                                {onCancel && (
                                    <Button
                                        variant="outlined"
                                        onClick={onCancel}
                                        disabled={loading}
                                    >
                                        Cancel
                                    </Button>
                                )}
                                <Button
                                    type="submit"
                                    variant="contained"
                                    disabled={loading}
                                    startIcon={loading ? <CircularProgress size={20} /> : <UploadIcon />}
                                >
                                    {loading 
                                        ? (editMode ? 'Updating Product...' : 'Creating Product...') 
                                        : (editMode ? 'Update Product' : 'Create Product')}
                                </Button>
                            </Box>
                        </Grid>
                    </Grid>
                </form>
            </CardContent>
        </Card>
    )
}