"""
FastAPI application with Clerk authentication integration.

This is a comprehensive example showing how to integrate Clerk authentication
with a FastAPI application for complete user management, session handling,
and role-based access control.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from auth import initialize_clerk, get_clerk_middleware
from routers import auth, users, organizations, protected
from models import ErrorResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting FastAPI application with Clerk integration...")
    
    # Initialize Clerk authentication
    try:
        secret_key = os.getenv("CLERK_SECRET_KEY")
        jwt_key = os.getenv("CLERK_JWT_KEY")  # Optional for local verification
        
        if not secret_key:
            logger.error("CLERK_SECRET_KEY environment variable is required")
            raise ValueError("CLERK_SECRET_KEY environment variable is required")
        
        initialize_clerk(secret_key=secret_key, jwt_key=jwt_key)
        logger.info("Clerk authentication initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Clerk: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")


# Create FastAPI application
app = FastAPI(
    title="FastAPI with Clerk Authentication",
    description="""
    A comprehensive example of integrating Clerk authentication with FastAPI.
    
    This application demonstrates:
    - JWT token verification and session management
    - User management (CRUD operations)
    - Organization management and memberships
    - Role-based access control
    - Permission-based authorization
    - Protected routes with various authentication patterns
    
    ## Authentication
    
    To authenticate, you need to:
    1. Sign up/sign in through your Clerk frontend application
    2. Include the session token in the Authorization header: `Bearer <token>`
    3. The token can be either:
       - Session token from `__session` cookie
       - JWT token from Authorization header
    
    ## Environment Variables Required
    
    - `CLERK_SECRET_KEY`: Your Clerk secret key (required)
    - `CLERK_JWT_KEY`: Your Clerk JWT public key (optional, for local verification)
    
    ## Example Usage
    
    ```bash
    # Set environment variables
    export CLERK_SECRET_KEY="sk_test_..."
    export CLERK_JWT_KEY="-----BEGIN PUBLIC KEY-----..."  # Optional
    
    # Start the application
    uvicorn main:app --reload
    ```
    """,
    version="1.0.0",
    contact={
        "name": "Your API Team",
        "email": "api@yourcompany.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default port
        "http://localhost:8080",  # Vue default port
        "http://localhost:5173",  # Vite default port
        "https://your-domain.com",  # Add your production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path)
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(organizations.router)
app.include_router(protected.router)


# Root endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "FastAPI application with Clerk authentication",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health",
        "authentication": {
            "description": "This API uses Clerk for authentication",
            "header": "Authorization: Bearer <token>",
            "cookie": "__session=<token>",
            "endpoints": {
                "auth_status": "/auth/status",
                "current_user": "/auth/me",
                "protected_example": "/protected/basic"
            }
        },
        "features": [
            "JWT token verification",
            "User management",
            "Organization management",
            "Role-based access control",
            "Permission-based authorization",
            "Session management"
        ]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Verify Clerk middleware is initialized
        get_clerk_middleware()
        
        return {
            "status": "healthy",
            "service": "FastAPI with Clerk Authentication",
            "version": "1.0.0",
            "clerk_initialized": True
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "clerk_initialized": False
            }
        )


@app.get("/openapi-schema", include_in_schema=False)
async def get_openapi_schema():
    """Custom OpenAPI schema with security definitions."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token from Clerk authentication"
        },
        "CookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "__session",
            "description": "Session cookie from Clerk"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"CookieAuth": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with additional configuration."""
    return get_swagger_ui_html(
        openapi_url="/openapi-schema",
        title=f"{app.title} - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
        }
    )


# Example webhooks endpoint (for Clerk webhooks)
@app.post("/webhooks/clerk", tags=["Webhooks"])
async def clerk_webhook(request: Request):
    """
    Handle Clerk webhooks.
    
    This endpoint can be used to handle various Clerk events like:
    - user.created
    - user.updated
    - user.deleted
    - session.created
    - session.ended
    - organization.created
    - organizationMembership.created
    
    Note: In production, you should verify the webhook signature.
    """
    try:
        payload = await request.json()
        event_type = payload.get("type")
        
        logger.info(f"Received Clerk webhook: {event_type}")
        
        # Handle different event types
        if event_type == "user.created":
            user_data = payload.get("data")
            logger.info(f"New user created: {user_data.get('id')}")
            # Add your custom logic here
            
        elif event_type == "user.updated":
            user_data = payload.get("data")
            logger.info(f"User updated: {user_data.get('id')}")
            # Add your custom logic here
            
        elif event_type == "session.created":
            session_data = payload.get("data")
            logger.info(f"New session created: {session_data.get('id')}")
            # Add your custom logic here
            
        elif event_type == "organization.created":
            org_data = payload.get("data")
            logger.info(f"New organization created: {org_data.get('id')}")
            # Add your custom logic here
            
        # Add more event handlers as needed
        
        return {"message": "Webhook processed successfully"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Check for required environment variables
    if not os.getenv("CLERK_SECRET_KEY"):
        print("Error: CLERK_SECRET_KEY environment variable is required")
        print("Get your secret key from https://dashboard.clerk.com")
        exit(1)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )