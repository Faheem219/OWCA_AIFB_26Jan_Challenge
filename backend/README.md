# Multilingual Mandi Backend

A FastAPI-based backend for the Multilingual Mandi platform - a real-time linguistic bridge connecting Indian vendors and buyers across language barriers.

## Features

- **FastAPI** with async/await support
- **MongoDB** for flexible document storage
- **Redis** for caching and session management
- **JWT Authentication** with refresh tokens
- **Multi-language support** for 22 official Indian languages
- **CORS** configured for frontend integration
- **Property-based testing** with Hypothesis
- **Docker** support for easy deployment

## Quick Start

### Prerequisites

- Python 3.11+
- MongoDB
- Redis
- Docker (optional)

### Installation

1. **Clone and setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services**:

**Option A: Using Docker Compose (Recommended)**
```bash
cd ..  # Go to project root
docker-compose up -d
```

**Option B: Manual setup**
```bash
# Start MongoDB and Redis locally
# Then run:
python run.py
```

4. **Access the API**:
- API Documentation: http://localhost:8000/api/v1/docs
- Health Check: http://localhost:8000/api/v1/health

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with username/password
- `POST /api/v1/auth/login/email` - Login with email/password
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/me` - Get current user info
- `PUT /api/v1/auth/profile` - Update user profile

### Health
- `GET /api/v1/health` - System health check
- `GET /api/v1/ping` - Simple ping
- `GET /api/v1/version` - API version info

## Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run Property-Based Tests
```bash
pytest tests/test_auth_properties.py -v
```

### Run with Coverage
```bash
pytest --cov=app tests/
```

## Project Structure

```
backend/
├── app/
│   ├── api/                 # API routes
│   │   ├── deps.py         # Dependencies
│   │   └── v1/             # API v1 routes
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration
│   │   └── security.py     # Security utilities
│   ├── db/                 # Database connections
│   │   ├── mongodb.py      # MongoDB setup
│   │   └── redis.py        # Redis setup
│   ├── models/             # Data models
│   │   ├── user.py         # User models
│   │   └── common.py       # Common models
│   ├── services/           # Business logic
│   │   └── auth_service.py # Authentication service
│   └── main.py             # FastAPI application
├── tests/                  # Test files
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
└── run.py                 # Development server
```

## Configuration

Key environment variables:

- `MONGODB_URL` - MongoDB connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key
- `DEBUG` - Enable debug mode
- `CORS_ORIGINS` - Allowed CORS origins

## Supported Languages

The platform supports all 22 official Indian languages:
- Hindi (hi), English (en), Tamil (ta), Telugu (te)
- Bengali (bn), Marathi (mr), Gujarati (gu), Kannada (kn)
- Malayalam (ml), Punjabi (pa), Odia (or), Assamese (as)
- Urdu (ur), Sanskrit (sa), Sindhi (sd), Nepali (ne)
- Kashmiri (ks), Dogri (doi), Manipuri (mni), Konkani (kok)
- Maithili (mai), Bodo (bo)

## Development

### Adding New Features

1. Create models in `app/models/`
2. Implement services in `app/services/`
3. Add API routes in `app/api/v1/`
4. Write tests in `tests/`
5. Update documentation

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

## Deployment

### Docker Deployment
```bash
docker-compose up -d --build
```

### Production Considerations

1. **Security**:
   - Change `SECRET_KEY` in production
   - Use strong database passwords
   - Enable HTTPS
   - Configure proper CORS origins

2. **Performance**:
   - Use MongoDB replica sets
   - Configure Redis persistence
   - Set up load balancing
   - Monitor with logging

3. **Monitoring**:
   - Health check endpoints
   - Application metrics
   - Error tracking
   - Performance monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the test suite
5. Submit a pull request

## License

This project is part of the Multilingual Mandi platform supporting the Viksit Bharat vision.