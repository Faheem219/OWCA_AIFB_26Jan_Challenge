import { User, VendorProfile, BuyerProfile, SupportedLanguage, LocationData, ProductCategory } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export interface UpdateProfileRequest {
    preferred_languages?: SupportedLanguage[]
    location?: LocationData
    phone?: string
    // Vendor-specific fields
    business_name?: string
    business_type?: string
    product_categories?: ProductCategory[]
    market_location?: string
    // Buyer-specific fields
    preferred_categories?: ProductCategory[]
    budget_range?: {
        min: number
        max: number
        currency: string
    }
}

export interface ProfileResponse {
    user: User | VendorProfile | BuyerProfile
}

class ProfileService {
    private getAuthHeaders(): Record<string, string> {
        const token = localStorage.getItem('accessToken')
        return {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` })
        }
    }

    async getProfile(): Promise<User | VendorProfile | BuyerProfile> {
        const response = await fetch(`${API_BASE_URL}/users/profile`, {
            headers: this.getAuthHeaders(),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to get profile')
        }

        const data = await response.json()
        return this.transformProfileResponse(data)
    }

    async updateProfile(updates: UpdateProfileRequest): Promise<User | VendorProfile | BuyerProfile> {
        const response = await fetch(`${API_BASE_URL}/users/profile`, {
            method: 'PUT',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(updates),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to update profile')
        }

        const data = await response.json()
        return this.transformProfileResponse(data)
    }

    async uploadProfileImage(file: File): Promise<{ url: string }> {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch(`${API_BASE_URL}/users/profile/image`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
            },
            body: formData,
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to upload image')
        }

        return response.json()
    }

    async verifyPhone(phoneNumber: string): Promise<{ message: string; verification_id: string }> {
        const response = await fetch(`${API_BASE_URL}/users/verify/phone`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({ phone_number: phoneNumber }),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to send verification code')
        }

        return response.json()
    }

    async confirmPhoneVerification(verificationId: string, code: string): Promise<{ success: boolean; message: string }> {
        const response = await fetch(`${API_BASE_URL}/users/verify/phone/confirm`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
                verification_id: verificationId,
                verification_code: code
            }),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Phone verification failed')
        }

        return response.json()
    }

    async verifyBusiness(documents: File[]): Promise<{ message: string; verification_id: string }> {
        const formData = new FormData()
        documents.forEach((file, index) => {
            formData.append(`document_${index}`, file)
        })

        const response = await fetch(`${API_BASE_URL}/users/verify/business`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
            },
            body: formData,
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to submit business verification')
        }

        return response.json()
    }

    private transformProfileResponse(data: any): User | VendorProfile | BuyerProfile {
        const baseUser: User = {
            id: data.user_id || data.id,
            email: data.email,
            role: data.role,
            preferredLanguages: data.preferred_languages || ['en'],
            location: data.location || {
                type: 'Point',
                coordinates: [0, 0]
            },
            verificationStatus: {
                isEmailVerified: data.verification_status?.includes('email') || false,
                isPhoneVerified: data.verification_status?.includes('phone') || false,
                isBusinessVerified: data.verification_status?.includes('business') || false,
                isIdentityVerified: data.verification_status?.includes('identity') || false,
            },
            createdAt: data.created_at,
            updatedAt: data.updated_at,
        }

        if (data.role === 'VENDOR') {
            return {
                ...baseUser,
                businessName: data.business_name || '',
                businessType: data.business_type || '',
                productCategories: data.product_categories || [],
                marketLocation: data.market_location || '',
                verificationDocuments: data.verification_documents || [],
                rating: data.rating || 0,
                totalTransactions: data.total_transactions || 0,
            } as VendorProfile
        } else {
            return {
                ...baseUser,
                purchaseHistory: data.purchase_history || [],
                preferredCategories: data.preferred_categories || [],
                budgetRange: data.budget_range,
                deliveryAddresses: data.delivery_addresses || [],
            } as BuyerProfile
        }
    }
}

export const profileService = new ProfileService()