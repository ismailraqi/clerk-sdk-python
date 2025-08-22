# FastAPI Integration with Clerk Authentication

A comprehensive example demonstrating how to integrate [Clerk](https://clerk.com) authentication with [FastAPI](https://fastapi.tiangolo.com/) for complete user management, session handling, and role-based access control.

## Features

- ✅ **JWT Token Verification**: Secure token validation using Clerk's public keys
- ✅ **User Management**: Complete CRUD operations for users
- ✅ **Session Management**: Handle user sessions and token creation
- ✅ **Organization Management**: Multi-tenant support with organizations and memberships
- ✅ **Role-Based Access Control**: Protect routes based on user roles
- ✅ **Permission-Based Authorization**: Fine-grained permissions system
- ✅ **Middleware Integration**: Seamless authentication middleware
- ✅ **Multiple Auth Patterns**: Various ways to protect and authenticate routes
- ✅ **Webhook Support**: Handle Clerk webhooks for real-time updates
- ✅ **Comprehensive Documentation**: Full API documentation with Swagger UI

## Quick Start

### Prerequisites

1. **Clerk Account**: Sign up at [clerk.com](https://clerk.com)
2. **Python 3.9+**: Make sure you have Python 3.9 or newer
3. **Clerk Application**: Create a new application in your Clerk dashboard

### Installation

1. **Clone and Navigate**:
   ```bash
   cd examples/fastapi_integration
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**:
   Create a `.env` file with your Clerk credentials:
   ```env
   CLERK_SECRET_KEY=sk_test_your_secret_key_here
   CLERK_JWT_KEY="-----BEGIN PUBLIC KEY-----
   your_jwt_public_key_here
   -----END PUBLIC KEY-----"
   ```

   **Getting Your Keys**:
   - **Secret Key**: Go to Clerk Dashboard → API Keys → Secret Key
   - **JWT Key**: Go to Clerk Dashboard → API Keys → Show JWT public key (optional, for local verification)

4. **Run the Application**:
   ```bash
   python main.py
   # or
   uvicorn main:app --reload
   ```

5. **Access the API**:
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health
   - **API Root**: http://localhost:8000/

## Project Structure

```
fastapi_integration/
├── main.py                    # Main FastAPI application
├── auth.py                    # Authentication middleware and dependencies
├── models.py                  # Pydantic models for request/response
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── routers/
    ├── __init__.py
    ├── auth.py               # Authentication endpoints
    ├── users.py              # User management endpoints
    ├── organizations.py      # Organization management endpoints
    └── protected.py          # Example protected routes
```

## Authentication Methods

This integration supports multiple authentication methods:

### 1. Bearer Token (Recommended)
```bash
curl -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
     http://localhost:8000/protected/basic
```

### 2. Session Cookie
The `__session` cookie is automatically checked if present.

### 3. Custom Header
You can modify the authentication to check custom headers.

## API Endpoints

### Authentication (`/auth`)
- `GET /auth/me` - Get current user information
- `GET /auth/status` - Check authentication status (no auth required)
- `POST /auth/sign-in-token` - Create sign-in tokens
- `POST /auth/session-token` - Create session tokens
- `POST /auth/revoke-session` - Revoke current session
- `GET /auth/sessions` - List user sessions
- `GET /auth/permissions` - Get user permissions
- `POST /auth/logout` - Logout user

### User Management (`/users`)
- `POST /users/` - Create new user (requires permissions)
- `GET /users/` - List users (requires permissions)
- `GET /users/me` - Get current user details
- `GET /users/{user_id}` - Get specific user (requires permissions)
- `PATCH /users/me` - Update current user
- `PATCH /users/{user_id}` - Update user (requires permissions)
- `DELETE /users/{user_id}` - Delete user (requires permissions)
- `POST /users/{user_id}/ban` - Ban user (requires permissions)
- `POST /users/{user_id}/unban` - Unban user (requires permissions)

### Organization Management (`/organizations`)
- `POST /organizations/` - Create organization
- `GET /organizations/` - List organizations
- `GET /organizations/{org_id}` - Get organization details
- `PATCH /organizations/{org_id}` - Update organization (admin only)
- `DELETE /organizations/{org_id}` - Delete organization (admin only)
- `POST /organizations/{org_id}/memberships` - Add member (admin only)
- `GET /organizations/{org_id}/memberships` - List members
- `PATCH /organizations/{org_id}/memberships/{user_id}` - Update membership (admin only)
- `DELETE /organizations/{org_id}/memberships/{user_id}` - Remove member (admin only)
- `POST /organizations/{org_id}/invitations` - Invite user (admin only)
- `GET /organizations/{org_id}/invitations` - List invitations (admin only)

### Protected Routes (`/protected`)
- `GET /protected/basic` - Basic protected route
- `GET /protected/optional-auth` - Optional authentication
- `GET /protected/admin-only` - Admin role required
- `GET /protected/user-management` - Specific permissions required
- `GET /protected/dashboard-data` - Role-based dashboard data
- `POST /protected/secure-action` - Permission-based actions

## Usage Examples

### 1. Basic Authentication

```python
from fastapi import FastAPI, Depends
from auth import get_current_user, ClerkUser, get_clerk_user

app = FastAPI()

@app.get("/profile")
async def get_profile(user: ClerkUser = Depends(get_clerk_user)):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "organization": user.organization_id
    }
```

### 2. Role-Based Protection

```python
from auth import require_role

@app.get("/admin-panel")
async def admin_panel(user = Depends(require_role("admin"))):
    return {"message": "Welcome to admin panel"}
```

### 3. Permission-Based Protection

```python
from auth import require_permissions

@app.get("/user-management")
async def user_management(
    user = Depends(require_permissions(["org:user_management:read"]))
):
    return {"message": "User management access granted"}
```

### 4. Custom Permission Logic

```python
from auth import get_clerk_user, ClerkUser

@app.get("/custom-logic")
async def custom_logic(user: ClerkUser = Depends(get_clerk_user)):
    if not user.organization_id:
        raise HTTPException(403, "Organization required")
    
    if user.has_permission("custom:action"):
        return {"message": "Custom action allowed"}
    else:
        raise HTTPException(403, "Insufficient permissions")
```

## Frontend Integration

### React Example

```javascript
import { useAuth } from '@clerk/clerk-react';

function APICall() {
  const { getToken } = useAuth();
  
  const callAPI = async () => {
    const token = await getToken();
    
    const response = await fetch('http://localhost:8000/protected/basic', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    console.log(data);
  };
  
  return <button onClick={callAPI}>Call Protected API</button>;
}
```

### Next.js Example

```javascript
import { auth } from '@clerk/nextjs';

export default async function ServerComponent() {
  const { getToken } = auth();
  const token = await getToken();
  
  const response = await fetch('http://localhost:8000/users/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
    }
  });
  
  const user = await response.json();
  return <div>Hello, {user.first_name}!</div>;
}
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CLERK_SECRET_KEY` | Yes | Your Clerk secret key from the dashboard |
| `CLERK_JWT_KEY` | No | Public key for local JWT verification (optional) |

### Authentication Options

```python
from auth import AuthenticateRequestOptions

options = AuthenticateRequestOptions(
    secret_key="your_secret_key",
    jwt_key="your_jwt_public_key",  # Optional
    authorized_parties=["https://your-domain.com"],
    clock_skew_in_ms=5000,
    accepts_token=["session_token", "oauth_token"]
)
```

## Security Features

### Token Verification
- Validates JWT signature using Clerk's public keys
- Checks token expiration and issuer
- Supports both remote (API) and local (public key) verification

### Permission System
- Organization-based permissions
- Role-based access control
- Fine-grained permission checking
- Automatic permission inheritance

### Security Best Practices
- CORS configuration for cross-origin requests
- Secure cookie handling
- Proper error handling without information leakage
- Request rate limiting (recommended for production)

## Error Handling

The API provides comprehensive error responses:

```json
{
  "detail": "Authentication required",
  "status_code": 401,
  "path": "/protected/basic"
}
```

Common error codes:
- `401`: Authentication required or invalid token
- `403`: Insufficient permissions or wrong role
- `404`: Resource not found
- `422`: Validation error
- `500`: Server error

## Testing

### Run Tests
```bash
pytest tests/ -v
```

### Test with curl

```bash
# Health check (no auth required)
curl http://localhost:8000/health

# Get auth status (no auth required)
curl http://localhost:8000/auth/status

# Protected endpoint (requires auth)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/protected/basic
```

## Deployment

### Production Considerations

1. **Environment Variables**: Use secure secret management
2. **HTTPS**: Always use HTTPS in production
3. **CORS**: Configure specific origins, not wildcards
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Monitoring**: Add logging and monitoring
6. **Error Handling**: Don't expose sensitive information in errors

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup for Production

```bash
export CLERK_SECRET_KEY="sk_live_your_production_key"
export CLERK_JWT_KEY="your_production_jwt_key"
```

## Troubleshooting

### Common Issues

1. **"Clerk middleware not initialized"**
   - Ensure `CLERK_SECRET_KEY` is set
   - Call `initialize_clerk()` before using dependencies

2. **"Authentication required" on valid requests**
   - Check token format: should be `Bearer <token>`
   - Verify token is not expired
   - Ensure `authorized_parties` includes your domain

3. **"Permission denied" errors**
   - Check user's organization membership
   - Verify user has required permissions
   - Ensure organization context is set

4. **CORS errors in browser**
   - Add your frontend domain to `allow_origins`
   - Check that credentials are included in requests

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Resources

- [Clerk Documentation](https://clerk.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Clerk Python SDK](https://github.com/clerk/clerk-sdk-python)
- [JWT.io](https://jwt.io/) for token debugging

## License

This example is provided under the MIT License. See the main repository for details.

## Support

For questions and support:
- [Clerk Discord Community](https://clerk.com/discord)
- [Clerk Support](https://clerk.com/support)
- [FastAPI GitHub Discussions](https://github.com/tiangolo/fastapi/discussions)