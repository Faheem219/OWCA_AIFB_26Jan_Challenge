// Core type definitions for the Multilingual Mandi Marketplace

export type SupportedLanguage =
    | 'hi' // Hindi
    | 'en' // English
    | 'ta' // Tamil
    | 'te' // Telugu
    | 'kn' // Kannada
    | 'ml' // Malayalam
    | 'gu' // Gujarati
    | 'pa' // Punjabi
    | 'bn' // Bengali
    | 'mr' // Marathi

export type UserRole = 'VENDOR' | 'BUYER'

export type ProductCategory =
    | 'VEGETABLES'
    | 'FRUITS'
    | 'GRAINS'
    | 'SPICES'
    | 'DAIRY'

export type ProductStatus = 'ACTIVE' | 'SOLD' | 'EXPIRED' | 'DRAFT'

// Measurement units for products (lowercase to match backend enums)
export type MeasurementUnit =
    | 'kg'
    | 'gram'
    | 'quintal'
    | 'ton'
    | 'liter'
    | 'piece'
    | 'dozen'
    | 'bag'
    | 'box'

// Quality grades for products (lowercase to match backend enums)
export type QualityGrade =
    | 'premium'
    | 'grade_a'
    | 'grade_b'
    | 'standard'
    | 'organic'

export type PaymentStatus =
    | 'PENDING'
    | 'PROCESSING'
    | 'COMPLETED'
    | 'FAILED'
    | 'REFUNDED'
    | 'CANCELLED'

export type ConversationStatus = 'ACTIVE' | 'ARCHIVED' | 'BLOCKED'

export type MessageType = 'TEXT' | 'VOICE' | 'OFFER' | 'SYSTEM' | 'IMAGE'

export type OfferStatus = 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED'

// User types
export interface User {
    id: string
    email: string
    phone?: string
    role: UserRole
    preferredLanguages: SupportedLanguage[]
    location: LocationData
    verificationStatus: VerificationStatus
    createdAt: string
    updatedAt: string
}

export interface VendorProfile extends User {
    businessName: string
    businessType: string
    productCategories: ProductCategory[]
    marketLocation: string
    verificationDocuments: DocumentReference[]
    rating: number
    totalTransactions: number
}

export interface BuyerProfile extends User {
    purchaseHistory: string[]
    preferredCategories: ProductCategory[]
    budgetRange?: BudgetRange
    deliveryAddresses: Address[]
}

export interface LocationData {
    type: 'Point'
    coordinates: [number, number] // [longitude, latitude]
    address?: string
    city?: string
    state?: string
    pincode?: string
}

export interface VerificationStatus {
    isEmailVerified: boolean
    isPhoneVerified: boolean
    isBusinessVerified: boolean
    isIdentityVerified: boolean
}

export interface DocumentReference {
    id: string
    type: string
    url: string
    uploadedAt: string
}

export interface BudgetRange {
    min: number
    max: number
    currency: string
}

export interface Address {
    id: string
    type: 'HOME' | 'WORK' | 'OTHER'
    addressLine1: string
    addressLine2?: string
    city: string
    state: string
    pincode: string
    isDefault: boolean
}

// Product types
export interface MultilingualText {
    originalLanguage: SupportedLanguage
    originalText: string
    translations: Partial<Record<SupportedLanguage, string>>
    autoTranslated: boolean
}

export interface Product {
    id: string
    vendorId: string
    name: MultilingualText
    description: MultilingualText
    category: ProductCategory
    subcategory: string
    images: ImageReference[]
    basePrice: number
    unit: string
    quantityAvailable: number
    qualityGrade: string
    harvestDate?: string
    location: LocationData
    tags: string[]
    createdAt: string
    updatedAt: string
    status: ProductStatus
}

export interface ImageReference {
    id: string
    url: string
    thumbnailUrl: string
    alt: string
    isPrimary: boolean
}

// Communication types
export interface Conversation {
    id: string
    participants: ParticipantInfo[]
    productContext?: ProductReference
    createdAt: string
    lastActivity: string
    status: ConversationStatus
}

export interface ParticipantInfo {
    userId: string
    role: UserRole
    name: string
    avatar?: string
    isOnline: boolean
    lastSeen?: string
}

export interface ProductReference {
    id: string
    name: string
    image: string
    price: number
}

export interface Message {
    id: string
    conversationId: string
    senderId: string
    content: MessageContent
    timestamp: string
    messageType: MessageType
    translationData?: TranslationData
    readBy: string[]
}

export interface MessageContent {
    originalText: string
    originalLanguage: SupportedLanguage
    translations: Partial<Record<SupportedLanguage, string>>
    attachments: AttachmentReference[]
}

export interface TranslationData {
    isTranslated: boolean
    confidence: number
    originalLanguage: SupportedLanguage
}

export interface AttachmentReference {
    id: string
    type: 'IMAGE' | 'VOICE' | 'DOCUMENT'
    url: string
    name: string
    size: number
}

export interface Offer {
    id: string
    conversationId: string
    productId: string
    proposerId: string
    amount: number
    quantity: number
    conditions: string
    expiresAt: string
    status: OfferStatus
    createdAt: string
}

// Price discovery types
export interface MarketPrice {
    commodity: string
    market: string
    date: string
    minPrice: number
    maxPrice: number
    modalPrice: number
    arrivals: number
    source: string
}

export interface PricePrediction {
    commodity: string
    predictedPrice: number
    confidenceScore: number
    factors: PriceFactor[]
    predictionDate: string
    modelVersion: string
}

export interface PriceFactor {
    name: string
    impact: number
    description: string
}

export interface PriceSuggestion {
    suggestedPrice: number
    priceRange: PriceRange
    marketComparison: MarketComparison
    reasoning: string
    confidence: number
}

export interface PriceRange {
    min: number
    max: number
}

export interface MarketComparison {
    averagePrice: number
    percentageDifference: number
    competitorCount: number
}

// Transaction types
export interface Transaction {
    id: string
    buyerId: string
    vendorId: string
    productId: string
    quantity: number
    agreedPrice: number
    totalAmount: number
    paymentMethod: string
    paymentStatus: PaymentStatus
    deliveryDetails: DeliveryInfo
    createdAt: string
    completedAt?: string
}

export interface DeliveryInfo {
    address: Address
    estimatedDelivery: string
    trackingNumber?: string
    deliveryStatus: string
}

// API response types
export interface ApiResponse<T> {
    data: T
    message: string
    success: boolean
}

export interface PaginatedResponse<T> {
    data: T[]
    total: number
    page: number
    limit: number
    hasNext: boolean
    hasPrev: boolean
}

export interface ErrorResponse {
    error: string
    message: string
    details?: Record<string, any>
}

// Form types
export interface LoginForm {
    email: string
    password: string
    rememberMe: boolean
}

export interface RegisterForm {
    email: string
    password: string
    confirmPassword: string
    role: UserRole
    preferredLanguages: SupportedLanguage[]
    phone?: string
    businessName?: string
    location: LocationData
}

export interface ProductForm {
    name: string
    description: string
    category: ProductCategory
    subcategory: string
    basePrice: number
    unit: string
    quantityAvailable: number
    qualityGrade: string
    harvestDate?: string
    tags: string[]
    images: File[]
}

// Search and filter types
export interface SearchFilters {
    query?: string
    category?: ProductCategory
    priceRange?: PriceRange
    location?: LocationData
    radius?: number
    qualityGrade?: string
    availability?: boolean
    sortBy?: 'price' | 'distance' | 'rating' | 'date'
    sortOrder?: 'asc' | 'desc'
}

export interface SearchResult {
    products: Product[]
    total: number
    filters: SearchFilters
    suggestions: string[]
}

// WebSocket types
export interface WebSocketMessage {
    type: string
    payload: any
    timestamp: string
}

export interface ChatMessage extends WebSocketMessage {
    type: 'chat_message'
    payload: Message
}

export interface OfferMessage extends WebSocketMessage {
    type: 'offer'
    payload: Offer
}

export interface TypingIndicator extends WebSocketMessage {
    type: 'typing'
    payload: {
        userId: string
        conversationId: string
        isTyping: boolean
    }
}