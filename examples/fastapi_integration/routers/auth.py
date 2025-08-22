"""
Authentication routes for FastAPI Clerk integration.

This module provides endpoints for authentication-related operations.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    get_current_user, 
    get_current_user_optional, 
    get_clerk_middleware,
    ClerkUser,
    get_clerk_user
)
from models import (
    AuthenticatedUser, 
    SignInTokenCreate, 
    SignInTokenResponse,
    SessionTokenCreate,
    SessionTokenResponse,
    SuccessResponse,
    ErrorResponse
)
from clerk_backend_api.security.types import RequestState


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=AuthenticatedUser)
async def get_current_user_info(
    user: Annotated[ClerkUser, Depends(get_clerk_user)]
) -> AuthenticatedUser:
    """
    Get information about the currently authenticated user.
    
    Returns user information extracted from the JWT token.
    """
    return AuthenticatedUser(
        user_id=user.user_id,
        session_id=user.session_id,
        organization_id=user.organization_id,
        organization_role=user.organization_role,
        organization_permissions=user.organization_permissions,
        email=user.email
    )


@router.get("/status")
async def get_auth_status(
    auth_state: Optional[RequestState] = Depends(get_current_user_optional)
) -> dict:
    """
    Check authentication status without requiring authentication.
    
    Returns whether the user is authenticated and basic info if they are.
    """
    if auth_state and auth_state.payload:
        return {
            "authenticated": True,
            "user_id": auth_state.payload.get("sub"),
            "session_id": auth_state.payload.get("sid"),
            "organization_id": auth_state.payload.get("org_id")
        }
    
    return {"authenticated": False}


@router.post("/sign-in-token", response_model=SignInTokenResponse)
async def create_sign_in_token(
    token_data: SignInTokenCreate,
    current_user: Annotated[RequestState, Depends(get_current_user)]
) -> SignInTokenResponse:
    """
    Create a sign-in token for a user.
    
    This endpoint requires authentication and allows creating sign-in tokens
    for other users (useful for admin operations).
    """
    try:
        middleware = get_clerk_middleware()
        
        # Create sign-in token using Clerk SDK
        response = middleware.clerk.sign_in_tokens.create(
            user_id=token_data.user_id,
            expires_in_seconds=token_data.expires_in_seconds
        )
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create sign-in token"
            )
        
        return SignInTokenResponse(
            token=response.token,
            url=response.url,
            expires_at=getattr(response, 'expires_at', None)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sign-in token: {str(e)}"
        )


@router.post("/session-token", response_model=SessionTokenResponse)
async def create_session_token(
    token_data: SessionTokenCreate,
    current_user: Annotated[RequestState, Depends(get_current_user)]
) -> SessionTokenResponse:
    """
    Create a session token from a session.
    
    This can be used to create custom JWTs for specific use cases.
    """
    try:
        middleware = get_clerk_middleware()
        
        if token_data.template_name:
            # Create token from template
            response = middleware.clerk.sessions.create_token_from_template(
                session_id=token_data.session_id,
                template_name=token_data.template_name
            )
        else:
            # Create standard session token
            response = middleware.clerk.sessions.create_token(
                session_id=token_data.session_id
            )
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session token"
            )
        
        return SessionTokenResponse(
            jwt=response.jwt,
            object=response.object
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session token: {str(e)}"
        )


@router.post("/revoke-session")
async def revoke_session(
    current_user: Annotated[RequestState, Depends(get_current_user)]
) -> SuccessResponse:
    """
    Revoke the current user's session.
    
    This will invalidate the current session token.
    """
    try:
        middleware = get_clerk_middleware()
        session_id = current_user.payload.get("sid")
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active session found"
            )
        
        # Revoke the session
        middleware.clerk.sessions.revoke(session_id=session_id)
        
        return SuccessResponse(message="Session revoked successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke session: {str(e)}"
        )


@router.get("/sessions")
async def list_user_sessions(
    user_id: Optional[str] = None,
    current_user: Annotated[RequestState, Depends(get_current_user)] = None
) -> dict:
    """
    List sessions for a user.
    
    If no user_id is provided, lists sessions for the current user.
    """
    try:
        middleware = get_clerk_middleware()
        
        if not user_id:
            user_id = current_user.payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        # List sessions for the user
        sessions = middleware.clerk.sessions.list(user_id=user_id)
        
        return {
            "sessions": sessions or [],
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/permissions")
async def get_user_permissions(
    user: Annotated[ClerkUser, Depends(get_clerk_user)]
) -> dict:
    """
    Get the current user's permissions and role information.
    """
    return {
        "user_id": user.user_id,
        "organization_id": user.organization_id,
        "organization_role": user.organization_role,
        "permissions": user.organization_permissions,
        "has_organization": user.organization_id is not None
    }


@router.post("/check-permission")
async def check_permission(
    permission: str,
    user: Annotated[ClerkUser, Depends(get_clerk_user)]
) -> dict:
    """
    Check if the current user has a specific permission.
    """
    has_permission = user.has_permission(permission)
    
    return {
        "permission": permission,
        "has_permission": has_permission,
        "user_permissions": user.organization_permissions
    }


@router.post("/logout")
async def logout(
    current_user: Annotated[RequestState, Depends(get_current_user)]
) -> JSONResponse:
    """
    Logout the current user by revoking their session.
    
    Note: This only revokes the server-side session. The client should
    also clear any stored tokens.
    """
    try:
        middleware = get_clerk_middleware()
        session_id = current_user.payload.get("sid")
        
        if session_id:
            middleware.clerk.sessions.revoke(session_id=session_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Logged out successfully"}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Logout failed: {str(e)}"}
        )