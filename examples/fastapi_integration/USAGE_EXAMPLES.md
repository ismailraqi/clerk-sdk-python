# FastAPI + Clerk Authentication Integration - Usage Examples

This document provides practical examples of how to use the FastAPI Clerk integration in real applications.

## Quick Start Example

Here's a minimal example to get you started:

```python
from fastapi import FastAPI, Depends
from auth import initialize_clerk, get_clerk_user, ClerkUser
import os

# Initialize the app and Clerk
app = FastAPI()
initialize_clerk(secret_key=os.getenv("CLERK_SECRET_KEY"))

@app.get("/profile")
async def get_profile(user: ClerkUser = Depends(get_clerk_user)):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "organization": user.organization_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

## Authentication Patterns

### 1. Basic Authentication
```python
from fastapi import Depends
from auth import get_current_user
from clerk_backend_api.security.types import RequestState

@app.get("/protected")
async def protected_route(user: RequestState = Depends(get_current_user)):
    return {"message": "You are authenticated!", "user_id": user.payload["sub"]}
```

### 2. Optional Authentication
```python
from auth import get_current_user_optional

@app.get("/maybe-protected")
async def maybe_protected(user: Optional[RequestState] = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello, {user.payload['sub']}!"}
    return {"message": "Hello, anonymous user!"}
```

### 3. Role-Based Protection
```python
from auth import require_role

@app.get("/admin")
async def admin_only(user: RequestState = Depends(require_role("admin"))):
    return {"message": "Welcome to the admin panel!"}
```

### 4. Permission-Based Protection
```python
from auth import require_permissions

@app.get("/manage-users")
async def manage_users(
    user: RequestState = Depends(require_permissions(["org:user_management:read"]))
):
    return {"message": "You can manage users!"}
```

### 5. Custom Authorization Logic
```python
from auth import get_clerk_user, ClerkUser
from fastapi import HTTPException

@app.get("/custom-logic")
async def custom_logic(user: ClerkUser = Depends(get_clerk_user)):
    # Custom business logic
    if not user.organization_id:
        raise HTTPException(403, "Organization membership required")
    
    if user.has_permission("custom:action") or user.has_role("admin"):
        return {"message": "Action authorized"}
    
    raise HTTPException(403, "Insufficient permissions")
```

## Frontend Integration Examples

### React with Clerk
```javascript
// Frontend React component
import { useAuth } from '@clerk/clerk-react';
import { useState, useEffect } from 'react';

function UserProfile() {
  const { getToken } = useAuth();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    async function fetchProfile() {
      try {
        const token = await getToken();
        const response = await fetch('http://localhost:8000/users/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setProfile(data);
        }
      } catch (error) {
        console.error('Failed to fetch profile:', error);
      }
    }

    fetchProfile();
  }, [getToken]);

  return (
    <div>
      {profile ? (
        <div>
          <h1>Welcome, {profile.first_name}!</h1>
          <p>Email: {profile.email_addresses[0]?.email_address}</p>
          <p>User ID: {profile.id}</p>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}
```

### Next.js API Route
```javascript
// pages/api/protected-data.js
import { auth } from '@clerk/nextjs';

export default async function handler(req, res) {
  const { getToken } = auth();
  
  try {
    const token = await getToken();
    
    const response = await fetch('http://localhost:8000/protected/dashboard-data', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      res.status(200).json(data);
    } else {
      res.status(response.status).json({ error: 'Failed to fetch data' });
    }
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
}
```

### JavaScript/TypeScript Client
```typescript
class APIClient {
  private baseURL: string;
  private getToken: () => Promise<string>;

  constructor(baseURL: string, getToken: () => Promise<string>) {
    this.baseURL = baseURL;
    this.getToken = getToken;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const token = await this.getToken();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getCurrentUser() {
    return this.request('/users/me');
  }

  async createOrganization(name: string) {
    return this.request('/organizations/', {
      method: 'POST',
      body: JSON.stringify({ name })
    });
  }

  async getUserPermissions() {
    return this.request('/auth/permissions');
  }
}

// Usage
const client = new APIClient('http://localhost:8000', () => clerk.session.getToken());
const user = await client.getCurrentUser();
```

## Advanced Use Cases

### 1. Multi-Tenant SaaS Application
```python
from auth import get_clerk_user, ClerkUser

@app.get("/tenant-data")
async def get_tenant_data(
    user: ClerkUser = Depends(get_clerk_user),
    tenant_id: str = Query(...)
):
    # Ensure user has access to this tenant
    if user.organization_id != tenant_id:
        raise HTTPException(403, "Access denied to this tenant")
    
    # Return tenant-specific data
    return {"tenant_id": tenant_id, "data": "..."}

@app.post("/tenant-users")
async def create_tenant_user(
    user_data: UserCreate,
    user: ClerkUser = Depends(get_clerk_user)
):
    # Only allow user creation within user's organization
    if not user.has_permission("org:user_management:create"):
        raise HTTPException(403, "Cannot create users")
    
    # Set the user's organization in metadata
    user_data.public_metadata = {
        **user_data.public_metadata or {},
        "organization_id": user.organization_id
    }
    
    # Create user using Clerk SDK
    return await create_user(user_data)
```

### 2. API Key Management
```python
from auth import require_permissions

@app.post("/api-keys")
async def create_api_key(
    user: RequestState = Depends(require_permissions(["org:api_keys:create"]))
):
    middleware = get_clerk_middleware()
    
    # Create a machine-to-machine token for API access
    response = middleware.clerk.m2m.create_token(
        machine_id=user.payload["sub"],
        scopes=["api:read", "api:write"]
    )
    
    return {"api_key": response.token, "expires_at": response.expires_at}

@app.get("/api-keys")
async def list_api_keys(
    user: RequestState = Depends(require_permissions(["org:api_keys:read"]))
):
    middleware = get_clerk_middleware()
    
    # List all API keys for the organization
    tokens = middleware.clerk.m2m.list_tokens(
        organization_id=user.payload["org_id"]
    )
    
    return {"api_keys": tokens}
```

### 3. Webhook Processing
```python
@app.post("/webhooks/user-created")
async def handle_user_created(webhook: WebhookEvent):
    """Handle new user registration."""
    user_data = webhook.data
    
    # Custom onboarding logic
    await send_welcome_email(user_data["email"])
    await setup_default_permissions(user_data["id"])
    await log_user_registration(user_data)
    
    return {"status": "processed"}

@app.post("/webhooks/organization-membership")
async def handle_org_membership(webhook: WebhookEvent):
    """Handle organization membership changes."""
    membership_data = webhook.data
    
    if webhook.type == "organizationMembership.created":
        await grant_organization_access(
            membership_data["user_id"],
            membership_data["organization_id"],
            membership_data["role"]
        )
    elif webhook.type == "organizationMembership.deleted":
        await revoke_organization_access(
            membership_data["user_id"],
            membership_data["organization_id"]
        )
    
    return {"status": "processed"}
```

### 4. Custom Middleware
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from subdomain or header
        tenant_id = self.extract_tenant(request)
        
        if tenant_id:
            request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        return response
    
    def extract_tenant(self, request: Request) -> Optional[str]:
        # Extract from subdomain
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            return subdomain
        
        # Extract from header
        return request.headers.get("x-tenant-id")

app.add_middleware(TenantMiddleware)
```

## Production Deployment

### Environment Configuration
```bash
# Production environment variables
CLERK_SECRET_KEY=sk_live_your_production_secret_key
CLERK_JWT_KEY="-----BEGIN PUBLIC KEY-----
Your JWT public key for local verification
-----END PUBLIC KEY-----"

# Optional: Custom Clerk API settings
CLERK_API_URL=https://api.clerk.com
CLERK_API_VERSION=v1

# CORS settings for production
ALLOWED_ORIGINS=https://your-app.com,https://admin.your-app.com

# Security settings
SESSION_SECRET=your-session-secret-key
SECURE_COOKIES=true
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Run application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name api.your-app.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "https://your-app.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        add_header Access-Control-Allow-Credentials true always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}
```

This integration provides a complete, production-ready authentication system for FastAPI applications using Clerk, with support for all major authentication patterns and use cases.