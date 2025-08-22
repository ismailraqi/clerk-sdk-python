"""
Protected routes demonstrating various authentication and authorization patterns.

This module shows different ways to protect routes using Clerk authentication.
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
    ClerkUser,
    get_clerk_user,
    require_permissions,
    require_role,
    get_user_id,
    get_organization_id
)
from models import SuccessResponse
from clerk_backend_api.security.types import RequestState


router = APIRouter(prefix="/protected", tags=["Protected Routes"])


@router.get("/basic")
async def basic_protected_route(
    current_user: Annotated[RequestState, Depends(get_current_user)]
) -> dict:
    """
    Basic protected route that requires authentication.
    
    Returns basic user information from the JWT token.
    """
    return {
        "message": "This is a protected route",
        "user_id": current_user.payload.get("sub"),
        "session_id": current_user.payload.get("sid"),
        "authenticated": True
    }


@router.get("/optional-auth")
async def optional_auth_route(
    auth_state: Optional[RequestState] = Depends(get_current_user_optional)
) -> dict:
    """
    Route with optional authentication.
    
    Returns different content based on whether user is authenticated.
    """
    if auth_state and auth_state.payload:
        return {
            "message": "Welcome back!",
            "user_id": auth_state.payload.get("sub"),
            "authenticated": True
        }
    else:
        return {
            "message": "Welcome, anonymous user!",
            "authenticated": False,
            "suggestion": "Sign in for a personalized experience"
        }


@router.get("/user-info")
async def get_detailed_user_info(
    user: Annotated[ClerkUser, Depends(get_clerk_user)]
) -> dict:
    """
    Get detailed user information using the ClerkUser helper.
    """
    return {
        "user_id": user.user_id,
        "session_id": user.session_id,
        "organization": {
            "id": user.organization_id,
            "role": user.organization_role,
            "permissions": user.organization_permissions
        } if user.organization_id else None,
        "email": user.email,
        "has_organization": user.organization_id is not None
    }


@router.get("/admin-only")
async def admin_only_route(
    current_user: Annotated[RequestState, Depends(require_role("admin"))]
) -> dict:
    """
    Route that requires admin role in the current organization.
    """
    return {
        "message": "Welcome, admin!",
        "user_id": current_user.payload.get("sub"),
        "organization_id": current_user.payload.get("org_id"),
        "role": current_user.payload.get("org_role")
    }


@router.get("/member-or-admin")
async def member_or_admin_route(
    user: Annotated[ClerkUser, Depends(get_clerk_user)]
) -> dict:
    """
    Route that requires member or admin role.
    
    Uses manual role checking for more complex logic.
    """
    if not user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization membership required"
        )
    
    if not user.has_role("admin") and not user.has_role("member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or member role required"
        )
    
    return {
        "message": f"Welcome, {user.organization_role}!",
        "user_id": user.user_id,
        "organization_id": user.organization_id,
        "role": user.organization_role
    }


@router.get("/user-management")
async def user_management_route(
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:read"]))]
) -> dict:
    """
    Route that requires specific user management permissions.
    """
    return {
        "message": "You have user management permissions",
        "user_id": current_user.payload.get("sub"),
        "permissions": current_user.payload.get("org_permissions", [])
    }


@router.get("/multiple-permissions")
async def multiple_permissions_route(
    current_user: Annotated[RequestState, Depends(require_permissions([
        "org:user_management:read",
        "org:user_management:create"
    ]))]
) -> dict:
    """
    Route that requires multiple permissions.
    """
    return {
        "message": "You have both read and create user management permissions",
        "user_id": current_user.payload.get("sub"),
        "permissions": current_user.payload.get("org_permissions", [])
    }


@router.post("/permission-check")
async def check_specific_permission(
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
        "message": f"You {'have' if has_permission else 'do not have'} the '{permission}' permission",
        "all_permissions": user.organization_permissions
    }


@router.get("/organization-context")
async def organization_context_route(
    user_id: Annotated[str, Depends(get_user_id)],
    org_id: Annotated[Optional[str], Depends(get_organization_id)]
) -> dict:
    """
    Route that demonstrates extracting user and organization context.
    """
    if not org_id:
        return {
            "message": "User is not in an organization context",
            "user_id": user_id,
            "organization_id": None
        }
    
    return {
        "message": "User is in an organization context",
        "user_id": user_id,
        "organization_id": org_id
    }


@router.get("/dashboard-data")
async def get_dashboard_data(
    user: Annotated[ClerkUser, Depends(get_clerk_user)]
) -> dict:
    """
    Example dashboard route that returns different data based on user's role and permissions.
    """
    dashboard_data = {
        "user_info": {
            "id": user.user_id,
            "email": user.email
        },
        "navigation": [],
        "widgets": []
    }
    
    # Add basic user widgets
    dashboard_data["widgets"].append({
        "type": "profile",
        "title": "My Profile",
        "data": {"user_id": user.user_id}
    })
    
    # Add organization-specific content
    if user.organization_id:
        dashboard_data["organization"] = {
            "id": user.organization_id,
            "role": user.organization_role,
            "permissions": user.organization_permissions
        }
        
        # Add navigation items based on role
        if user.has_role("admin"):
            dashboard_data["navigation"].extend([
                {"title": "User Management", "url": "/admin/users"},
                {"title": "Organization Settings", "url": "/admin/settings"}
            ])
        
        if user.has_role("member") or user.has_role("admin"):
            dashboard_data["navigation"].append(
                {"title": "Team", "url": "/team"}
            )
        
        # Add widgets based on permissions
        if user.has_permission("org:user_management:read"):
            dashboard_data["widgets"].append({
                "type": "user_stats",
                "title": "User Statistics",
                "data": {"organization_id": user.organization_id}
            })
        
        if user.has_permission("org:analytics:read"):
            dashboard_data["widgets"].append({
                "type": "analytics",
                "title": "Analytics Dashboard",
                "data": {"organization_id": user.organization_id}
            })
    
    return dashboard_data


@router.post("/secure-action")
async def secure_action(
    action_type: str,
    user: Annotated[ClerkUser, Depends(get_clerk_user)]
) -> SuccessResponse:
    """
    Example of a secure action that requires different permissions based on the action type.
    """
    permission_map = {
        "create_user": "org:user_management:create",
        "delete_user": "org:user_management:delete",
        "modify_settings": "org:settings:update",
        "view_analytics": "org:analytics:read"
    }
    
    required_permission = permission_map.get(action_type)
    
    if not required_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action type: {action_type}"
        )
    
    if not user.has_permission(required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{required_permission}' required for action '{action_type}'"
        )
    
    # Perform the secure action (mock implementation)
    return SuccessResponse(
        message=f"Action '{action_type}' completed successfully",
        data={
            "action_type": action_type,
            "user_id": user.user_id,
            "organization_id": user.organization_id,
            "timestamp": "2023-01-01T00:00:00Z"  # In real implementation, use actual timestamp
        }
    )


@router.get("/health-check")
async def protected_health_check(
    current_user: Annotated[RequestState, Depends(get_current_user)]
) -> dict:
    """
    Protected health check endpoint.
    
    Useful for monitoring whether the authentication system is working properly.
    """
    return {
        "status": "healthy",
        "authenticated": True,
        "user_id": current_user.payload.get("sub"),
        "session_valid": True,
        "timestamp": "2023-01-01T00:00:00Z"  # In real implementation, use actual timestamp
    }


@router.get("/debug-token")
async def debug_token_info(
    current_user: Annotated[RequestState, Depends(get_current_user)]
) -> dict:
    """
    Debug endpoint to inspect token contents.
    
    WARNING: This should only be available in development environments.
    """
    return {
        "token_payload": current_user.payload,
        "token_present": current_user.token is not None,
        "auth_status": current_user.status.value
    }