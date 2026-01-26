import React, { useState, useEffect, useCallback } from 'react';
import {
    Box,
    TextField,
    Button,
    Grid,
    Card,
    CardContent,
    Typography,
    Chip,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Slider,
    Switch,
    FormControlLabel,
    Alert,
    Autocomplete,
    IconButton,
    Collapse
} from '@mui/material';
import {
    Search as SearchIcon,
    FilterList as FilterIcon,
    Clear as ClearIcon
} from '@mui/icons-material';
import { useTranslation } from '../../hooks/useTranslation';
import { useLanguage } from '../../contexts/LanguageContext';
import { useGeolocation } from '../../hooks/useGeolocation';
import { ProductSearchQuery } from '../../services/productService';
import { ProductCategory } from '../../types';

// Types
interface SearchFilters {
    query: string;
    category: string;
    subcategory: string;
    minPrice: number;
    maxPrice: number;
    city: string;
    state: string;
    qualityGrades: string[];
    availableOnly: boolean;
    organicOnly: boolean;
    useLocation: boolean;
    radius: number;
    sortBy: string;
    sortOrder: string;
}

interface ProductSearchProps {
    onSearch: (query: ProductSearchQuery) => void;
    initialFilters?: Partial<SearchFilters>;
}

const CATEGORIES: ProductCategory[] = ['VEGETABLES', 'FRUITS', 'GRAINS', 'SPICES', 'DAIRY'];

const QUALITY_GRADES = [
    'PREMIUM',
    'GRADE_A',
    'GRADE_B',
    'STANDARD',
    'ORGANIC'
];

const SORT_OPTIONS = [
    { value: 'relevance', label: 'Relevance' },
    { value: 'price', label: 'Price' },
    { value: 'date', label: 'Date Added' },
    { value: 'rating', label: 'Vendor Rating' },
    { value: 'distance', label: 'Distance' },
    { value: 'popularity', label: 'Popularity' }
];

const INDIAN_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad',
    'Pune', 'Ahmedabad', 'Surat', 'Jaipur', 'Lucknow', 'Kanpur',
    'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri-Chinchwad'
];

const INDIAN_STATES = [
    'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Gujarat', 'Rajasthan',
    'Uttar Pradesh', 'West Bengal', 'Madhya Pradesh', 'Telangana', 'Andhra Pradesh'
];

export const ProductSearch: React.FC<ProductSearchProps> = ({ onSearch, initialFilters = {} }) => {
    // Get translated text with products namespace
    const t = (key: string) => {
        return useTranslation().t(`products.${key}`);
    };
    const { currentLanguage } = useLanguage();
    const { coordinates, error: locationError, getCurrentPosition, clearLocation } = useGeolocation();

    // State
    const [filters, setFilters] = useState<SearchFilters>({
        query: initialFilters.query || '',
        category: initialFilters.category || '',
        subcategory: initialFilters.subcategory || '',
        minPrice: initialFilters.minPrice || 0,
        maxPrice: initialFilters.maxPrice || 1000,
        city: initialFilters.city || '',
        state: initialFilters.state || '',
        qualityGrades: initialFilters.qualityGrades || [],
        availableOnly: initialFilters.availableOnly !== undefined ? initialFilters.availableOnly : true,
        organicOnly: initialFilters.organicOnly || false,
        useLocation: initialFilters.useLocation || false,
        radius: initialFilters.radius || 10,
        sortBy: initialFilters.sortBy || 'relevance',
        sortOrder: initialFilters.sortOrder || 'desc'
    });

    const [showFilters, setShowFilters] = useState(false);

    // Get user location when location filter is enabled
    useEffect(() => {
        if (filters.useLocation && !coordinates) {
            getCurrentPosition();
        } else if (!filters.useLocation) {
            clearLocation();
        }
    }, [filters.useLocation, coordinates, getCurrentPosition, clearLocation]);

    // Build search query and call onSearch
    const performSearch = useCallback(() => {
        const searchQuery: ProductSearchQuery = {
            language: currentLanguage,
            limit: 20,
            skip: 0
        };

        // Basic search parameters
        if (filters.query) searchQuery.query = filters.query;
        if (filters.category) searchQuery.category = filters.category as ProductCategory;
        if (filters.subcategory) searchQuery.subcategory = filters.subcategory;

        // Price filters
        if (filters.minPrice > 0) searchQuery.min_price = filters.minPrice;
        if (filters.maxPrice < 1000) searchQuery.max_price = filters.maxPrice;

        // Location filters
        if (filters.city) searchQuery.city = filters.city;
        if (filters.state) searchQuery.state = filters.state;

        // Geolocation
        if (filters.useLocation && coordinates) {
            searchQuery.latitude = coordinates.latitude;
            searchQuery.longitude = coordinates.longitude;
            searchQuery.radius_km = filters.radius;
        }

        // Quality and availability
        if (filters.qualityGrades.length > 0) searchQuery.quality_grades = filters.qualityGrades;
        searchQuery.available_only = filters.availableOnly;
        searchQuery.organic_only = filters.organicOnly;

        // Sorting
        searchQuery.sort_by = filters.sortBy;
        searchQuery.sort_order = filters.sortOrder;

        onSearch(searchQuery);
    }, [filters, currentLanguage, coordinates, onSearch]);

    // Handle search
    const handleSearch = () => {
        performSearch();
    };

    // Handle filter changes
    const handleFilterChange = (key: keyof SearchFilters, value: any) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    // Clear filters
    const clearFilters = () => {
        setFilters({
            query: '',
            category: '',
            subcategory: '',
            minPrice: 0,
            maxPrice: 1000,
            city: '',
            state: '',
            qualityGrades: [],
            availableOnly: true,
            organicOnly: false,
            useLocation: false,
            radius: 10,
            sortBy: 'relevance',
            sortOrder: 'desc'
        });
    };

    return (
        <Box>
            {/* Search Bar */}
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <TextField
                    fullWidth
                    placeholder={t('search_products_placeholder')}
                    value={filters.query}
                    onChange={(e) => handleFilterChange('query', e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    InputProps={{
                        startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    }}
                />
                <Button
                    variant="contained"
                    onClick={handleSearch}
                    sx={{ minWidth: 120 }}
                >
                    {t('search')}
                </Button>
                <IconButton
                    onClick={() => setShowFilters(!showFilters)}
                    color={showFilters ? 'primary' : 'default'}
                >
                    <FilterIcon />
                </IconButton>
            </Box>

            {/* Quick Filters */}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                {CATEGORIES.map(category => (
                    <Chip
                        key={category}
                        label={t(category.toLowerCase())}
                        onClick={() => handleFilterChange('category', filters.category === category ? '' : category)}
                        color={filters.category === category ? 'primary' : 'default'}
                        variant={filters.category === category ? 'filled' : 'outlined'}
                    />
                ))}
            </Box>

            {/* Advanced Filters */}
            <Collapse in={showFilters}>
                <Card sx={{ mb: 3 }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Typography variant="h6">{t('filters')}</Typography>
                            <Button onClick={clearFilters} startIcon={<ClearIcon />}>
                                {t('clear_filters')}
                            </Button>
                        </Box>

                        <Grid container spacing={3}>
                            {/* Category and Subcategory */}
                            <Grid item xs={12} md={6}>
                                <FormControl fullWidth>
                                    <InputLabel>{t('category')}</InputLabel>
                                    <Select
                                        value={filters.category}
                                        onChange={(e) => handleFilterChange('category', e.target.value)}
                                    >
                                        <MenuItem value="">{t('all_categories')}</MenuItem>
                                        {CATEGORIES.map(category => (
                                            <MenuItem key={category} value={category}>
                                                {t(category.toLowerCase())}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <TextField
                                    fullWidth
                                    label={t('subcategory')}
                                    value={filters.subcategory}
                                    onChange={(e) => handleFilterChange('subcategory', e.target.value)}
                                />
                            </Grid>

                            {/* Price Range */}
                            <Grid item xs={12}>
                                <Typography gutterBottom>{t('price_range')}</Typography>
                                <Box sx={{ px: 2 }}>
                                    <Slider
                                        value={[filters.minPrice, filters.maxPrice]}
                                        onChange={(_, value) => {
                                            const [min, max] = value as number[];
                                            handleFilterChange('minPrice', min);
                                            handleFilterChange('maxPrice', max);
                                        }}
                                        valueLabelDisplay="auto"
                                        min={0}
                                        max={1000}
                                        step={10}
                                        marks={[
                                            { value: 0, label: '₹0' },
                                            { value: 500, label: '₹500' },
                                            { value: 1000, label: '₹1000+' }
                                        ]}
                                    />
                                </Box>
                            </Grid>

                            {/* Location */}
                            <Grid item xs={12} md={6}>
                                <Autocomplete
                                    options={INDIAN_CITIES}
                                    value={filters.city}
                                    onChange={(_, value) => handleFilterChange('city', value || '')}
                                    renderInput={(params) => (
                                        <TextField {...params} label={t('city')} />
                                    )}
                                />
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <Autocomplete
                                    options={INDIAN_STATES}
                                    value={filters.state}
                                    onChange={(_, value) => handleFilterChange('state', value || '')}
                                    renderInput={(params) => (
                                        <TextField {...params} label={t('state')} />
                                    )}
                                />
                            </Grid>

                            {/* Geolocation */}
                            <Grid item xs={12}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={filters.useLocation}
                                            onChange={(e) => handleFilterChange('useLocation', e.target.checked)}
                                        />
                                    }
                                    label={t('use_my_location')}
                                />
                                {filters.useLocation && (
                                    <Box sx={{ mt: 2 }}>
                                        <Typography gutterBottom>{t('search_radius')} ({filters.radius} km)</Typography>
                                        <Slider
                                            value={filters.radius}
                                            onChange={(_, value) => handleFilterChange('radius', value)}
                                            min={1}
                                            max={50}
                                            step={1}
                                            valueLabelDisplay="auto"
                                            marks={[
                                                { value: 1, label: '1km' },
                                                { value: 25, label: '25km' },
                                                { value: 50, label: '50km' }
                                            ]}
                                        />
                                    </Box>
                                )}
                            </Grid>

                            {/* Quality Grades */}
                            <Grid item xs={12}>
                                <Typography gutterBottom>{t('quality_grades')}</Typography>
                                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                    {QUALITY_GRADES.map(grade => (
                                        <Chip
                                            key={grade}
                                            label={t(grade.toLowerCase())}
                                            onClick={() => {
                                                const newGrades = filters.qualityGrades.includes(grade)
                                                    ? filters.qualityGrades.filter(g => g !== grade)
                                                    : [...filters.qualityGrades, grade];
                                                handleFilterChange('qualityGrades', newGrades);
                                            }}
                                            color={filters.qualityGrades.includes(grade) ? 'primary' : 'default'}
                                            variant={filters.qualityGrades.includes(grade) ? 'filled' : 'outlined'}
                                        />
                                    ))}
                                </Box>
                            </Grid>

                            {/* Availability Options */}
                            <Grid item xs={12} md={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={filters.availableOnly}
                                            onChange={(e) => handleFilterChange('availableOnly', e.target.checked)}
                                        />
                                    }
                                    label={t('available_only')}
                                />
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={filters.organicOnly}
                                            onChange={(e) => handleFilterChange('organicOnly', e.target.checked)}
                                        />
                                    }
                                    label={t('organic_only')}
                                />
                            </Grid>

                            {/* Sorting */}
                            <Grid item xs={12} md={6}>
                                <FormControl fullWidth>
                                    <InputLabel>{t('sort_by')}</InputLabel>
                                    <Select
                                        value={filters.sortBy}
                                        onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                                    >
                                        {SORT_OPTIONS.map(option => (
                                            <MenuItem key={option.value} value={option.value}>
                                                {t(option.label.toLowerCase().replace(' ', '_'))}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <FormControl fullWidth>
                                    <InputLabel>{t('sort_order')}</InputLabel>
                                    <Select
                                        value={filters.sortOrder}
                                        onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
                                    >
                                        <MenuItem value="desc">{t('descending')}</MenuItem>
                                        <MenuItem value="asc">{t('ascending')}</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            </Collapse>

            {/* Error Display */}
            {locationError && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {locationError}
                </Alert>
            )}
        </Box>
    );
};