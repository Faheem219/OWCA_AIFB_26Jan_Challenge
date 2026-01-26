import React, { useState } from 'react'
import {
    Box,
    Card,
    CardContent,
    Typography,
    TextField,
    Button,
    Grid,
    Avatar,
    IconButton,
    Alert,
    Divider,
    Chip,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    OutlinedInput,
    SelectChangeEvent,
} from '@mui/material'
import { PhotoCamera, Save, Cancel } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { User, VendorProfile, BuyerProfile, SupportedLanguage, LocationData, ProductCategory } from '../../types'
import { LanguageSelector } from '../auth/LanguageSelector'
import { LocationSelector } from '../auth/LocationSelector'
import { profileService } from '../../services/profileService'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface ProfileFormProps {
    user: User | VendorProfile | BuyerProfile
    onUpdate: (updatedUser: User | VendorProfile | BuyerProfile) => void
    onCancel?: () => void
}

const productCategories: ProductCategory[] = [
    'VEGETABLES',
    'FRUITS',
    'GRAINS',
    'SPICES',
    'DAIRY',
]

export const ProfileForm: React.FC<ProfileFormProps> = ({
    user,
    onUpdate,
    onCancel,
}) => {
    const { t } = useTranslation()
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)

    const [formData, setFormData] = useState({
        preferredLanguages: user.preferredLanguages,
        location: user.location,
        phone: '',
        // Vendor fields
        businessName: (user as VendorProfile).businessName || '',
        businessType: (user as VendorProfile).businessType || '',
        productCategories: (user as VendorProfile).productCategories || [],
        marketLocation: (user as VendorProfile).marketLocation || '',
        // Buyer fields
        preferredCategories: (user as BuyerProfile).preferredCategories || [],
        budgetMin: (user as BuyerProfile).budgetRange?.min || 0,
        budgetMax: (user as BuyerProfile).budgetRange?.max || 10000,
        budgetCurrency: (user as BuyerProfile).budgetRange?.currency || 'INR',
    })

    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = event.target
        setFormData(prev => ({
            ...prev,
            [name]: value,
        }))

        // Clear validation error
        if (validationErrors[name]) {
            setValidationErrors(prev => ({
                ...prev,
                [name]: '',
            }))
        }

        // Clear messages
        setError(null)
        setSuccess(null)
    }

    const handleLanguagesChange = (languages: SupportedLanguage[]) => {
        setFormData(prev => ({ ...prev, preferredLanguages: languages }))
    }

    const handleLocationChange = (location: LocationData) => {
        setFormData(prev => ({ ...prev, location }))
    }

    const handleCategoriesChange = (event: SelectChangeEvent<ProductCategory[]>) => {
        const value = event.target.value
        const categories = typeof value === 'string' ? [value as ProductCategory] : value as ProductCategory[]

        if (user.role === 'VENDOR') {
            setFormData(prev => ({ ...prev, productCategories: categories }))
        } else {
            setFormData(prev => ({ ...prev, preferredCategories: categories }))
        }
    }

    const validateForm = () => {
        const errors: Record<string, string> = {}

        if (formData.preferredLanguages.length === 0) {
            errors.preferredLanguages = 'Please select at least one preferred language'
        }

        if (!formData.location || !formData.location.address) {
            errors.location = 'Please enter your location'
        }

        if (user.role === 'VENDOR') {
            if (!formData.businessName.trim()) {
                errors.businessName = 'Business name is required'
            }
            if (!formData.businessType.trim()) {
                errors.businessType = 'Business type is required'
            }
            if (formData.productCategories.length === 0) {
                errors.productCategories = 'Please select at least one product category'
            }
        }

        if (user.role === 'BUYER') {
            if (formData.budgetMin < 0) {
                errors.budgetMin = 'Minimum budget cannot be negative'
            }
            if (formData.budgetMax <= formData.budgetMin) {
                errors.budgetMax = 'Maximum budget must be greater than minimum budget'
            }
        }

        setValidationErrors(errors)
        return Object.keys(errors).length === 0
    }

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault()

        if (!validateForm()) {
            return
        }

        setIsLoading(true)
        setError(null)
        setSuccess(null)

        try {
            const updateData: any = {
                preferred_languages: formData.preferredLanguages,
                location: formData.location,
                phone: formData.phone || undefined,
            }

            if (user.role === 'VENDOR') {
                updateData.business_name = formData.businessName
                updateData.business_type = formData.businessType
                updateData.product_categories = formData.productCategories
                updateData.market_location = formData.marketLocation
            } else {
                updateData.preferred_categories = formData.preferredCategories
                if (formData.budgetMin > 0 || formData.budgetMax > 0) {
                    updateData.budget_range = {
                        min: formData.budgetMin,
                        max: formData.budgetMax,
                        currency: formData.budgetCurrency,
                    }
                }
            }

            const updatedUser = await profileService.updateProfile(updateData)
            onUpdate(updatedUser)
            setSuccess('Profile updated successfully!')
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to update profile')
        } finally {
            setIsLoading(false)
        }
    }

    const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0]
        if (!file) return

        setIsLoading(true)
        try {
            await profileService.uploadProfileImage(file)
            setSuccess('Profile image updated successfully!')
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to upload image')
        } finally {
            setIsLoading(false)
        }
    }

    if (isLoading) {
        return <LoadingSpinner message="Updating profile..." />
    }

    return (
        <Card>
            <CardContent>
                <Typography variant="h5" gutterBottom>
                    {t('profile.updateProfile')}
                </Typography>

                {error && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                        {error}
                    </Alert>
                )}

                {success && (
                    <Alert severity="success" sx={{ mb: 3 }}>
                        {success}
                    </Alert>
                )}

                <form onSubmit={handleSubmit}>
                    {/* Profile Image */}
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <Avatar
                            sx={{ width: 80, height: 80, mr: 2 }}
                            src="" // Profile image URL would go here
                        >
                            {user.email.charAt(0).toUpperCase()}
                        </Avatar>
                        <Box>
                            <input
                                accept="image/*"
                                style={{ display: 'none' }}
                                id="profile-image-upload"
                                type="file"
                                onChange={handleImageUpload}
                            />
                            <label htmlFor="profile-image-upload">
                                <IconButton color="primary" component="span">
                                    <PhotoCamera />
                                </IconButton>
                            </label>
                            <Typography variant="body2" color="text.secondary">
                                Click to upload profile image
                            </Typography>
                        </Box>
                    </Box>

                    <Grid container spacing={3}>
                        {/* Basic Information */}
                        <Grid item xs={12}>
                            <Typography variant="h6" gutterBottom>
                                {t('profile.personalInfo')}
                            </Typography>
                            <Divider sx={{ mb: 2 }} />
                        </Grid>

                        <Grid item xs={12} sm={6}>
                            <TextField
                                fullWidth
                                label={t('auth.email')}
                                value={user.email}
                                disabled
                                helperText="Email cannot be changed"
                            />
                        </Grid>

                        <Grid item xs={12} sm={6}>
                            <TextField
                                fullWidth
                                name="phone"
                                label={t('auth.phone')}
                                value={formData.phone}
                                onChange={handleInputChange}
                                placeholder="+91 9876543210"
                            />
                        </Grid>

                        <Grid item xs={12}>
                            <LanguageSelector
                                selectedLanguages={formData.preferredLanguages}
                                onChange={handleLanguagesChange}
                                required
                                error={!!validationErrors.preferredLanguages}
                                helperText={validationErrors.preferredLanguages}
                            />
                        </Grid>

                        <Grid item xs={12}>
                            <LocationSelector
                                location={formData.location}
                                onChange={handleLocationChange}
                                required
                                error={!!validationErrors.location}
                                helperText={validationErrors.location}
                            />
                        </Grid>

                        {/* Role-specific fields */}
                        {user.role === 'VENDOR' && (
                            <>
                                <Grid item xs={12}>
                                    <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                                        {t('profile.businessInfo')}
                                    </Typography>
                                    <Divider sx={{ mb: 2 }} />
                                </Grid>

                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        name="businessName"
                                        label={t('auth.businessName')}
                                        value={formData.businessName}
                                        onChange={handleInputChange}
                                        required
                                        error={!!validationErrors.businessName}
                                        helperText={validationErrors.businessName}
                                    />
                                </Grid>

                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        name="businessType"
                                        label="Business Type"
                                        value={formData.businessType}
                                        onChange={handleInputChange}
                                        required
                                        error={!!validationErrors.businessType}
                                        helperText={validationErrors.businessType}
                                        placeholder="e.g., Wholesale, Retail, Farm"
                                    />
                                </Grid>

                                <Grid item xs={12} sm={6}>
                                    <FormControl fullWidth required error={!!validationErrors.productCategories}>
                                        <InputLabel>Product Categories</InputLabel>
                                        <Select
                                            multiple
                                            value={formData.productCategories}
                                            onChange={handleCategoriesChange}
                                            input={<OutlinedInput label="Product Categories" />}
                                            renderValue={(selected) => (
                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                                    {selected.map((value) => (
                                                        <Chip key={value} label={value} size="small" />
                                                    ))}
                                                </Box>
                                            )}
                                        >
                                            {productCategories.map((category) => (
                                                <MenuItem key={category} value={category}>
                                                    {category}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                        {validationErrors.productCategories && (
                                            <Typography variant="body2" color="error" sx={{ mt: 1, ml: 2 }}>
                                                {validationErrors.productCategories}
                                            </Typography>
                                        )}
                                    </FormControl>
                                </Grid>

                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        name="marketLocation"
                                        label="Market Location"
                                        value={formData.marketLocation}
                                        onChange={handleInputChange}
                                        placeholder="e.g., Azadpur Mandi, Delhi"
                                    />
                                </Grid>
                            </>
                        )}

                        {user.role === 'BUYER' && (
                            <>
                                <Grid item xs={12}>
                                    <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                                        {t('profile.preferences')}
                                    </Typography>
                                    <Divider sx={{ mb: 2 }} />
                                </Grid>

                                <Grid item xs={12}>
                                    <FormControl fullWidth>
                                        <InputLabel>Preferred Categories</InputLabel>
                                        <Select
                                            multiple
                                            value={formData.preferredCategories}
                                            onChange={handleCategoriesChange}
                                            input={<OutlinedInput label="Preferred Categories" />}
                                            renderValue={(selected) => (
                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                                    {selected.map((value) => (
                                                        <Chip key={value} label={value} size="small" />
                                                    ))}
                                                </Box>
                                            )}
                                        >
                                            {productCategories.map((category) => (
                                                <MenuItem key={category} value={category}>
                                                    {category}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                </Grid>

                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        name="budgetMin"
                                        label="Min Budget"
                                        type="number"
                                        value={formData.budgetMin}
                                        onChange={handleInputChange}
                                        error={!!validationErrors.budgetMin}
                                        helperText={validationErrors.budgetMin}
                                        InputProps={{
                                            startAdornment: <Typography sx={{ mr: 1 }}>₹</Typography>,
                                        }}
                                    />
                                </Grid>

                                <Grid item xs={12} sm={4}>
                                    <TextField
                                        fullWidth
                                        name="budgetMax"
                                        label="Max Budget"
                                        type="number"
                                        value={formData.budgetMax}
                                        onChange={handleInputChange}
                                        error={!!validationErrors.budgetMax}
                                        helperText={validationErrors.budgetMax}
                                        InputProps={{
                                            startAdornment: <Typography sx={{ mr: 1 }}>₹</Typography>,
                                        }}
                                    />
                                </Grid>

                                <Grid item xs={12} sm={4}>
                                    <FormControl fullWidth>
                                        <InputLabel>Currency</InputLabel>
                                        <Select
                                            name="budgetCurrency"
                                            value={formData.budgetCurrency}
                                            onChange={(e) => setFormData(prev => ({ ...prev, budgetCurrency: e.target.value }))}
                                            input={<OutlinedInput label="Currency" />}
                                        >
                                            <MenuItem value="INR">INR (₹)</MenuItem>
                                            <MenuItem value="USD">USD ($)</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Grid>
                            </>
                        )}

                        {/* Action Buttons */}
                        <Grid item xs={12}>
                            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 3 }}>
                                {onCancel && (
                                    <Button
                                        variant="outlined"
                                        startIcon={<Cancel />}
                                        onClick={onCancel}
                                    >
                                        Cancel
                                    </Button>
                                )}
                                <Button
                                    type="submit"
                                    variant="contained"
                                    startIcon={<Save />}
                                    disabled={isLoading}
                                >
                                    {t('common.save')}
                                </Button>
                            </Box>
                        </Grid>
                    </Grid>
                </form>
            </CardContent>
        </Card>
    )
}