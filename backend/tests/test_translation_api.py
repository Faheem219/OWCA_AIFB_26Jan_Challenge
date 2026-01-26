"""
Integration tests for translation API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.models.translation import LanguageCode


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    # In a real test, you would create a valid JWT token
    return {"Authorization": "Bearer mock_token"}


class TestTranslationAPI:
    """Test translation API endpoints."""
    
    @patch('app.api.deps.get_current_user')
    @patch('app.api.deps.get_translation_service')
    @patch('app.api.deps.get_database')
    @patch('app.api.deps.get_redis')
    def test_get_supported_languages(self, mock_get_redis, mock_get_db, mock_get_service, mock_get_user, client):
        """Test getting supported languages endpoint."""
        # Mock dependencies
        mock_get_db.return_value = MagicMock()
        mock_get_redis.return_value = MagicMock()
        
        # Mock user
        mock_user = AsyncMock()
        mock_get_user.return_value = mock_user
        
        # Mock translation service
        mock_service = AsyncMock()
        mock_service.get_supported_languages.return_value = {
            "languages": [
                {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
                {"code": "en", "name": "English", "native_name": "English"}
            ],
            "total_count": 2
        }
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/translation/languages")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["languages"]) == 2
    
    @patch('app.api.deps.get_current_user')
    @patch('app.api.deps.get_translation_service')
    @patch('app.api.deps.get_database')
    @patch('app.api.deps.get_redis')
    def test_translate_text_same_language(self, mock_get_redis, mock_get_db, mock_get_service, mock_get_user, client, auth_headers):
        """Test text translation with same source and target language."""
        # Mock dependencies
        mock_get_db.return_value = MagicMock()
        mock_get_redis.return_value = MagicMock()
        
        # Mock user
        mock_user = AsyncMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        # Mock translation service
        mock_service = AsyncMock()
        mock_service.translate_text.return_value = {
            "original_text": "Hello",
            "translated_text": "Hello",
            "source_language": "en",
            "target_language": "en",
            "confidence_score": 1.0,
            "provider": "no_translation_needed",
            "cached": False,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        mock_get_service.return_value = mock_service
        
        request_data = {
            "text": "Hello",
            "source_language": "en",
            "target_language": "en"
        }
        
        response = client.post(
            "/api/v1/translation/translate",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_text"] == "Hello"
        assert data["translated_text"] == "Hello"
        assert data["provider"] == "no_translation_needed"
    
    @patch('app.api.deps.get_translation_service')
    @patch('app.api.deps.get_database')
    @patch('app.api.deps.get_redis')
    def test_translation_health_check(self, mock_get_redis, mock_get_db, mock_get_service, client):
        """Test translation service health check."""
        # Mock dependencies
        mock_get_db.return_value = MagicMock()
        mock_get_redis.return_value = MagicMock()
        
        mock_service = AsyncMock()
        mock_service.aws_translate = None
        mock_service.http_client = AsyncMock()
        mock_service.redis = AsyncMock()
        mock_service.db = AsyncMock()
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/translation/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "aws_translate_configured" in data
        assert "gemini_api_configured" in data
        assert "cache_available" in data
        assert "database_available" in data
    
    def test_invalid_translation_request(self, client, auth_headers):
        """Test translation with invalid request data."""
        request_data = {
            "text": "",  # Empty text should fail validation
            "source_language": "en",
            "target_language": "hi"
        }
        
        response = client.post(
            "/api/v1/translation/translate",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_unauthorized_access(self, client):
        """Test accessing translation endpoints without authentication."""
        request_data = {
            "text": "Hello",
            "source_language": "en",
            "target_language": "hi"
        }
        
        response = client.post(
            "/api/v1/translation/translate",
            json=request_data
        )
        
        assert response.status_code == 403  # Forbidden without auth