# Design Document: Multilingual Mandi Marketplace Platform

## Overview

The Multilingual Mandi Marketplace Platform is a comprehensive web application built using the FARM stack (FastAPI, React, MongoDB) with integrated AI services from AWS. The platform addresses language barriers in Indian local markets by providing real-time translation, AI-driven price discovery, and secure multilingual communication tools.

The system architecture follows a microservices approach with clear separation between the frontend Progressive Web App (PWA), backend API services, AI translation layer, and external market data integrations. The platform is designed to handle high concurrency with sub-second translation latency while maintaining cultural sensitivity and regional context.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        PWA[React PWA]
        SW[Service Worker]
        Cache[Local Cache]
    end
    
    subgraph "API Gateway"
        Gateway[FastAPI Gateway]
        Auth[Authentication Service]
        Rate[Rate Limiter]
    end
    
    subgraph "Core Services"
        User[User Service]
        Product[Product Service]
        Chat[Chat Service]
        Payment[Payment Service]
        Price[Price Discovery Service]
    end
    
    subgraph "AI Services Layer"
        Translate[Translation Engine]
        ML[Price ML Models]
        Moderation[Content Moderation]
    end
    
    subgraph "External Services"
        AWS[AWS AI Services]
        Agmark[Agmarknet API]
        UPI[Payment Gateways]
    end
    
    subgraph "Data Layer"
        MongoDB[(MongoDB Atlas)]
        Redis[(Redis Cache)]
    end
    
    PWA --> Gateway
    SW --> Cache
    Gateway --> Core Services
    Core Services --> AI Services Layer
    AI Services Layer --> External Services
    Core Services --> Data Layer
    
    classDef frontend fill:#e1f5fe
    classDef backend fill:#f3e5f5
    classDef ai fill:#fff3e0
    classDef external fill:#e8f5e8
    classDef data fill:#fce4ec
    
    class PWA,SW,Cache frontend
    class Gateway,Auth,Rate,User,Product,Chat,Payment,Price backend
    class Translate,ML,Moderation ai
    class AWS,Agmark,UPI external
    class MongoDB,Redis data
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript for type safety and modern development
- Vite for fast development and optimized builds
- PWA capabilities with service workers for offline functionality
- Material-UI with custom theming for consistent, accessible design
- React Query for efficient data fetching and caching
- WebSocket client for real-time chat functionality

**Backend:**
- FastAPI with Python 3.11+ for high-performance async API development
- Pydantic for data validation and serialization
- WebSocket support for real-time features
- JWT-based authentication with role-based access control
- Background task processing with Celery for heavy operations

**Database:**
- MongoDB Atlas as primary document database for flexible schema
- Redis for session management, caching, and real-time data
- Elasticsearch for advanced search capabilities across multilingual content

**AI and External Services:**
- AWS Amazon Translate for real-time multilingual translation
- AWS SageMaker for custom price prediction models
- AWS Bedrock for generative AI features
- Agmarknet API integration for real-time commodity prices
- Payment gateway integrations (UPI, Razorpay, Stripe)

## Components and Interfaces

### Frontend Components

**Core Application Shell:**
```typescript
interface AppShell {
  navigationBar: NavigationComponent;
  languageSelector: LanguageSelectorComponent;
  userProfile: UserProfileComponent;
  notificationCenter: NotificationComponent;
}

interface NavigationComponent {
  routes: Route[];
  currentLanguage: SupportedLanguage;
  userRole: UserRole;
  onLanguageChange: (language: SupportedLanguage) => void;
}
```

**User Management Components:**
```typescript
interface UserProfileComponent {
  profile: UserProfile;
  preferences: UserPreferences;
  verificationStatus: VerificationStatus;
  onProfileUpdate: (updates: Partial<UserProfile>) => Promise<void>;
}

interface AuthenticationComponent {
  loginMethods: AuthMethod[];
  registrationFlow: RegistrationStep[];
  onAuthenticate: (credentials: AuthCredentials) => Promise<AuthResult>;
}
```

**Marketplace Components:**
```typescript
interface ProductListingComponent {
  products: Product[];
  filters: FilterOptions;
  searchQuery: string;
  onSearch: (query: string, language: SupportedLanguage) => Promise<Product[]>;
  onFilter: (filters: FilterOptions) => void;
}

interface ProductDetailComponent {
  product: Product;
  priceAnalysis: PriceAnalysis;
  vendorInfo: VendorProfile;
  onNegotiate: () => void;
  onAddToCart: () => void;
}
```

**Communication Components:**
```typescript
interface ChatComponent {
  conversation: Message[];
  participants: ChatParticipant[];
  translationEnabled: boolean;
  onSendMessage: (content: string, language: SupportedLanguage) => Promise<void>;
  onToggleTranslation: () => void;
}

interface NegotiationComponent {
  currentOffer: Offer;
  priceHistory: PricePoint[];
  aiSuggestions: AISuggestion[];
  onMakeOffer: (amount: number) => Promise<void>;
  onAcceptOffer: (offerId: string) => Promise<void>;
}
```

### Backend Service Interfaces

**User Service:**
```python
class UserService:
    async def create_user(self, user_data: UserCreateRequest) -> UserResponse
    async def authenticate_user(self, credentials: AuthCredentials) -> AuthResult
    async def update_profile(self, user_id: str, updates: UserUpdateRequest) -> UserResponse
    async def get_user_preferences(self, user_id: str) -> UserPreferences
    async def verify_user(self, user_id: str, verification_data: VerificationData) -> VerificationResult
```

**Product Service:**
```python
class ProductService:
    async def create_listing(self, vendor_id: str, product_data: ProductCreateRequest) -> ProductResponse
    async def search_products(self, query: SearchQuery) -> List[ProductResponse]
    async def get_product_details(self, product_id: str, language: SupportedLanguage) -> ProductDetailResponse
    async def update_availability(self, product_id: str, availability: AvailabilityUpdate) -> bool
    async def get_vendor_products(self, vendor_id: str) -> List[ProductResponse]
```

**Translation Service:**
```python
class TranslationService:
    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> TranslationResult
    async def translate_bulk(self, texts: List[str], source_lang: str, target_lang: str) -> List[TranslationResult]
    async def detect_language(self, text: str) -> LanguageDetectionResult
    async def translate_with_context(self, text: str, context: TranslationContext) -> TranslationResult
```

**Price Discovery Service:**
```python
class PriceDiscoveryService:
    async def get_market_price(self, commodity: str, location: str) -> MarketPriceResponse
    async def predict_price_trend(self, commodity: str, timeframe: int) -> PriceTrendPrediction
    async def suggest_fair_price(self, product_id: str, context: PriceContext) -> PriceSuggestion
    async def get_price_history(self, commodity: str, days: int) -> List[PricePoint]
```

**Chat Service:**
```python
class ChatService:
    async def create_conversation(self, participants: List[str]) -> ConversationResponse
    async def send_message(self, conversation_id: str, message: MessageRequest) -> MessageResponse
    async def get_conversation_history(self, conversation_id: str, limit: int) -> List[MessageResponse]
    async def translate_message(self, message_id: str, target_language: str) -> TranslationResult
```

## Data Models

### User Models

```python
class UserProfile(BaseModel):
    user_id: str
    email: EmailStr
    phone: Optional[str]
    role: UserRole  # VENDOR, BUYER
    preferred_languages: List[SupportedLanguage]
    location: LocationData
    verification_status: VerificationStatus
    created_at: datetime
    updated_at: datetime

class VendorProfile(UserProfile):
    business_name: str
    business_type: BusinessType
    product_categories: List[ProductCategory]
    market_location: str
    verification_documents: List[DocumentReference]
    rating: float
    total_transactions: int

class BuyerProfile(UserProfile):
    purchase_history: List[TransactionReference]
    preferred_categories: List[ProductCategory]
    budget_range: Optional[BudgetRange]
    delivery_addresses: List[Address]
```

### Product Models

```python
class Product(BaseModel):
    product_id: str
    vendor_id: str
    name: MultilingualText
    description: MultilingualText
    category: ProductCategory
    subcategory: str
    images: List[ImageReference]
    base_price: Decimal
    unit: MeasurementUnit
    quantity_available: int
    quality_grade: QualityGrade
    harvest_date: Optional[date]
    location: LocationData
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    status: ProductStatus  # ACTIVE, SOLD, EXPIRED

class MultilingualText(BaseModel):
    original_language: SupportedLanguage
    original_text: str
    translations: Dict[SupportedLanguage, str]
    auto_translated: bool
```

### Communication Models

```python
class Conversation(BaseModel):
    conversation_id: str
    participants: List[ParticipantInfo]
    product_context: Optional[ProductReference]
    created_at: datetime
    last_activity: datetime
    status: ConversationStatus

class Message(BaseModel):
    message_id: str
    conversation_id: str
    sender_id: str
    content: MessageContent
    timestamp: datetime
    message_type: MessageType  # TEXT, VOICE, OFFER, SYSTEM
    translation_data: Optional[TranslationData]

class MessageContent(BaseModel):
    original_text: str
    original_language: SupportedLanguage
    translations: Dict[SupportedLanguage, str]
    attachments: List[AttachmentReference]

class Offer(BaseModel):
    offer_id: str
    conversation_id: str
    product_id: str
    proposer_id: str
    amount: Decimal
    quantity: int
    conditions: str
    expires_at: datetime
    status: OfferStatus  # PENDING, ACCEPTED, REJECTED, EXPIRED
```

### Price Discovery Models

```python
class MarketPrice(BaseModel):
    commodity: str
    market: str
    date: date
    min_price: Decimal
    max_price: Decimal
    modal_price: Decimal
    arrivals: int
    source: DataSource

class PricePrediction(BaseModel):
    commodity: str
    predicted_price: Decimal
    confidence_score: float
    factors: List[PriceFactor]
    prediction_date: date
    model_version: str

class PriceSuggestion(BaseModel):
    suggested_price: Decimal
    price_range: PriceRange
    market_comparison: MarketComparison
    reasoning: str
    confidence: float
```

### Transaction Models

```python
class Transaction(BaseModel):
    transaction_id: str
    buyer_id: str
    vendor_id: str
    product_id: str
    quantity: int
    agreed_price: Decimal
    total_amount: Decimal
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    delivery_details: DeliveryInfo
    created_at: datetime
    completed_at: Optional[datetime]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the prework analysis, I need to analyze the acceptance criteria for testability:

### Property 1: Role-Based Access Control
*For any* user account with a specified role (vendor or buyer), the system should provide access only to functionality appropriate for that role and restrict access to inappropriate functionality.
**Validates: Requirements 1.2**

### Property 2: Profile Validation Completeness
*For any* user profile creation or update (vendor or buyer), all required fields for that role should be validated, and the operation should fail if any required field is missing or invalid.
**Validates: Requirements 1.3, 1.4, 1.6**

### Property 3: Authentication Flow Correctness
*For any* valid user credentials and role, successful authentication should redirect the user to the appropriate role-specific dashboard.
**Validates: Requirements 1.5**

### Property 4: Multilingual Translation Consistency
*For any* text content in a supported language, the translation engine should produce consistent translations that preserve meaning and context across all supported target languages.
**Validates: Requirements 2.2, 2.3, 3.2, 3.4, 5.2**

### Property 5: Translation Fallback Reliability
*For any* translation request that fails or encounters an error, the system should gracefully fallback to English with clear indication of the fallback.
**Validates: Requirements 2.5**

### Property 6: Product Listing Validation
*For any* product upload attempt, all required fields (images, descriptions, quantities, base prices, category) should be validated, and the upload should fail if any required field is missing.
**Validates: Requirements 3.1**

### Property 7: Multilingual Search Completeness
*For any* search query in a supported language, the system should return relevant results regardless of the original language of the product listings, and results should be displayed in the user's preferred language.
**Validates: Requirements 3.3, 3.4**

### Property 8: Search Filter Accuracy
*For any* combination of applied filters (price range, location, quality, availability), all returned results should match the specified filter criteria.
**Validates: Requirements 3.5, 3.6**

### Property 9: Price Discovery Data Integration
*For any* price suggestion request, the system should integrate real-time data from external sources (Agmarknet, commodity APIs) and consider all specified factors (historical data, supply-demand, weather, seasonal trends).
**Validates: Requirements 4.1, 4.2**

### Property 10: Price Suggestion Completeness
*For any* price suggestion generated, the response should include confidence scores, explanations, and when requested, interactive charts with historical and forecast data.
**Validates: Requirements 4.3, 4.4, 4.5**

### Property 11: Communication Security
*For any* chat communication or payment processing, the system should apply end-to-end encryption to protect sensitive data.
**Validates: Requirements 5.1, 6.4, 8.3**

### Property 12: Real-Time Translation Accuracy
*For any* message sent in a chat conversation, the system should instantly translate it for recipients while preserving context, idioms, and cultural appropriateness.
**Validates: Requirements 5.2, 5.3**

### Property 13: AI-Powered Negotiation Support
*For any* price negotiation context, the system should provide AI-powered counteroffers and suggestions based on current market data.
**Validates: Requirements 5.5**

### Property 14: Transaction Management Completeness
*For any* completed transaction, the system should generate digital invoices in the user's preferred language and provide AI-summarized information for complex transactions.
**Validates: Requirements 6.2, 6.3**

### Property 15: Fraud Detection Responsiveness
*For any* suspicious activity pattern, the AI-powered fraud detection system should trigger appropriate prevention measures.
**Validates: Requirements 6.5**

### Property 16: Performance Requirements
*For any* translation request or API call, the system should respond within 1 second to maintain optimal user experience.
**Validates: Requirements 7.1, 10.5**

### Property 17: Offline Functionality
*For any* poor connectivity scenario, the system should provide offline capabilities through service workers and local caching.
**Validates: Requirements 7.2**

### Property 18: Accessibility Compliance
*For any* user with accessibility needs, the system should provide functional voice navigation, screen reader compatibility, and high contrast modes.
**Validates: Requirements 7.3**

### Property 19: Data Residency Compliance
*For any* user data storage operation, all data should reside within Indian data centers and comply with local data protection regulations.
**Validates: Requirements 8.1, 8.2**

### Property 20: Data Rights Fulfillment
*For any* user request for data access or deletion, the system should provide mechanisms to fulfill these requests within regulatory timeframes.
**Validates: Requirements 8.4**

### Property 21: Audit Trail Completeness
*For any* transaction or data access operation, the system should maintain comprehensive logs for audit purposes.
**Validates: Requirements 8.5**

### Property 22: AI Content Moderation
*For any* community content posted, the AI moderation system should detect inappropriate content while respecting cultural contexts and providing culturally sensitive resolution suggestions.
**Validates: Requirements 9.1, 9.3**

### Property 23: AI-Powered Analytics Generation
*For any* vendor performance analysis or sustainability information request, the system should generate AI-powered insights and recommendations.
**Validates: Requirements 9.4, 9.5**

### Property 24: External Service Integration
*For any* requirement for external data or AI services, the system should successfully integrate with AWS services (Translate, SageMaker, Lex, Bedrock) and maintain reliable connections.
**Validates: Requirements 10.1, 10.4**

### Property 25: Infrastructure Scalability
*For any* increased user load, the system should automatically scale infrastructure resources to maintain performance without manual intervention.
**Validates: Requirements 10.2, 10.3**

## Error Handling

### Translation Service Error Handling
- **Network Failures**: Implement retry logic with exponential backoff for AWS Translate API calls
- **Language Detection Failures**: Fallback to user's preferred language or English when language detection fails
- **Translation Quality Issues**: Provide confidence scores and allow users to report translation problems
- **Rate Limiting**: Implement request queuing and caching to handle AWS API rate limits

### Price Discovery Error Handling
- **External API Failures**: Cache recent price data and use historical averages when Agmarknet API is unavailable
- **ML Model Failures**: Fallback to rule-based pricing when machine learning models are unavailable
- **Data Quality Issues**: Validate and sanitize external price data before processing
- **Prediction Confidence**: Clearly indicate when price predictions have low confidence scores

### Communication System Error Handling
- **WebSocket Disconnections**: Implement automatic reconnection with message queuing for offline periods
- **Message Delivery Failures**: Provide delivery status indicators and retry mechanisms
- **Translation Delays**: Show typing indicators and estimated translation times for longer texts
- **File Upload Failures**: Implement chunked uploads with resume capability for large files

### Payment Processing Error Handling
- **Gateway Failures**: Support multiple payment gateways with automatic failover
- **Transaction Timeouts**: Implement proper timeout handling with clear user feedback
- **Fraud Detection**: Provide clear explanations when transactions are flagged for review
- **Refund Processing**: Automated refund workflows with proper audit trails

### Data Consistency Error Handling
- **Database Failures**: Implement proper transaction rollbacks and data integrity checks
- **Synchronization Issues**: Use eventual consistency patterns with conflict resolution
- **Cache Invalidation**: Implement proper cache invalidation strategies for real-time data
- **Backup and Recovery**: Automated backup systems with point-in-time recovery capabilities

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points between components. Unit tests validate concrete scenarios and error conditions, ensuring individual components work correctly in isolation.

**Property Tests**: Verify universal properties across all inputs through randomized testing. Property tests validate that the system maintains correctness guarantees regardless of input variations, catching edge cases that might be missed by example-based tests.

### Property-Based Testing Configuration

**Testing Framework**: Use Hypothesis for Python backend services and fast-check for TypeScript frontend components to implement property-based testing.

**Test Configuration**: Each property test must run a minimum of 100 iterations to ensure adequate coverage through randomization. Tests should be configured with appropriate generators for multilingual content, user roles, product categories, and price ranges.

**Property Test Tagging**: Each property-based test must include a comment referencing its corresponding design document property:
- Format: **Feature: multilingual-mandi-marketplace, Property {number}: {property_text}**
- Example: **Feature: multilingual-mandi-marketplace, Property 4: Multilingual Translation Consistency**

### Testing Categories

**Authentication and Authorization Testing**:
- Unit tests for specific login scenarios and edge cases
- Property tests for role-based access control across all user types and permissions
- Integration tests for third-party authentication providers (Google, Aadhaar)

**Translation and Multilingual Testing**:
- Unit tests for specific translation examples and cultural expressions
- Property tests for translation consistency across all supported language pairs
- Performance tests for translation latency requirements (sub-1-second response)

**Price Discovery Testing**:
- Unit tests for specific market scenarios and edge cases
- Property tests for price prediction accuracy across different commodities and conditions
- Integration tests for external API reliability (Agmarknet, commodity APIs)

**Communication System Testing**:
- Unit tests for message formatting and delivery scenarios
- Property tests for real-time translation accuracy across all language combinations
- Load tests for concurrent chat sessions and WebSocket connections

**Payment Processing Testing**:
- Unit tests for specific payment scenarios and error conditions
- Property tests for transaction integrity across all payment methods
- Security tests for fraud detection and prevention mechanisms

**Performance and Scalability Testing**:
- Unit tests for specific performance bottlenecks
- Property tests for system behavior under various load conditions
- Stress tests for auto-scaling and resource management

### AI and ML Testing Strategy

**Translation Model Testing**:
- Validate translation quality using BLEU scores and human evaluation
- Test cultural sensitivity and context preservation
- Verify fallback mechanisms for unsupported language pairs

**Price Prediction Model Testing**:
- Validate prediction accuracy against historical data
- Test model performance across different commodities and market conditions
- Verify confidence score calibration and explanation generation

**Content Moderation Testing**:
- Test AI moderation accuracy across different content types and languages
- Validate cultural sensitivity in moderation decisions
- Verify escalation mechanisms for complex moderation cases

### Integration Testing

**External Service Integration**:
- Test AWS service integration reliability and error handling
- Validate Agmarknet API integration and data quality
- Test payment gateway integration across all supported methods

**End-to-End User Flows**:
- Complete user registration and profile setup flows
- Full product listing, search, and purchase workflows
- Multilingual negotiation and transaction completion scenarios

**Cross-Platform Testing**:
- Test PWA functionality across different browsers and devices
- Validate offline capabilities and service worker behavior
- Test responsive design across various screen sizes and orientations