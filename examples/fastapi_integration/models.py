"""
Pydantic models for FastAPI Clerk integration.

This module defines the data models used in the FastAPI application.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """User roles in the organization."""
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"


class UserCreate(BaseModel):
    """Model for creating a new user."""
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    public_metadata: Optional[Dict[str, Any]] = None
    private_metadata: Optional[Dict[str, Any]] = None
    unsafe_metadata: Optional[Dict[str, Any]] = None


class UserUpdate(BaseModel):
    """Model for updating user information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    public_metadata: Optional[Dict[str, Any]] = None
    private_metadata: Optional[Dict[str, Any]] = None
    unsafe_metadata: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """Model for user response data."""
    id: str
    email_addresses: List[Dict[str, Any]] = []
    phone_numbers: List[Dict[str, Any]] = []
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    public_metadata: Dict[str, Any] = {}
    private_metadata: Dict[str, Any] = {}
    unsafe_metadata: Dict[str, Any] = {}
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class SessionResponse(BaseModel):
    """Model for session response data."""
    id: str
    user_id: str
    status: str
    last_active_at: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class OrganizationCreate(BaseModel):
    """Model for creating an organization."""
    name: str
    slug: Optional[str] = None
    created_by: Optional[str] = None
    public_metadata: Optional[Dict[str, Any]] = None
    private_metadata: Optional[Dict[str, Any]] = None
    max_allowed_memberships: Optional[int] = None


class OrganizationUpdate(BaseModel):
    """Model for updating organization information."""
    name: Optional[str] = None
    slug: Optional[str] = None
    public_metadata: Optional[Dict[str, Any]] = None
    private_metadata: Optional[Dict[str, Any]] = None
    max_allowed_memberships: Optional[int] = None


class OrganizationResponse(BaseModel):
    """Model for organization response data."""
    id: str
    name: str
    slug: Optional[str] = None
    members_count: Optional[int] = None
    public_metadata: Dict[str, Any] = {}
    private_metadata: Dict[str, Any] = {}
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class OrganizationMembershipCreate(BaseModel):
    """Model for creating organization membership."""
    user_id: str
    role: UserRole = UserRole.MEMBER


class OrganizationMembershipUpdate(BaseModel):
    """Model for updating organization membership."""
    role: UserRole


class OrganizationMembershipResponse(BaseModel):
    """Model for organization membership response."""
    id: str
    organization_id: str
    user_id: str
    role: str
    permissions: List[str] = []
    public_metadata: Dict[str, Any] = {}
    private_metadata: Dict[str, Any] = {}
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class AuthenticatedUser(BaseModel):
    """Model for authenticated user information."""
    user_id: str
    session_id: Optional[str] = None
    organization_id: Optional[str] = None
    organization_role: Optional[str] = None
    organization_permissions: List[str] = []
    email: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            # Add custom encoders if needed
        }


class ErrorResponse(BaseModel):
    """Model for error responses."""
    detail: str
    error_code: Optional[str] = None
    timestamp: Optional[str] = None


class SuccessResponse(BaseModel):
    """Model for success responses."""
    message: str
    data: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """Model for paginated responses."""
    data: List[Dict[str, Any]]
    total_count: Optional[int] = None
    page: int = 1
    per_page: int = 10
    has_next: bool = False
    has_prev: bool = False


class SignInTokenCreate(BaseModel):
    """Model for creating sign-in tokens."""
    user_id: str
    expires_in_seconds: Optional[int] = Field(default=2592000, description="Token expiry in seconds (default: 30 days)")


class SignInTokenResponse(BaseModel):
    """Model for sign-in token response."""
    token: str
    url: str
    expires_at: Optional[int] = None


class InvitationCreate(BaseModel):
    """Model for creating invitations."""
    email_address: EmailStr
    public_metadata: Optional[Dict[str, Any]] = None
    redirect_url: Optional[str] = None
    notify: bool = True
    ignore_existing: bool = False


class InvitationResponse(BaseModel):
    """Model for invitation response."""
    id: str
    email_address: str
    status: str
    url: str
    public_metadata: Dict[str, Any] = {}
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class WebhookEvent(BaseModel):
    """Model for Clerk webhook events."""
    data: Dict[str, Any]
    object: str
    type: str


class PermissionCheck(BaseModel):
    """Model for checking permissions."""
    permissions: List[str]
    require_all: bool = True  # If True, user must have ALL permissions; if False, user must have ANY permission


class RoleCheck(BaseModel):
    """Model for checking roles."""
    roles: List[str]
    organization_id: Optional[str] = None


class SessionTokenCreate(BaseModel):
    """Model for creating session tokens."""
    session_id: str
    template_name: Optional[str] = None


class SessionTokenResponse(BaseModel):
    """Model for session token response."""
    jwt: str
    object: str = "token"


class UserMetadataUpdate(BaseModel):
    """Model for updating user metadata."""
    public_metadata: Optional[Dict[str, Any]] = None
    private_metadata: Optional[Dict[str, Any]] = None
    unsafe_metadata: Optional[Dict[str, Any]] = None


class OrganizationInvitationCreate(BaseModel):
    """Model for creating organization invitations."""
    email_address: EmailStr
    inviter_user_id: str
    role: UserRole = UserRole.MEMBER
    public_metadata: Optional[Dict[str, Any]] = None
    private_metadata: Optional[Dict[str, Any]] = None
    redirect_url: Optional[str] = None


class BulkUserOperation(BaseModel):
    """Model for bulk user operations."""
    user_ids: List[str]
    operation: str  # "ban", "unban", "delete", etc.
    reason: Optional[str] = None