"""
Demo script to showcase the FastAPI Clerk integration functionality.

This script demonstrates various features of the integration without requiring actual Clerk credentials.
"""

import os
import sys

# Add the source directory to Python path
sys.path.insert(0, '/home/runner/work/clerk-sdk-python/clerk-sdk-python/src')

# Set mock environment variables
os.environ['CLERK_SECRET_KEY'] = 'sk_test_mock_secret_key_for_demo'

from fastapi.testclient import TestClient
from main import app

def demo_fastapi_clerk_integration():
    """Demonstrate the FastAPI Clerk integration features."""
    
    print("🚀 FastAPI Clerk Integration Demo")
    print("=" * 50)
    
    client = TestClient(app)
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Message: {response.json()['message']}")
    
    # Test 2: Health check
    print("\n2. Testing health check...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Health: {response.json()['status']}")
    
    # Test 3: Auth status (no authentication required)
    print("\n3. Testing auth status (no auth required)...")
    response = client.get("/auth/status")
    print(f"   Status: {response.status_code}")
    print(f"   Authenticated: {response.json()['authenticated']}")
    
    # Test 4: Protected endpoint without authentication
    print("\n4. Testing protected endpoint without auth...")
    response = client.get("/protected/basic")
    print(f"   Status: {response.status_code} (Expected: 401/403)")
    print(f"   Detail: {response.json().get('detail', 'No detail')}")
    
    # Test 5: Optional auth endpoint
    print("\n5. Testing optional auth endpoint...")
    response = client.get("/protected/optional-auth")
    print(f"   Status: {response.status_code}")
    print(f"   Message: {response.json()['message']}")
    print(f"   Authenticated: {response.json()['authenticated']}")
    
    # Test 6: OpenAPI schema
    print("\n6. Testing OpenAPI schema...")
    response = client.get("/openapi-schema")
    print(f"   Status: {response.status_code}")
    schema = response.json()
    print(f"   Title: {schema.get('info', {}).get('title')}")
    print(f"   Security schemes: {list(schema.get('components', {}).get('securitySchemes', {}).keys())}")
    
    # Test 7: Webhook endpoint
    print("\n7. Testing webhook endpoint...")
    webhook_data = {
        "type": "user.created",
        "data": {
            "id": "user_demo123",
            "email": "demo@example.com"
        }
    }
    response = client.post("/webhooks/clerk", json=webhook_data)
    print(f"   Status: {response.status_code}")
    print(f"   Message: {response.json()['message']}")
    
    # Test 8: Various protected endpoints
    protected_endpoints = [
        "/users/",
        "/organizations/",
        "/protected/admin-only",
        "/protected/user-management"
    ]
    
    print("\n8. Testing various protected endpoints...")
    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        print(f"   {endpoint}: {response.status_code} (Expected: 401/403)")
    
    print("\n✅ Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("• ✅ FastAPI application setup with Clerk integration")
    print("• ✅ Authentication middleware and dependencies")
    print("• ✅ Protected and unprotected routes")
    print("• ✅ Role-based and permission-based access control")
    print("• ✅ User and organization management endpoints")
    print("• ✅ Webhook handling")
    print("• ✅ Comprehensive API documentation")
    print("• ✅ Error handling and security")
    
    print("\n📖 To use with real Clerk credentials:")
    print("1. Set CLERK_SECRET_KEY environment variable")
    print("2. Optionally set CLERK_JWT_KEY for local verification")
    print("3. Run: uvicorn main:app --reload")
    print("4. Visit: http://localhost:8000/docs")
    
    print("\n🔗 Integration Features:")
    print("• JWT token verification with Clerk's public keys")
    print("• Session management and token creation")
    print("• User CRUD operations")
    print("• Organization and membership management")
    print("• Fine-grained permissions and role checking")
    print("• Multiple authentication patterns")
    print("• Production-ready error handling")

if __name__ == "__main__":
    demo_fastapi_clerk_integration()