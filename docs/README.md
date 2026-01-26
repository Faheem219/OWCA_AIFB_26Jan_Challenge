# Multilingual Mandi Marketplace Platform Documentation

This directory contains comprehensive documentation for the Multilingual Mandi Marketplace Platform.

## Documentation Structure

- `api.md` - API documentation and endpoint specifications
- `frontend.md` - Frontend architecture and component documentation
- `backend.md` - Backend architecture and service documentation
- `deployment.md` - Deployment guide and infrastructure setup
- `development.md` - Development setup and contribution guidelines
- `testing.md` - Testing strategies and guidelines
- `i18n.md` - Internationalization and localization guide
- `security.md` - Security considerations and best practices

## Quick Links

- [Getting Started](../README.md#quick-start)
- [API Documentation](./api.md)
- [Development Guide](./development.md)
- [Deployment Guide](./deployment.md)

## Architecture Overview

The platform follows a modern microservices architecture with:

- **Frontend**: React PWA with TypeScript and Material-UI
- **Backend**: FastAPI with Python 3.11+ and async/await
- **Database**: MongoDB Atlas for document storage
- **Cache**: Redis for session management and caching
- **Search**: Elasticsearch for multilingual product search
- **AI Services**: AWS Translate, SageMaker, and Bedrock
- **Real-time**: WebSocket connections for chat and live updates

## Key Features

1. **Multilingual Support**: 10+ Indian languages with real-time translation
2. **AI-Powered Price Discovery**: ML-based fair pricing with market data
3. **Real-Time Communication**: Instant multilingual chat and negotiation
4. **Secure Payments**: Multiple payment methods with fraud detection
5. **Progressive Web App**: Offline capabilities and mobile-first design
6. **Cultural Sensitivity**: Context-aware translations and regional expressions

## Technology Stack

### Frontend
- React 18 with TypeScript
- Vite for fast development and builds
- Material-UI for consistent design
- React Query for data fetching
- i18next for internationalization
- Workbox for PWA functionality

### Backend
- FastAPI with Python 3.11+
- Motor for async MongoDB operations
- Redis for caching and sessions
- Pydantic for data validation
- JWT for authentication
- Celery for background tasks

### Infrastructure
- Docker for containerization
- GitHub Actions for CI/CD
- MongoDB Atlas for production database
- AWS services for AI capabilities
- Nginx for reverse proxy and load balancing

## Contributing

Please read our [Development Guide](./development.md) for information on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.