"""
Basic tests for the FastAPI Clerk integration.

These tests validate the basic functionality without requiring actual Clerk credentials.
"""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import our app
from main import app
from auth import initialize_clerk


class TestFastAPIClerkIntegration:
    """Test cases for FastAPI Clerk integration."""
    
    def setup_method(self):
        """Set up test environment."""
        # Mock environment variables
        self.mock_secret_key = "sk_test_mock_secret_key"
        os.environ["CLERK_SECRET_KEY"] = self.mock_secret_key
        
        # Initialize test client
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Clean up after tests."""
        # Clean up environment variables
        if "CLERK_SECRET_KEY" in os.environ:
            del os.environ["CLERK_SECRET_KEY"]
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "FastAPI application with Clerk authentication" in data["message"]
    
    def test_health_endpoint_without_clerk(self):
        """Test health endpoint when Clerk is not initialized."""
        response = self.client.get("/health")
        # Should still work but indicate Clerk is not initialized
        assert response.status_code in [200, 503]
    
    @patch('auth.ClerkAuthMiddleware')
    def test_health_endpoint_with_clerk(self, mock_middleware):
        """Test health endpoint when Clerk is properly initialized."""
        # Mock successful Clerk initialization
        mock_middleware.return_value = MagicMock()
        
        with patch('auth._clerk_middleware', mock_middleware.return_value):
            response = self.client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_auth_status_endpoint(self):
        """Test auth status endpoint (should work without authentication)."""
        response = self.client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "authenticated" in data
        assert data["authenticated"] is False
    
    def test_protected_endpoint_without_auth(self):
        """Test that protected endpoints require authentication."""
        response = self.client.get("/protected/basic")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_invalid_token(self):
        """Test protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get("/protected/basic", headers=headers)
        assert response.status_code == 401
    
    @pytest.mark.parametrize("endpoint", [
        "/users/",
        "/organizations/",
        "/protected/admin-only",
        "/protected/user-management"
    ])
    def test_protected_endpoints_require_auth(self, endpoint):
        """Test that various protected endpoints require authentication."""
        response = self.client.get(endpoint)
        assert response.status_code == 401
    
    def test_openapi_schema(self):
        """Test that OpenAPI schema is accessible."""
        response = self.client.get("/openapi-schema")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "components" in schema
        assert "securitySchemes" in schema["components"]
    
    def test_docs_endpoint(self):
        """Test that documentation endpoint is accessible."""
        response = self.client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @patch('clerk_backend_api.Clerk')
    def test_webhook_endpoint(self, mock_clerk):
        """Test Clerk webhook endpoint."""
        webhook_data = {
            "type": "user.created",
            "data": {
                "id": "user_test123",
                "email": "test@example.com"
            }
        }
        
        response = self.client.post("/webhooks/clerk", json=webhook_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_invalid_webhook_data(self):
        """Test webhook endpoint with invalid data."""
        response = self.client.post("/webhooks/clerk", json={"invalid": "data"})
        assert response.status_code == 200  # Should handle gracefully
    
    @patch('auth.initialize_clerk')
    def test_clerk_initialization(self, mock_init):
        """Test Clerk initialization."""
        mock_middleware = MagicMock()
        mock_init.return_value = mock_middleware
        
        # Test initialization with secret key
        result = initialize_clerk(secret_key="test_key")
        mock_init.assert_called_once_with(secret_key="test_key")
    
    def test_missing_secret_key_error(self):
        """Test that missing secret key raises appropriate error."""
        # Remove the secret key from environment
        if "CLERK_SECRET_KEY" in os.environ:
            del os.environ["CLERK_SECRET_KEY"]
        
        with pytest.raises(ValueError, match="Clerk secret key is required"):
            initialize_clerk()


class TestAuthenticationHelpers:
    """Test authentication helper functions."""
    
    @patch('auth._clerk_middleware')
    def test_get_clerk_middleware_success(self, mock_middleware):
        """Test getting clerk middleware when initialized."""
        from auth import get_clerk_middleware
        
        mock_middleware_instance = MagicMock()
        mock_middleware = mock_middleware_instance
        
        with patch('auth._clerk_middleware', mock_middleware_instance):
            result = get_clerk_middleware()
            assert result == mock_middleware_instance
    
    def test_get_clerk_middleware_not_initialized(self):
        """Test getting clerk middleware when not initialized."""
        from auth import get_clerk_middleware
        
        with patch('auth._clerk_middleware', None):
            with pytest.raises(RuntimeError, match="Clerk middleware not initialized"):
                get_clerk_middleware()


class TestModels:
    """Test Pydantic models."""
    
    def test_user_create_model(self):
        """Test UserCreate model validation."""
        from models import UserCreate
        
        # Valid data
        user_data = {
            "email_address": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        user = UserCreate(**user_data)
        assert user.email_address == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
    
    def test_user_create_model_optional_fields(self):
        """Test UserCreate model with optional fields."""
        from models import UserCreate
        
        # Minimal data
        user = UserCreate()
        assert user.email_address is None
        assert user.first_name is None
    
    def test_organization_create_model(self):
        """Test OrganizationCreate model."""
        from models import OrganizationCreate
        
        org_data = {"name": "Test Organization"}
        org = OrganizationCreate(**org_data)
        assert org.name == "Test Organization"
        assert org.slug is None
    
    def test_error_response_model(self):
        """Test ErrorResponse model."""
        from models import ErrorResponse
        
        error = ErrorResponse(detail="Test error", error_code="TEST_ERROR")
        assert error.detail == "Test error"
        assert error.error_code == "TEST_ERROR"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])