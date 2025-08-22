"""
User management routes for FastAPI Clerk integration.

This module provides endpoints for user CRUD operations and management.
"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    get_current_user, 
    get_clerk_middleware,
    ClerkUser,
    get_clerk_user,
    require_permissions,
    get_user_id
)
from models import (
    UserCreate, 
    UserUpdate, 
    UserResponse,
    UserMetadataUpdate,
    SuccessResponse,
    PaginatedResponse,
    BulkUserOperation
)
from clerk_backend_api.security.types import RequestState


router = APIRouter(prefix="/users", tags=["User Management"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:create"]))]
) -> UserResponse:
    """
    Create a new user.
    
    Requires 'org:user_management:create' permission.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Create user using Clerk SDK
        created_user = middleware.clerk.users.create(
            email_address=user_data.email_address,
            phone_number=user_data.phone_number,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=user_data.password,
            public_metadata=user_data.public_metadata,
            private_metadata=user_data.private_metadata,
            unsafe_metadata=user_data.unsafe_metadata
        )
        
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        return UserResponse(
            id=created_user.id,
            email_addresses=created_user.email_addresses or [],
            phone_numbers=created_user.phone_numbers or [],
            username=created_user.username,
            first_name=created_user.first_name,
            last_name=created_user.last_name,
            profile_image_url=created_user.profile_image_url,
            public_metadata=created_user.public_metadata or {},
            private_metadata=created_user.private_metadata or {},
            unsafe_metadata=created_user.unsafe_metadata or {},
            created_at=created_user.created_at,
            updated_at=created_user.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/", response_model=PaginatedResponse)
async def list_users(
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:read"]))],
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    email_address: Optional[List[str]] = Query(default=None),
    phone_number: Optional[List[str]] = Query(default=None),
    username: Optional[List[str]] = Query(default=None),
    query: Optional[str] = Query(default=None)
) -> PaginatedResponse:
    """
    List users with optional filtering.
    
    Requires 'org:user_management:read' permission.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Get users using Clerk SDK
        users = middleware.clerk.users.list(
            limit=limit,
            offset=offset,
            email_address=email_address,
            phone_number=phone_number,
            username=username,
            query=query
        )
        
        if not users:
            users = []
        
        # Convert to our response format
        user_data = []
        for user in users:
            user_data.append({
                "id": user.id,
                "email_addresses": user.email_addresses or [],
                "phone_numbers": user.phone_numbers or [],
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_image_url": user.profile_image_url,
                "public_metadata": user.public_metadata or {},
                "created_at": user.created_at,
                "updated_at": user.updated_at
            })
        
        return PaginatedResponse(
            data=user_data,
            page=offset // limit + 1,
            per_page=limit,
            total_count=len(user_data),
            has_next=len(user_data) == limit,
            has_prev=offset > 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_details(
    user_id: Annotated[str, Depends(get_user_id)]
) -> UserResponse:
    """
    Get the current user's detailed information.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Get user details using Clerk SDK
        user = middleware.clerk.users.get(user_id=user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            email_addresses=user.email_addresses or [],
            phone_numbers=user.phone_numbers or [],
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_image_url=user.profile_image_url,
            public_metadata=user.public_metadata or {},
            private_metadata=user.private_metadata or {},
            unsafe_metadata=user.unsafe_metadata or {},
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:read"]))]
) -> UserResponse:
    """
    Get a specific user by ID.
    
    Requires 'org:user_management:read' permission.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Get user using Clerk SDK
        user = middleware.clerk.users.get(user_id=user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            email_addresses=user.email_addresses or [],
            phone_numbers=user.phone_numbers or [],
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_image_url=user.profile_image_url,
            public_metadata=user.public_metadata or {},
            private_metadata=user.private_metadata or {},
            unsafe_metadata=user.unsafe_metadata or {},
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    user_id: Annotated[str, Depends(get_user_id)]
) -> UserResponse:
    """
    Update the current user's information.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Update user using Clerk SDK
        updated_user = middleware.clerk.users.update(
            user_id=user_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username,
            public_metadata=user_data.public_metadata,
            private_metadata=user_data.private_metadata,
            unsafe_metadata=user_data.unsafe_metadata
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        return UserResponse(
            id=updated_user.id,
            email_addresses=updated_user.email_addresses or [],
            phone_numbers=updated_user.phone_numbers or [],
            username=updated_user.username,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            profile_image_url=updated_user.profile_image_url,
            public_metadata=updated_user.public_metadata or {},
            private_metadata=updated_user.private_metadata or {},
            unsafe_metadata=updated_user.unsafe_metadata or {},
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:update"]))]
) -> UserResponse:
    """
    Update a specific user's information.
    
    Requires 'org:user_management:update' permission.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Update user using Clerk SDK
        updated_user = middleware.clerk.users.update(
            user_id=user_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username,
            public_metadata=user_data.public_metadata,
            private_metadata=user_data.private_metadata,
            unsafe_metadata=user_data.unsafe_metadata
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        return UserResponse(
            id=updated_user.id,
            email_addresses=updated_user.email_addresses or [],
            phone_numbers=updated_user.phone_numbers or [],
            username=updated_user.username,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            profile_image_url=updated_user.profile_image_url,
            public_metadata=updated_user.public_metadata or {},
            private_metadata=updated_user.private_metadata or {},
            unsafe_metadata=updated_user.unsafe_metadata or {},
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:delete"]))]
) -> SuccessResponse:
    """
    Delete a user.
    
    Requires 'org:user_management:delete' permission.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Delete user using Clerk SDK
        middleware.clerk.users.delete(user_id=user_id)
        
        return SuccessResponse(message=f"User {user_id} deleted successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.patch("/{user_id}/metadata", response_model=UserResponse)
async def update_user_metadata(
    user_id: str,
    metadata: UserMetadataUpdate,
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:update"]))]
) -> UserResponse:
    """
    Update user metadata.
    
    Requires 'org:user_management:update' permission.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Update user metadata using Clerk SDK
        updated_user = middleware.clerk.users.update_metadata(
            user_id=user_id,
            public_metadata=metadata.public_metadata,
            private_metadata=metadata.private_metadata,
            unsafe_metadata=metadata.unsafe_metadata
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user metadata"
            )
        
        return UserResponse(
            id=updated_user.id,
            email_addresses=updated_user.email_addresses or [],
            phone_numbers=updated_user.phone_numbers or [],
            username=updated_user.username,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            profile_image_url=updated_user.profile_image_url,
            public_metadata=updated_user.public_metadata or {},
            private_metadata=updated_user.private_metadata or {},
            unsafe_metadata=updated_user.unsafe_metadata or {},
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user metadata: {str(e)}"
        )


@router.post("/{user_id}/ban")
async def ban_user(
    user_id: str,
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:ban"]))]
) -> SuccessResponse:
    """
    Ban a user.
    
    Requires 'org:user_management:ban' permission.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Ban user using Clerk SDK
        middleware.clerk.users.ban(user_id=user_id)
        
        return SuccessResponse(message=f"User {user_id} banned successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ban user: {str(e)}"
        )


@router.post("/{user_id}/unban")
async def unban_user(
    user_id: str,
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:ban"]))]
) -> SuccessResponse:
    """
    Unban a user.
    
    Requires 'org:user_management:ban' permission.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Unban user using Clerk SDK
        middleware.clerk.users.unban(user_id=user_id)
        
        return SuccessResponse(message=f"User {user_id} unbanned successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unban user: {str(e)}"
        )


@router.post("/bulk-operations")
async def bulk_user_operations(
    operation: BulkUserOperation,
    current_user: Annotated[RequestState, Depends(require_permissions(["org:user_management:bulk"]))]
) -> SuccessResponse:
    """
    Perform bulk operations on users.
    
    Requires 'org:user_management:bulk' permission.
    """
    try:
        middleware = get_clerk_middleware()
        
        if operation.operation == "ban":
            # Bulk ban users
            middleware.clerk.users.bulk_ban(user_ids=operation.user_ids)
            message = f"Banned {len(operation.user_ids)} users successfully"
            
        elif operation.operation == "unban":
            # Bulk unban users
            middleware.clerk.users.bulk_unban(user_ids=operation.user_ids)
            message = f"Unbanned {len(operation.user_ids)} users successfully"
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported operation: {operation.operation}"
            )
        
        return SuccessResponse(message=message)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk operation: {str(e)}"
        )