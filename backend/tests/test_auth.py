"""
Authentication system tests.
"""
import pytest
from httpx import AsyncClient
from app.core.security import verify_password, get_password_hash


class TestAuthentication:
    """Test authentication functionality."""
    
    async def test_user_registration(self, client: AsyncClient, test_user_data):
        """Test user registration."""
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "User registered successfully"
        assert "data" in data
        assert data["data"]["email"] == test_user_data["email"]
        assert data["data"]["user_type"] == test_user_data["user_type"]
    
    async def test_duplicate_user_registration(self, client: AsyncClient, test_user_data):
        """Test duplicate user registration fails."""
        # Register user first time
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200
        
        # Try to register same user again
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400
    
    async def test_user_login(self, client: AsyncClient, test_user_data):
        """Test user login."""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    async def test_login_with_wrong_password(self, client: AsyncClient, test_user_data):
        """Test login with wrong password fails."""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try login with wrong password
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
    
    async def test_login_with_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password"
        }
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
    
    async def test_get_current_user(self, client: AsyncClient, authenticated_user_token):
        """Test getting current user information."""
        headers = {"Authorization": f"Bearer {authenticated_user_token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "email" in data["data"]
        assert "user_type" in data["data"]
    
    async def test_get_current_user_without_token(self, client: AsyncClient):
        """Test getting current user without token fails."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # No authorization header
    
    async def test_get_current_user_with_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    async def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify wrong password
        assert verify_password("wrongpassword", hashed) is False
    
    async def test_email_login(self, client: AsyncClient, test_user_data):
        """Test login with email endpoint."""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with email
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/api/v1/auth/login/email", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
    
    async def test_profile_update(self, client: AsyncClient, authenticated_user_token):
        """Test profile update."""
        headers = {"Authorization": f"Bearer {authenticated_user_token}"}
        
        update_data = {
            "full_name": "Updated Test User",
            "preferred_language": "hi"
        }
        
        response = await client.put("/api/v1/auth/profile", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["full_name"] == "Updated Test User"
        assert data["data"]["preferred_language"] == "hi"