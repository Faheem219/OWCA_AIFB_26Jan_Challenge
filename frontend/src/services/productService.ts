import {
    Product,
    ProductCategory,
    SupportedLanguage,
    MeasurementUnit,
    QualityGrade
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export interface ProductCreateRequest {
    name_text: string
    name_language: SupportedLanguage
    description_text: string
    description_language: SupportedLanguage
    category: string // lowercase category to match backend
    subcategory?: string
    tags: string[]
    base_price: number
    negotiable: boolean
    quantity_available: number
    unit: MeasurementUnit
    minimum_order: number
    maximum_order?: number
    quality_grade: QualityGrade
    harvest_date?: string
    expiry_date?: string
    certifications: string[]
    origin?: string
    variety?: string
    location_address?: string
    market_name?: string
    image_urls: string[]
}

export interface ProductUpdateRequest {
    name_text?: string
    name_language?: SupportedLanguage
    description_text?: string
    description_language?: SupportedLanguage
    subcategory?: string
    tags?: string[]
    base_price?: number
    negotiable?: boolean
    quantity_available?: number
    minimum_order?: number
    maximum_order?: number
    quality_grade?: string
    harvest_date?: string
    expiry_date?: string
    certifications?: string[]
    origin?: string
    variety?: string
    status?: string
    location_address?: string
    market_name?: string
}

export interface ProductSearchQuery {
    query?: string
    language?: SupportedLanguage
    category?: ProductCategory
    subcategory?: string
    min_price?: number
    max_price?: number
    city?: string
    state?: string
    latitude?: number
    longitude?: number
    radius_km?: number
    quality_grades?: string[]
    available_only?: boolean
    organic_only?: boolean
    sort_by?: string
    sort_order?: string
    limit?: number
    skip?: number
}

export interface ProductSearchResponse {
    products: Product[]
    total_count: number
    page_info: {
        current_page: number
        total_pages: number
        has_next: boolean
        has_previous: boolean
    }
    search_metadata: {
        query: string
        language: string
        search_time_ms: number
        filters_applied: string[]
    }
}

export interface ImageUploadResponse {
    image_id: string
    image_url: string
    thumbnail_url: string
    upload_status: string
    message: string
}

class ProductService {
    private getAuthHeaders(): Record<string, string> {
        const token = localStorage.getItem('accessToken')
        return {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` })
        }
    }

    private getMultipartHeaders(): Record<string, string> {
        const token = localStorage.getItem('accessToken')
        return {
            ...(token && { Authorization: `Bearer ${token}` })
        }
    }

    // Helper to convert category to lowercase for backend
    private categoryToBackend(category: ProductCategory | string): string {
        return category.toLowerCase()
    }

    // Helper to convert category from backend to uppercase for frontend
    private categoryFromBackend(category: string): ProductCategory {
        return category.toUpperCase() as ProductCategory
    }

    async createProduct(productData: ProductCreateRequest): Promise<Product> {
        // Convert category to lowercase for backend
        const backendData = {
            ...productData,
            category: this.categoryToBackend(productData.category)
        }

        const response = await fetch(`${API_BASE_URL}/products/`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(backendData),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to create product')
        }

        const result = await response.json()
        return this.transformBackendProduct(result)
    }

    async getProduct(productId: string, language: SupportedLanguage = 'en'): Promise<Product | null> {
        const response = await fetch(`${API_BASE_URL}/products/${productId}?language=${language}`)

        if (!response.ok) {
            if (response.status === 404) {
                return null
            }
            const error = await response.json()
            throw new Error(error.detail || 'Failed to get product')
        }

        const result = await response.json()
        return this.transformBackendProduct(result)
    }

    async updateProduct(productId: string, updates: ProductUpdateRequest): Promise<Product> {
        const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
            method: 'PUT',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(updates),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to update product')
        }

        const result = await response.json()
        return this.transformBackendProduct(result)
    }

    async deleteProduct(productId: string): Promise<{ message: string }> {
        const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders(),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to delete product')
        }

        return response.json()
    }

    async searchProducts(query: ProductSearchQuery): Promise<ProductSearchResponse> {
        const params = new URLSearchParams()

        // Add query parameters with proper conversion
        Object.entries(query).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                if (Array.isArray(value)) {
                    value.forEach(item => {
                        // Convert quality grades to lowercase
                        if (key === 'quality_grades') {
                            params.append(key, item.toString().toLowerCase())
                        } else {
                            params.append(key, item.toString())
                        }
                    })
                } else {
                    // Convert category to lowercase for backend
                    if (key === 'category') {
                        params.append(key, value.toString().toLowerCase())
                    } else {
                        params.append(key, value.toString())
                    }
                }
            }
        })

        const response = await fetch(`${API_BASE_URL}/products/?${params.toString()}`)

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Search failed')
        }

        const result = await response.json()
        return {
            products: result.products.map((p: any) => this.transformBackendProduct(p)),
            total_count: result.total_count,
            page_info: result.page_info,
            search_metadata: result.search_metadata
        }
    }

    async getVendorProducts(vendorId: string, status?: string, limit: number = 20, skip: number = 0): Promise<Product[]> {
        const params = new URLSearchParams()
        if (status) params.append('status_filter', status)
        params.append('limit', limit.toString())
        params.append('skip', skip.toString())

        const response = await fetch(`${API_BASE_URL}/products/vendor/${vendorId}?${params.toString()}`)

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to get vendor products')
        }

        const result = await response.json()
        return result.map((p: any) => this.transformBackendProduct(p))
    }

    async getMyProducts(status?: string, limit: number = 50, skip: number = 0): Promise<{ products: Product[], total: number }> {
        const params = new URLSearchParams()
        if (status) params.append('status_filter', status)
        params.append('limit', limit.toString())
        params.append('skip', skip.toString())

        const response = await fetch(`${API_BASE_URL}/products/my-products?${params.toString()}`, {
            headers: this.getAuthHeaders(),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to get my products')
        }

        const result = await response.json()
        // Handle both array and object responses and transform to Product type
        if (Array.isArray(result)) {
            return { products: result.map((p: any) => this.transformBackendProduct(p)), total: result.length }
        }
        const products = (result.products || []).map((p: any) => this.transformBackendProduct(p))
        return { products, total: result.total || products.length }
    }

    async updateProductAvailability(productId: string, quantityAvailable: number): Promise<Product> {
        const response = await fetch(`${API_BASE_URL}/products/${productId}/availability`, {
            method: 'PATCH',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({ quantity_available: quantityAvailable }),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to update availability')
        }

        const result = await response.json()
        return this.transformBackendProduct(result)
    }

    async uploadProductImage(
        productId: string,
        file: File,
        altText?: string,
        isPrimary: boolean = false
    ): Promise<ImageUploadResponse> {
        const formData = new FormData()
        formData.append('file', file)
        if (altText) formData.append('alt_text', altText)
        formData.append('is_primary', isPrimary.toString())

        const response = await fetch(`${API_BASE_URL}/products/${productId}/images`, {
            method: 'POST',
            headers: this.getMultipartHeaders(),
            body: formData,
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Image upload failed')
        }

        return response.json()
    }

    async getUploadPresignedUrl(
        productId: string,
        filename: string,
        contentType: string = 'image/jpeg'
    ): Promise<{ upload_url: string; fields: Record<string, string> }> {
        const params = new URLSearchParams({
            filename,
            content_type: contentType
        })

        const response = await fetch(`${API_BASE_URL}/products/upload-url/${productId}?${params.toString()}`, {
            headers: this.getAuthHeaders(),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to get upload URL')
        }

        return response.json()
    }

    async initializeSearchIndex(): Promise<{ status: string; message: string; indexed_count: number }> {
        const response = await fetch(`${API_BASE_URL}/products/search/initialize`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to initialize search index')
        }

        return response.json()
    }

    // Helper method to transform backend product response to frontend Product type
    private transformBackendProduct(backendProduct: any): Product {
        return {
            id: backendProduct.product_id,
            vendorId: backendProduct.vendor_id,
            name: {
                originalLanguage: backendProduct.name.original_language as SupportedLanguage,
                originalText: backendProduct.name.original_text,
                translations: backendProduct.name.translations || {},
                autoTranslated: backendProduct.name.auto_translated || false
            },
            description: {
                originalLanguage: backendProduct.description.original_language as SupportedLanguage,
                originalText: backendProduct.description.original_text,
                translations: backendProduct.description.translations || {},
                autoTranslated: backendProduct.description.auto_translated || false
            },
            category: this.categoryFromBackend(backendProduct.category),
            subcategory: backendProduct.subcategory || '',
            images: backendProduct.images?.map((img: any) => ({
                id: img.image_id,
                url: img.image_url,
                thumbnailUrl: img.thumbnail_url || img.image_url,
                alt: img.alt_text || '',
                isPrimary: img.is_primary || false
            })) || [],
            basePrice: parseFloat(backendProduct.price_info?.base_price || '0'),
            unit: backendProduct.availability?.unit || '',
            quantityAvailable: backendProduct.availability?.quantity_available || 0,
            qualityGrade: backendProduct.quality_grade || '',
            harvestDate: backendProduct.metadata?.harvest_date,
            location: {
                type: 'Point',
                coordinates: backendProduct.location?.coordinates || [0, 0],
                address: backendProduct.location?.address,
                city: backendProduct.location?.city,
                state: backendProduct.location?.state,
                pincode: backendProduct.location?.pincode
            },
            tags: backendProduct.tags || [],
            createdAt: backendProduct.created_at,
            updatedAt: backendProduct.updated_at,
            status: (backendProduct.status || 'ACTIVE').toUpperCase() as any
        }
    }
}

export const productService = new ProductService()