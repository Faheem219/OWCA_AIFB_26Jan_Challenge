# Multilingual Mandi Marketplace Platform

An AI-powered web application designed to bridge language barriers in Indian local markets (mandis). The platform enables seamless communication, fair pricing, and secure transactions between vendors and buyers who speak different Indian languages.

## Features

- **Multilingual Support**: 10+ Indian languages with real-time translation
- **AI-Powered Price Discovery**: ML-based fair pricing with market data integration
- **Real-Time Communication**: Instant multilingual chat and negotiation
- **Secure Payments**: Multiple payment methods with fraud detection
- **Progressive Web App**: Offline capabilities and mobile-first design
- **Cultural Sensitivity**: Context-aware translations and regional expressions

## Architecture

This is a monorepo containing:
- `frontend/`: React PWA with TypeScript and Vite
- `backend/`: FastAPI with Python 3.11+
- `docker/`: Development environment containers
- `docs/`: Documentation and API specs

## Quick Start

1. **Prerequisites**
   - Node.js 18+
   - Python 3.11+
   - Docker and Docker Compose

2. **Development Setup**
   ```bash
   # Clone and setup
   git clone <repository-url>
   cd multilingual-mandi-marketplace
   
   # Start development environment
   docker-compose up -d
   
   # Install dependencies
   cd frontend && npm install
   cd ../backend && pip install -r requirements.txt
   
   # Start development servers
   npm run dev:all
   ```

3. **Environment Configuration**
   - Copy `.env.example` to `.env` and configure your settings
   - Set up MongoDB Atlas connection
   - Configure AWS credentials for AI services

## Technology Stack

**Frontend:**
- React 18 with TypeScript
- Vite for fast development
- Material-UI for components
- PWA with service workers
- WebSocket for real-time features

**Backend:**
- FastAPI with Python 3.11+
- MongoDB Atlas for data storage
- Redis for caching and sessions
- AWS AI services integration
- JWT authentication

**Infrastructure:**
- Docker for development
- CI/CD with GitHub Actions
- MongoDB Atlas (production)
- AWS services for AI features

## Development

- `npm run dev:frontend` - Start frontend development server
- `npm run dev:backend` - Start backend development server
- `npm run dev:all` - Start both frontend and backend
- `npm run test` - Run all tests
- `npm run build` - Build for production

## Documentation

- [API Documentation](./docs/api.md)
- [Frontend Architecture](./docs/frontend.md)
- [Backend Architecture](./docs/backend.md)
- [Deployment Guide](./docs/deployment.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.