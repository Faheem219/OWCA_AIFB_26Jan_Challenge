import {
    User,
    SupportedLanguage,
    UserRole
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export interface LoginRequest {
    email: string
    password: string
    rememberMe?: boolean
}

// Backend expects this format
interface BackendLoginRequest {
    method: 'email' | 'phone' | 'google' | 'aadhaar'
    identifier: string
    password?: string
    remember_me?: boolean
}

export interface RegisterRequest {
    method: 'email' | 'phone'
    email: string
    password: string
    role: UserRole
    preferred_language: SupportedLanguage
    phone?: string
    full_name: string
    location_city: string
    location_state: string
    location_pincode: string
    business_name?: string
    business_type?: string
    product_categories?: string[]
    market_location?: string
    accept_terms: boolean
    accept_privacy: boolean
}

export interface AuthResponse {
    access_token: string
    refresh_token: string
    token_type: string
    expires_in: number
    user: User
}

export interface GoogleAuthRequest {
    id_token: string
    role?: UserRole
    preferred_languages?: SupportedLanguage[]
}

export interface AadhaarAuthRequest {
    aadhaar_number: string
    otp: string
    role: UserRole
    preferred_languages: SupportedLanguage[]
}

export interface VerificationRequest {
    user_id: string
    verification_code: string
    verification_type: 'email' | 'phone'
}

export interface PasswordResetRequest {
    email: string
}

export interface PasswordResetConfirmRequest {
    token: string
    new_password: string
}

class AuthService {
    private getAuthHeaders(): Record<string, string> {
        const token = localStorage.getItem('accessToken')
        return {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` })
        }
    }

    async login(credentials: LoginRequest): Promise<AuthResponse> {
        // Transform frontend request to backend format
        const backendRequest: BackendLoginRequest = {
            method: 'email',
            identifier: credentials.email,
            password: credentials.password,
            remember_me: credentials.rememberMe || false
        }

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(backendRequest),
        })

        if (!response.ok) {
            const error = await response.json()
            // Handle FastAPI validation errors (422) which return an array of errors
            if (error.detail && Array.isArray(error.detail)) {
                const messages = error.detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ')
                throw new Error(messages)
            }
            throw new Error(error.detail || 'Login failed')
        }

        const data = await response.json()
        
        // Transform backend user to frontend User type
        const backendUser = data.user
        const verificationStatus = backendUser.verification_status || 'unverified'
        const user: User = {
            id: backendUser.user_id || backendUser.id,
            email: backendUser.email,
            phone: backendUser.phone,
            role: backendUser.role as UserRole,
            preferredLanguages: backendUser.preferred_languages || ['en'],
            location: backendUser.location || { type: 'Point', coordinates: [0, 0] },
            verificationStatus: {
                isEmailVerified: verificationStatus === 'verified',
                isPhoneVerified: verificationStatus === 'verified',
                isBusinessVerified: verificationStatus === 'verified',
                isIdentityVerified: verificationStatus === 'verified',
            },
            createdAt: backendUser.created_at,
            updatedAt: backendUser.updated_at || backendUser.created_at,
        }
        
        return {
            access_token: data.access_token,
            refresh_token: data.refresh_token,
            token_type: data.token_type,
            expires_in: data.expires_in,
            user
        }
    }

    async register(userData: RegisterRequest): Promise<{ user_id: string; message: string; requires_verification: boolean; verification_method?: string }> {
        // Transform role to lowercase for backend
        const backendRequest = {
            ...userData,
            role: userData.role.toLowerCase() as 'vendor' | 'buyer'
        }

        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(backendRequest),
        })

        if (!response.ok) {
            const error = await response.json()
            // Handle FastAPI validation errors (422)
            if (error.detail && Array.isArray(error.detail)) {
                const messages = error.detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ')
                throw new Error(messages)
            }
            throw new Error(error.detail || 'Registration failed')
        }

        return response.json()
    }

    async loginWithGoogle(credentials: GoogleAuthRequest): Promise<AuthResponse> {
        const response = await fetch(`${API_BASE_URL}/auth/oauth/google`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
        })

        if (!response.ok) {
            const error = await response.json()
            if (response.status === 202) {
                // User needs to complete registration
                throw new Error('REGISTRATION_REQUIRED')
            }
            throw new Error(error.detail || 'Google authentication failed')
        }

        return response.json()
    }

    async loginWithAadhaar(credentials: AadhaarAuthRequest): Promise<AuthResponse> {
        const response = await fetch(`${API_BASE_URL}/auth/aadhaar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Aadhaar authentication failed')
        }

        return response.json()
    }

    async verifyUser(verificationData: VerificationRequest): Promise<{ success: boolean; message: string }> {
        const response = await fetch(`${API_BASE_URL}/auth/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(verificationData),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Verification failed')
        }

        return response.json()
    }

    async refreshToken(): Promise<{ access_token: string; token_type: string; expires_in: number }> {
        const refreshToken = localStorage.getItem('refreshToken')
        if (!refreshToken) {
            throw new Error('No refresh token available')
        }

        const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Token refresh failed')
        }

        return response.json()
    }

    async logout(): Promise<void> {
        const token = localStorage.getItem('accessToken')
        if (token) {
            try {
                await fetch(`${API_BASE_URL}/auth/logout`, {
                    method: 'POST',
                    headers: this.getAuthHeaders(),
                })
            } catch (error) {
                console.error('Logout API call failed:', error)
                // Continue with local logout even if API call fails
            }
        }

        // Clear local storage
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
    }

    async getCurrentUser(): Promise<User> {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: this.getAuthHeaders(),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to get user info')
        }

        const userData = await response.json()

        // Transform backend response to frontend User type
        // Backend verification_status is a single string like 'verified', 'unverified', etc.
        const verificationStatus = userData.verification_status || 'unverified'
        return {
            id: userData.user_id,
            email: userData.email,
            phone: userData.phone,
            role: userData.role as UserRole,
            preferredLanguages: userData.preferred_languages || ['en'],
            location: userData.location || {
                type: 'Point',
                coordinates: [0, 0]
            },
            verificationStatus: {
                isEmailVerified: verificationStatus === 'verified',
                isPhoneVerified: verificationStatus === 'verified',
                isBusinessVerified: verificationStatus === 'verified',
                isIdentityVerified: verificationStatus === 'verified',
            },
            createdAt: userData.created_at,
            updatedAt: userData.last_login || userData.created_at,
        }
    }

    async requestPasswordReset(email: string): Promise<{ message: string }> {
        const response = await fetch(`${API_BASE_URL}/auth/password-reset/request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email }),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Password reset request failed')
        }

        return response.json()
    }

    async confirmPasswordReset(data: PasswordResetConfirmRequest): Promise<{ message: string }> {
        const response = await fetch(`${API_BASE_URL}/auth/password-reset/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Password reset failed')
        }

        return response.json()
    }

    // Helper method to check if user is authenticated
    isAuthenticated(): boolean {
        const token = localStorage.getItem('accessToken')
        if (!token) return false

        try {
            // Basic JWT token validation (check if not expired)
            const payload = JSON.parse(atob(token.split('.')[1]))
            const currentTime = Date.now() / 1000
            return payload.exp > currentTime
        } catch {
            return false
        }
    }

    // Helper method to get stored tokens
    getTokens(): { accessToken: string | null; refreshToken: string | null } {
        return {
            accessToken: localStorage.getItem('accessToken'),
            refreshToken: localStorage.getItem('refreshToken')
        }
    }

    // Helper method to store tokens
    storeTokens(accessToken: string, refreshToken: string): void {
        localStorage.setItem('accessToken', accessToken)
        localStorage.setItem('refreshToken', refreshToken)
    }
}

export const authService = new AuthService()