"""
FastAPI authentication utilities using Clerk SDK.

This module provides middleware, dependencies, and utilities for integrating
Clerk authentication with FastAPI applications.
"""

import os
from typing import Optional, List, Annotated
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from clerk_backend_api import Clerk
from clerk_backend_api.security import authenticate_request, AuthenticateRequestOptions
from clerk_backend_api.security.types import AuthStatus, RequestState


class ClerkAuthMiddleware:
    """Middleware for Clerk authentication."""
    
    def __init__(self, clerk_secret_key: str, jwt_key: Optional[str] = None):
        self.clerk_secret_key = clerk_secret_key
        self.jwt_key = jwt_key
        self.clerk = Clerk(bearer_auth=clerk_secret_key)
    
    def authenticate(self, request: Request) -> RequestState:
        """Authenticate a request using Clerk."""
        options = AuthenticateRequestOptions(
            secret_key=self.clerk_secret_key,
            jwt_key=self.jwt_key,
            authorized_parties=['http://localhost:8000', 'https://localhost:8000']  # Add your domain
        )
        
        return authenticate_request(request, options)


# Global clerk middleware instance
_clerk_middleware: Optional[ClerkAuthMiddleware] = None


def initialize_clerk(
    secret_key: Optional[str] = None, 
    jwt_key: Optional[str] = None
) -> ClerkAuthMiddleware:
    """Initialize Clerk authentication middleware."""
    global _clerk_middleware
    
    if secret_key is None:
        secret_key = os.getenv("CLERK_SECRET_KEY")
    
    if secret_key is None:
        raise ValueError(
            "Clerk secret key is required. Set CLERK_SECRET_KEY environment variable "
            "or pass it to initialize_clerk()"
        )
    
    _clerk_middleware = ClerkAuthMiddleware(secret_key, jwt_key)
    return _clerk_middleware


def get_clerk_middleware() -> ClerkAuthMiddleware:
    """Get the initialized Clerk middleware."""
    if _clerk_middleware is None:
        raise RuntimeError("Clerk middleware not initialized. Call initialize_clerk() first.")
    return _clerk_middleware


# Security scheme for Swagger UI
security = HTTPBearer()


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] = None
) -> RequestState:
    """
    FastAPI dependency to get the current authenticated user.
    
    Raises HTTPException if user is not authenticated.
    """
    middleware = get_clerk_middleware()
    auth_state = middleware.authenticate(request)
    
    if auth_state.status != AuthStatus.SIGNED_IN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_state.message or "Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return auth_state


def get_current_user_optional(request: Request) -> Optional[RequestState]:
    """
    FastAPI dependency to optionally get the current authenticated user.
    
    Returns None if user is not authenticated instead of raising an exception.
    """
    try:
        middleware = get_clerk_middleware()
        auth_state = middleware.authenticate(request)
        
        if auth_state.status == AuthStatus.SIGNED_IN:
            return auth_state
        return None
    except Exception:
        return None


def require_permissions(required_permissions: List[str]):
    """
    Dependency factory for requiring specific permissions.
    
    Args:
        required_permissions: List of required permissions
        
    Returns:
        A FastAPI dependency that checks permissions
    """
    def check_permissions(
        auth_state: Annotated[RequestState, Depends(get_current_user)]
    ) -> RequestState:
        if not auth_state.payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_permissions = auth_state.payload.get("org_permissions", [])
        
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
        
        return auth_state
    
    return check_permissions


def require_role(required_role: str):
    """
    Dependency factory for requiring a specific organization role.
    
    Args:
        required_role: Required organization role
        
    Returns:
        A FastAPI dependency that checks the role
    """
    def check_role(
        auth_state: Annotated[RequestState, Depends(get_current_user)]
    ) -> RequestState:
        if not auth_state.payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_role = auth_state.payload.get("org_role")
        
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required, but user has '{user_role}'"
            )
        
        return auth_state
    
    return check_role


def get_user_id(auth_state: Annotated[RequestState, Depends(get_current_user)]) -> str:
    """Extract user ID from authentication state."""
    if not auth_state.payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user_id = auth_state.payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )
    
    return user_id


def get_organization_id(auth_state: Annotated[RequestState, Depends(get_current_user)]) -> Optional[str]:
    """Extract organization ID from authentication state."""
    if not auth_state.payload:
        return None
    
    return auth_state.payload.get("org_id")


def get_session_id(auth_state: Annotated[RequestState, Depends(get_current_user)]) -> Optional[str]:
    """Extract session ID from authentication state."""
    if not auth_state.payload:
        return None
    
    return auth_state.payload.get("sid")


class ClerkUser:
    """Utility class for user information from Clerk token."""
    
    def __init__(self, auth_state: RequestState):
        self.auth_state = auth_state
        self.payload = auth_state.payload or {}
    
    @property
    def user_id(self) -> str:
        """Get user ID."""
        user_id = self.payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token: missing user ID")
        return user_id
    
    @property
    def session_id(self) -> Optional[str]:
        """Get session ID."""
        return self.payload.get("sid")
    
    @property
    def organization_id(self) -> Optional[str]:
        """Get organization ID."""
        return self.payload.get("org_id")
    
    @property
    def organization_role(self) -> Optional[str]:
        """Get organization role."""
        return self.payload.get("org_role")
    
    @property
    def organization_permissions(self) -> List[str]:
        """Get organization permissions."""
        return self.payload.get("org_permissions", [])
    
    @property
    def email(self) -> Optional[str]:
        """Get user email."""
        return self.payload.get("email")
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.organization_permissions
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return self.organization_role == role


def get_clerk_user(auth_state: Annotated[RequestState, Depends(get_current_user)]) -> ClerkUser:
    """Get a ClerkUser object with convenient methods."""
    return ClerkUser(auth_state)