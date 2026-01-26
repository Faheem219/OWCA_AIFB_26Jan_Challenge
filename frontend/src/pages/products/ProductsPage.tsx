import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
    Container,
    Box,
    Typography,
    Pagination,
    Alert,
    Fab,
    Breadcrumbs,
    Link
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { ProductSearch } from '../../components/products/ProductSearch'
import { ProductGrid } from '../../components/products/ProductGrid'
import { productService, ProductSearchQuery } from '../../services/productService'
import { useLanguage } from '../../contexts/LanguageContext'
import { useAuth } from '../../hooks/useAuth'
import { Product, ProductCategory } from '../../types'

export const ProductsPage: React.FC = () => {
    const navigate = useNavigate()
    const [searchParams, setSearchParams] = useSearchParams()
    const { currentLanguage } = useLanguage()
    const { user } = useAuth()

    const [products, setProducts] = useState<Product[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [totalCount, setTotalCount] = useState(0)
    const [currentPage, setCurrentPage] = useState(1)
    const [totalPages, setTotalPages] = useState(0)
    const [searchMetadata, setSearchMetadata] = useState<any>(null)
    const [favoriteProductIds, setFavoriteProductIds] = useState<Set<string>>(new Set())

    const itemsPerPage = 20

    // Parse search parameters from URL
    const getSearchQueryFromParams = useCallback((): ProductSearchQuery => {
        const query: ProductSearchQuery = {
            language: currentLanguage,
            limit: itemsPerPage,
            skip: (currentPage - 1) * itemsPerPage
        }

        // Parse URL parameters
        const searchText = searchParams.get('q')
        if (searchText) query.query = searchText

        const category = searchParams.get('category')
        if (category) query.category = category as ProductCategory

        const subcategory = searchParams.get('subcategory')
        if (subcategory) query.subcategory = subcategory

        const minPrice = searchParams.get('min_price')
        if (minPrice) query.min_price = parseFloat(minPrice)

        const maxPrice = searchParams.get('max_price')
        if (maxPrice) query.max_price = parseFloat(maxPrice)

        const city = searchParams.get('city')
        if (city) query.city = city

        const state = searchParams.get('state')
        if (state) query.state = state

        const latitude = searchParams.get('lat')
        const longitude = searchParams.get('lng')
        if (latitude && longitude) {
            query.latitude = parseFloat(latitude)
            query.longitude = parseFloat(longitude)
        }

        const radius = searchParams.get('radius')
        if (radius) query.radius_km = parseFloat(radius)

        const qualityGrades = searchParams.get('quality')
        if (qualityGrades) query.quality_grades = qualityGrades.split(',')

        const availableOnly = searchParams.get('available')
        if (availableOnly) query.available_only = availableOnly === 'true'

        const organicOnly = searchParams.get('organic')
        if (organicOnly) query.organic_only = organicOnly === 'true'

        const sortBy = searchParams.get('sort')
        if (sortBy) query.sort_by = sortBy

        const sortOrder = searchParams.get('order')
        if (sortOrder) query.sort_order = sortOrder

        return query
    }, [searchParams, currentLanguage, currentPage, itemsPerPage])

    // Update URL parameters
    const updateSearchParams = (newParams: Partial<ProductSearchQuery>) => {
        const params = new URLSearchParams(searchParams)

        Object.entries(newParams).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                if (Array.isArray(value)) {
                    params.set(key, value.join(','))
                } else {
                    params.set(key, value.toString())
                }
            } else {
                params.delete(key)
            }
        })

        // Reset page when search parameters change
        if (key !== 'skip' && key !== 'limit') {
            params.delete('page')
            setCurrentPage(1)
        }

        setSearchParams(params)
    }

    // Perform search
    const performSearch = useCallback(async (searchQuery: ProductSearchQuery) => {
        setLoading(true)
        setError(null)

        try {
            const result = await productService.searchProducts(searchQuery)

            setProducts(result.products)
            setTotalCount(result.total_count)
            setTotalPages(result.page_info.total_pages)
            setSearchMetadata(result.search_metadata)

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Search failed')
            setProducts([])
            setTotalCount(0)
            setTotalPages(0)
        } finally {
            setLoading(false)
        }
    }, [])

    // Load products when search parameters change
    useEffect(() => {
        const searchQuery = getSearchQueryFromParams()
        performSearch(searchQuery)
    }, [getSearchQueryFromParams, performSearch])

    // Load user favorites
    useEffect(() => {
        const loadFavorites = async () => {
            if (user) {
                try {
                    // TODO: Implement favorites API
                    // const favorites = await favoriteService.getUserFavorites()
                    // setFavoriteProductIds(new Set(favorites.map(f => f.productId)))
                } catch (err) {
                    console.error('Failed to load favorites:', err)
                }
            }
        }

        loadFavorites()
    }, [user])

    const handleSearch = (searchQuery: ProductSearchQuery) => {
        updateSearchParams(searchQuery)
    }

    const handleProductClick = (product: Product) => {
        navigate(`/products/${product.id}`)
    }

    const handleFavoriteToggle = async (productId: string, isFavorited: boolean) => {
        try {
            // TODO: Implement favorite/unfavorite API
            const newFavorites = new Set(favoriteProductIds)
            if (isFavorited) {
                newFavorites.add(productId)
            } else {
                newFavorites.delete(productId)
            }
            setFavoriteProductIds(newFavorites)
        } catch (err) {
            console.error('Failed to toggle favorite:', err)
        }
    }

    const handleShare = (product: Product) => {
        const productUrl = `${window.location.origin}/products/${product.id}`

        if (navigator.share) {
            navigator.share({
                title: product.name.originalText,
                text: product.description.originalText,
                url: productUrl
            })
        } else {
            navigator.clipboard.writeText(productUrl)
        }
    }

    const handleMakeOffer = (product: Product) => {
        // Navigate to product detail page where user can make offer
        navigate(`/products/${product.id}`)
    }

    const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
        setCurrentPage(page)
        const params = new URLSearchParams(searchParams)
        params.set('page', page.toString())
        setSearchParams(params)

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    const isVendor = user?.role === 'VENDOR'

    return (
        <Container maxWidth="xl">
            <Box sx={{ py: 4 }}>
                {/* Breadcrumbs */}
                <Breadcrumbs sx={{ mb: 3 }}>
                    <Link
                        color="inherit"
                        href="/"
                        onClick={(e) => {
                            e.preventDefault()
                            navigate('/')
                        }}
                    >
                        Home
                    </Link>
                    <Typography color="text.primary">Products</Typography>
                </Breadcrumbs>

                {/* Page Header */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                    <Box>
                        <Typography variant="h4" component="h1" gutterBottom>
                            Marketplace
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            Discover fresh products from local vendors
                        </Typography>
                    </Box>
                </Box>

                {/* Search Interface */}
                <Box sx={{ mb: 4 }}>
                    <ProductSearch onSearch={handleSearch} />
                </Box>

                {/* Error Display */}
                {error && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                        {error}
                    </Alert>
                )}

                {/* Search Results Header */}
                {searchMetadata && (
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            {totalCount} products found
                            {searchMetadata.query && ` for "${searchMetadata.query}"`}
                        </Typography>

                        {searchMetadata.search_time_ms && (
                            <Typography variant="body2" color="text.secondary">
                                Search completed in {searchMetadata.search_time_ms}ms
                            </Typography>
                        )}

                        {searchMetadata.filters_applied && searchMetadata.filters_applied.length > 0 && (
                            <Typography variant="body2" color="text.secondary">
                                Filters applied: {searchMetadata.filters_applied.join(', ')}
                            </Typography>
                        )}
                    </Box>
                )}

                {/* Product Grid */}
                <ProductGrid
                    products={products}
                    loading={loading}
                    onProductClick={handleProductClick}
                    onFavoriteToggle={handleFavoriteToggle}
                    onShare={handleShare}
                    onMakeOffer={handleMakeOffer}
                    favoriteProductIds={favoriteProductIds}
                    showVendorInfo={true}
                    columns={{ xs: 1, sm: 2, md: 3, lg: 4, xl: 5 }}
                />

                {/* Pagination */}
                {totalPages > 1 && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 6 }}>
                        <Pagination
                            count={totalPages}
                            page={currentPage}
                            onChange={handlePageChange}
                            color="primary"
                            size="large"
                            showFirstButton
                            showLastButton
                        />
                    </Box>
                )}

                {/* Floating Action Button for Vendors */}
                {isVendor && (
                    <Fab
                        color="primary"
                        aria-label="add product"
                        sx={{
                            position: 'fixed',
                            bottom: 24,
                            right: 24,
                            zIndex: 1000
                        }}
                        onClick={() => navigate('/products/create')}
                    >
                        <AddIcon />
                    </Fab>
                )}
            </Box>
        </Container>
    )
}