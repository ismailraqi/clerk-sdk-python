"""
Organization management routes for FastAPI Clerk integration.

This module provides endpoints for organization CRUD operations and membership management.
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
    require_role,
    get_user_id,
    get_organization_id
)
from models import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationMembershipCreate,
    OrganizationMembershipUpdate,
    OrganizationMembershipResponse,
    OrganizationInvitationCreate,
    InvitationResponse,
    SuccessResponse,
    PaginatedResponse,
    UserRole
)
from clerk_backend_api.security.types import RequestState


router = APIRouter(prefix="/organizations", tags=["Organization Management"])


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: Annotated[ClerkUser, Depends(get_clerk_user)]
) -> OrganizationResponse:
    """
    Create a new organization.
    
    The current user becomes the creator and admin of the organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Set the creator to current user if not specified
        if not org_data.created_by:
            org_data.created_by = current_user.user_id
        
        # Create organization using Clerk SDK
        created_org = middleware.clerk.organizations.create(
            name=org_data.name,
            slug=org_data.slug,
            created_by=org_data.created_by,
            public_metadata=org_data.public_metadata,
            private_metadata=org_data.private_metadata,
            max_allowed_memberships=org_data.max_allowed_memberships
        )
        
        if not created_org:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization"
            )
        
        return OrganizationResponse(
            id=created_org.id,
            name=created_org.name,
            slug=created_org.slug,
            members_count=created_org.members_count,
            public_metadata=created_org.public_metadata or {},
            private_metadata=created_org.private_metadata or {},
            created_at=created_org.created_at,
            updated_at=created_org.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}"
        )


@router.get("/", response_model=PaginatedResponse)
async def list_organizations(
    current_user: Annotated[RequestState, Depends(get_current_user)],
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_members_count: bool = Query(default=False),
    query: Optional[str] = Query(default=None),
    order_by: Optional[str] = Query(default=None)
) -> PaginatedResponse:
    """
    List organizations accessible to the current user.
    """
    try:
        middleware = get_clerk_middleware()
        
        # List organizations using Clerk SDK
        organizations = middleware.clerk.organizations.list(
            limit=limit,
            offset=offset,
            include_members_count=include_members_count,
            query=query,
            order_by=order_by
        )
        
        if not organizations:
            organizations = []
        
        # Convert to our response format
        org_data = []
        for org in organizations:
            org_data.append({
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "members_count": org.members_count,
                "public_metadata": org.public_metadata or {},
                "created_at": org.created_at,
                "updated_at": org.updated_at
            })
        
        return PaginatedResponse(
            data=org_data,
            page=offset // limit + 1,
            per_page=limit,
            total_count=len(org_data),
            has_next=len(org_data) == limit,
            has_prev=offset > 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list organizations: {str(e)}"
        )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    current_user: Annotated[RequestState, Depends(get_current_user)]
) -> OrganizationResponse:
    """
    Get a specific organization by ID.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Get organization using Clerk SDK
        org = middleware.clerk.organizations.get(organization_id=organization_id)
        
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            members_count=org.members_count,
            public_metadata=org.public_metadata or {},
            private_metadata=org.private_metadata or {},
            created_at=org.created_at,
            updated_at=org.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization: {str(e)}"
        )


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    org_data: OrganizationUpdate,
    current_user: Annotated[RequestState, Depends(require_role("admin"))]
) -> OrganizationResponse:
    """
    Update an organization.
    
    Requires admin role in the organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Update organization using Clerk SDK
        updated_org = middleware.clerk.organizations.update(
            organization_id=organization_id,
            name=org_data.name,
            slug=org_data.slug,
            public_metadata=org_data.public_metadata,
            private_metadata=org_data.private_metadata,
            max_allowed_memberships=org_data.max_allowed_memberships
        )
        
        if not updated_org:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update organization"
            )
        
        return OrganizationResponse(
            id=updated_org.id,
            name=updated_org.name,
            slug=updated_org.slug,
            members_count=updated_org.members_count,
            public_metadata=updated_org.public_metadata or {},
            private_metadata=updated_org.private_metadata or {},
            created_at=updated_org.created_at,
            updated_at=updated_org.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}"
        )


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: str,
    current_user: Annotated[RequestState, Depends(require_role("admin"))]
) -> SuccessResponse:
    """
    Delete an organization.
    
    Requires admin role in the organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Delete organization using Clerk SDK
        middleware.clerk.organizations.delete(organization_id=organization_id)
        
        return SuccessResponse(message=f"Organization {organization_id} deleted successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}"
        )


# Organization Membership endpoints
@router.post("/{organization_id}/memberships", response_model=OrganizationMembershipResponse)
async def create_membership(
    organization_id: str,
    membership_data: OrganizationMembershipCreate,
    current_user: Annotated[RequestState, Depends(require_role("admin"))]
) -> OrganizationMembershipResponse:
    """
    Add a user to an organization.
    
    Requires admin role in the organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Create membership using Clerk SDK
        membership = middleware.clerk.organization_memberships.create(
            organization_id=organization_id,
            user_id=membership_data.user_id,
            role=membership_data.role.value
        )
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create membership"
            )
        
        return OrganizationMembershipResponse(
            id=membership.id,
            organization_id=organization_id,
            user_id=membership_data.user_id,
            role=membership.role,
            permissions=membership.permissions or [],
            public_metadata=membership.public_metadata or {},
            private_metadata=membership.private_metadata or {},
            created_at=membership.created_at,
            updated_at=membership.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create membership: {str(e)}"
        )


@router.get("/{organization_id}/memberships", response_model=PaginatedResponse)
async def list_memberships(
    organization_id: str,
    current_user: Annotated[RequestState, Depends(get_current_user)],
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    order_by: Optional[str] = Query(default=None)
) -> PaginatedResponse:
    """
    List members of an organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # List memberships using Clerk SDK
        memberships = middleware.clerk.organization_memberships.list(
            organization_id=organization_id,
            limit=limit,
            offset=offset,
            order_by=order_by
        )
        
        if not memberships:
            memberships = []
        
        # Convert to our response format
        membership_data = []
        for membership in memberships:
            membership_data.append({
                "id": membership.id,
                "organization_id": organization_id,
                "user_id": membership.public_user_data.user_id if membership.public_user_data else None,
                "role": membership.role,
                "permissions": membership.permissions or [],
                "public_metadata": membership.public_metadata or {},
                "created_at": membership.created_at,
                "updated_at": membership.updated_at,
                "user_info": {
                    "first_name": membership.public_user_data.first_name if membership.public_user_data else None,
                    "last_name": membership.public_user_data.last_name if membership.public_user_data else None,
                    "image_url": membership.public_user_data.image_url if membership.public_user_data else None,
                    "identifier": membership.public_user_data.identifier if membership.public_user_data else None
                }
            })
        
        return PaginatedResponse(
            data=membership_data,
            page=offset // limit + 1,
            per_page=limit,
            total_count=len(membership_data),
            has_next=len(membership_data) == limit,
            has_prev=offset > 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list memberships: {str(e)}"
        )


@router.patch("/{organization_id}/memberships/{user_id}", response_model=OrganizationMembershipResponse)
async def update_membership(
    organization_id: str,
    user_id: str,
    membership_data: OrganizationMembershipUpdate,
    current_user: Annotated[RequestState, Depends(require_role("admin"))]
) -> OrganizationMembershipResponse:
    """
    Update a user's membership in an organization.
    
    Requires admin role in the organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Update membership using Clerk SDK
        membership = middleware.clerk.organization_memberships.update(
            organization_id=organization_id,
            user_id=user_id,
            role=membership_data.role.value
        )
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update membership"
            )
        
        return OrganizationMembershipResponse(
            id=membership.id,
            organization_id=organization_id,
            user_id=user_id,
            role=membership.role,
            permissions=membership.permissions or [],
            public_metadata=membership.public_metadata or {},
            private_metadata=membership.private_metadata or {},
            created_at=membership.created_at,
            updated_at=membership.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update membership: {str(e)}"
        )


@router.delete("/{organization_id}/memberships/{user_id}")
async def remove_membership(
    organization_id: str,
    user_id: str,
    current_user: Annotated[RequestState, Depends(require_role("admin"))]
) -> SuccessResponse:
    """
    Remove a user from an organization.
    
    Requires admin role in the organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Delete membership using Clerk SDK
        middleware.clerk.organization_memberships.delete(
            organization_id=organization_id,
            user_id=user_id
        )
        
        return SuccessResponse(message=f"User {user_id} removed from organization {organization_id}")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove membership: {str(e)}"
        )


# Organization Invitation endpoints
@router.post("/{organization_id}/invitations", response_model=InvitationResponse)
async def create_organization_invitation(
    organization_id: str,
    invitation_data: OrganizationInvitationCreate,
    current_user: Annotated[RequestState, Depends(require_role("admin"))]
) -> InvitationResponse:
    """
    Invite a user to join an organization.
    
    Requires admin role in the organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Create invitation using Clerk SDK
        invitation = middleware.clerk.organization_invitations.create(
            organization_id=organization_id,
            email_address=invitation_data.email_address,
            inviter_user_id=invitation_data.inviter_user_id,
            role=invitation_data.role.value,
            public_metadata=invitation_data.public_metadata,
            private_metadata=invitation_data.private_metadata,
            redirect_url=invitation_data.redirect_url
        )
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create invitation"
            )
        
        return InvitationResponse(
            id=invitation.id,
            email_address=invitation.email_address,
            status=invitation.status,
            url=invitation.url or "",
            public_metadata=invitation.public_metadata or {},
            created_at=invitation.created_at,
            updated_at=invitation.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invitation: {str(e)}"
        )


@router.get("/{organization_id}/invitations", response_model=PaginatedResponse)
async def list_organization_invitations(
    organization_id: str,
    current_user: Annotated[RequestState, Depends(require_role("admin"))],
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None)
) -> PaginatedResponse:
    """
    List pending invitations for an organization.
    
    Requires admin role in the organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # List invitations using Clerk SDK
        invitations = middleware.clerk.organization_invitations.list(
            organization_id=organization_id,
            limit=limit,
            offset=offset,
            status=status
        )
        
        if not invitations:
            invitations = []
        
        # Convert to our response format
        invitation_data = []
        for invitation in invitations:
            invitation_data.append({
                "id": invitation.id,
                "email_address": invitation.email_address,
                "status": invitation.status,
                "role": invitation.role,
                "organization_id": organization_id,
                "public_metadata": invitation.public_metadata or {},
                "created_at": invitation.created_at,
                "updated_at": invitation.updated_at
            })
        
        return PaginatedResponse(
            data=invitation_data,
            page=offset // limit + 1,
            per_page=limit,
            total_count=len(invitation_data),
            has_next=len(invitation_data) == limit,
            has_prev=offset > 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list invitations: {str(e)}"
        )


@router.post("/{organization_id}/invitations/{invitation_id}/revoke")
async def revoke_organization_invitation(
    organization_id: str,
    invitation_id: str,
    current_user: Annotated[RequestState, Depends(require_role("admin"))]
) -> SuccessResponse:
    """
    Revoke an organization invitation.
    
    Requires admin role in the organization.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Revoke invitation using Clerk SDK
        middleware.clerk.organization_invitations.revoke(
            organization_id=organization_id,
            invitation_id=invitation_id,
            requesting_user_id=current_user.payload.get("sub")
        )
        
        return SuccessResponse(message=f"Invitation {invitation_id} revoked successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke invitation: {str(e)}"
        )


@router.get("/my-organizations")
async def get_my_organizations(
    user: Annotated[ClerkUser, Depends(get_clerk_user)]
) -> dict:
    """
    Get organizations that the current user is a member of.
    """
    try:
        middleware = get_clerk_middleware()
        
        # Get user's organization memberships
        memberships = middleware.clerk.users.get_organization_memberships(user_id=user.user_id)
        
        if not memberships:
            memberships = []
        
        # Extract organization info
        organizations = []
        for membership in memberships:
            if hasattr(membership, 'organization'):
                organizations.append({
                    "id": membership.organization.id,
                    "name": membership.organization.name,
                    "slug": membership.organization.slug,
                    "role": membership.role,
                    "permissions": membership.permissions or []
                })
        
        return {
            "organizations": organizations,
            "count": len(organizations)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user organizations: {str(e)}"
        )