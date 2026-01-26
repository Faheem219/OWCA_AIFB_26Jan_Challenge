import React, { createContext, useContext, useReducer, useEffect } from 'react'
import { User, UserRole, SupportedLanguage, LocationData } from '../types'
import { authService, RegisterRequest, GoogleAuthRequest, AadhaarAuthRequest } from '../services/authService'

interface AuthState {
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean
    error: string | null
}

type AuthAction =
    | { type: 'AUTH_START' }
    | { type: 'AUTH_SUCCESS'; payload: User }
    | { type: 'AUTH_FAILURE'; payload: string }
    | { type: 'LOGOUT' }
    | { type: 'CLEAR_ERROR' }
    | { type: 'UPDATE_USER'; payload: Partial<User> }

export interface RegisterData {
    email: string
    password: string
    confirmPassword: string
    role: UserRole
    preferredLanguages: SupportedLanguage[]
    phone?: string
    businessName?: string
    location: LocationData
}

interface AuthContextType extends AuthState {
    login: (email: string, password: string) => Promise<void>
    register: (userData: RegisterData) => Promise<void>
    loginWithGoogle: (credentials: GoogleAuthRequest) => Promise<void>
    loginWithAadhaar: (credentials: AadhaarAuthRequest) => Promise<void>
    logout: () => Promise<void>
    updateUser: (userData: Partial<User>) => void
    clearError: () => void
    refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export { AuthContext }

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
    switch (action.type) {
        case 'AUTH_START':
            return {
                ...state,
                isLoading: true,
                error: null,
            }
        case 'AUTH_SUCCESS':
            return {
                ...state,
                user: action.payload,
                isAuthenticated: true,
                isLoading: false,
                error: null,
            }
        case 'AUTH_FAILURE':
            return {
                ...state,
                user: null,
                isAuthenticated: false,
                isLoading: false,
                error: action.payload,
            }
        case 'LOGOUT':
            return {
                ...state,
                user: null,
                isAuthenticated: false,
                isLoading: false,
                error: null,
            }
        case 'UPDATE_USER':
            return {
                ...state,
                user: state.user ? { ...state.user, ...action.payload } : null,
            }
        case 'CLEAR_ERROR':
            return {
                ...state,
                error: null,
            }
        default:
            return state
    }
}

const initialState: AuthState = {
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [state, dispatch] = useReducer(authReducer, initialState)

    // Check for existing authentication on app load
    useEffect(() => {
        const checkAuth = async () => {
            try {
                if (authService.isAuthenticated()) {
                    const user = await authService.getCurrentUser()
                    dispatch({ type: 'AUTH_SUCCESS', payload: user })
                } else {
                    dispatch({ type: 'AUTH_FAILURE', payload: 'Not authenticated' })
                }
            } catch (error) {
                console.error('Auth check failed:', error)
                dispatch({ type: 'AUTH_FAILURE', payload: 'Authentication check failed' })
            }
        }

        checkAuth()
    }, [])

    const login = async (email: string, password: string) => {
        dispatch({ type: 'AUTH_START' })

        try {
            const response = await authService.login({ email, password })

            // Store tokens
            authService.storeTokens(response.access_token, response.refresh_token)

            dispatch({ type: 'AUTH_SUCCESS', payload: response.user })
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Login failed'
            dispatch({ type: 'AUTH_FAILURE', payload: errorMessage })
            throw error
        }
    }

    const register = async (userData: RegisterData) => {
        dispatch({ type: 'AUTH_START' })

        try {
            // Validate password confirmation
            if (userData.password !== userData.confirmPassword) {
                throw new Error('Passwords do not match')
            }

            const registerRequest: RegisterRequest = {
                email: userData.email,
                password: userData.password,
                role: userData.role,
                preferred_languages: userData.preferredLanguages,
                phone: userData.phone,
                business_name: userData.businessName,
                location: userData.location
            }

            const response = await authService.register(registerRequest)

            if (response.requires_verification) {
                // Registration successful but requires verification
                dispatch({
                    type: 'AUTH_FAILURE',
                    payload: `Registration successful! Please check your ${response.verification_method} for verification instructions.`
                })
            } else {
                // Registration complete, user can login
                dispatch({
                    type: 'AUTH_FAILURE',
                    payload: 'Registration successful! Please login with your credentials.'
                })
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Registration failed'
            dispatch({ type: 'AUTH_FAILURE', payload: errorMessage })
            throw error
        }
    }

    const loginWithGoogle = async (credentials: GoogleAuthRequest) => {
        dispatch({ type: 'AUTH_START' })

        try {
            const response = await authService.loginWithGoogle(credentials)

            // Store tokens
            authService.storeTokens(response.access_token, response.refresh_token)

            dispatch({ type: 'AUTH_SUCCESS', payload: response.user })
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Google login failed'
            dispatch({ type: 'AUTH_FAILURE', payload: errorMessage })
            throw error
        }
    }

    const loginWithAadhaar = async (credentials: AadhaarAuthRequest) => {
        dispatch({ type: 'AUTH_START' })

        try {
            const response = await authService.loginWithAadhaar(credentials)

            // Store tokens
            authService.storeTokens(response.access_token, response.refresh_token)

            dispatch({ type: 'AUTH_SUCCESS', payload: response.user })
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Aadhaar login failed'
            dispatch({ type: 'AUTH_FAILURE', payload: errorMessage })
            throw error
        }
    }

    const logout = async () => {
        try {
            await authService.logout()
            dispatch({ type: 'LOGOUT' })
        } catch (error) {
            console.error('Logout error:', error)
            // Even if logout fails, clear local state
            dispatch({ type: 'LOGOUT' })
        }
    }

    const refreshToken = async () => {
        try {
            const response = await authService.refreshToken()
            authService.storeTokens(response.access_token, authService.getTokens().refreshToken || '')
        } catch (error) {
            console.error('Token refresh failed:', error)
            dispatch({ type: 'LOGOUT' })
            throw error
        }
    }

    const updateUser = (userData: Partial<User>) => {
        dispatch({ type: 'UPDATE_USER', payload: userData })
    }

    const clearError = () => {
        dispatch({ type: 'CLEAR_ERROR' })
    }

    const value: AuthContextType = {
        ...state,
        login,
        register,
        loginWithGoogle,
        loginWithAadhaar,
        logout,
        updateUser,
        clearError,
        refreshToken,
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}