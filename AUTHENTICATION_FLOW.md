# Authentication Flow

## Registration
1. User submits: `full_name`, `email`, `password`
2. Backend validates password strength (8+ chars, uppercase, lowercase, digit, special char)
3. Backend checks if email already exists
4. Backend hashes password with bcrypt
5. Backend checks whether SMTP email settings are configured in system settings
6. Backend creates user in database
7. If SMTP is configured:
   - user is created as `email_verified=false`
   - backend creates a one-time verification token
   - backend sends an email verification link to `{auth_backend_base_url}/auth/verify-email?token=...` (from DB settings, fallback: `AUTH_BACKEND_BASE_URL`)
8. If SMTP is not configured:
   - user is created as `email_verified=true`
9. User is redirected to login page

## Email Verification
1. User opens verification link (`GET /auth/verify-email?token=...`)
2. Backend validates token hash, expiry, and usage status
3. Backend marks user `email_verified=true`
4. Backend marks verification token as used
5. Backend redirects user to frontend login (`{auth_frontend_base_url}/login` from DB settings, fallback: `AUTH_FRONTEND_BASE_URL`)
6. If token is invalid/already used and request accepts HTML, backend renders an error page and redirects to frontend login after 10 seconds

## Forgot Password
1. User submits email to `POST /auth/forgot-password`
2. Backend always returns the same success message (prevents user enumeration)
3. If user exists:
   - backend invalidates existing unused reset tokens
   - backend creates a one-time password reset token
4. If SMTP is configured in system settings:
   - backend sends reset link to `{auth_frontend_base_url}/reset-password?token=...` (from DB settings, fallback: `AUTH_FRONTEND_BASE_URL`)

## Reset Password
1. User submits token + new password to `POST /auth/reset-password`
2. Backend validates token hash, expiry, and usage status
3. Backend validates new password strength
4. Backend updates password hash
5. Backend revokes all active refresh sessions for that user
6. Backend marks reset token as used

## Login
1. User submits: `email`, `password`
2. Backend authenticates credentials
3. Backend blocks login when `email_verified=false` (403)
3. Backend generates:
   - **Access Token** (JWT, short-lived, e.g., 15 minutes)
   - **Refresh Token** (random token, long-lived, e.g., 7 days)
4. Backend stores refresh token in database with:
   - User ID
   - Token hash
   - Client IP + User-Agent (fingerprint)
   - Expiry date
5. Backend returns:
   - Access token in response body
   - Refresh token in HttpOnly cookie
6. Frontend stores access token in localStorage
7. User redirected to dashboard

## Authenticated Requests
1. Frontend sends access token in `Authorization: Bearer <token>` header
2. Backend validates JWT signature and expiry
3. Backend extracts user ID from token
4. Backend processes request with user context

## Token Refresh
1. When access token expires (401 response)
2. Frontend automatically calls `/auth/refresh` endpoint
3. Backend:
   - Extracts refresh token from HttpOnly cookie
   - Validates token hash exists in database
   - Checks token not revoked or expired
   - Validates client fingerprint matches
   - **Rotates token** (marks old as used, generates new)
4. Backend returns new access token + new refresh token
5. Frontend updates access token in localStorage
6. Frontend retries original request

## Logout
1. User clicks logout button
2. Frontend calls `/auth/logout` endpoint (with access token)
3. Backend:
   - Extracts refresh token from cookie
   - Marks refresh token as revoked
   - **Revokes all descendant tokens** (from token rotation chain)
   - Clears refresh token cookie
4. Frontend:
   - Removes access token from localStorage
   - Clears user state
   - Redirects to login page

**Security benefit:** Even if attacker has stolen refresh token, it becomes invalid immediately upon logout.

## Session Security Features

### Token Rotation
- Each refresh generates a NEW refresh token
- Old token marked as "used"
- If used token is reused → security breach detected → revoke entire chain
- Prevents token replay attacks

### Client Fingerprinting
- Refresh tokens bound to IP + User-Agent
- If fingerprint changes → refresh denied
- Prevents token theft across devices

### Refresh Token Revocation
- Users can logout from all devices
- Password reset revokes all active refresh sessions for that user
- Compromised tokens can be blacklisted

### Email Verification Gate
- If SMTP is configured, self-registered users cannot obtain tokens until email is verified.
- Admin-created users are marked verified at creation and do not require verification.

## Token Storage

| Token Type | Storage Location | Lifespan | Purpose |
|------------|-----------------|----------|---------|
| Access Token | localStorage | 15 min | API authentication |
| Refresh Token | HttpOnly Cookie | 7 days | Get new access tokens |

**Why this approach?**
- Access tokens in localStorage: Convenient for API calls, short-lived reduces risk
- Refresh tokens in HttpOnly cookies: Protected from XSS, longer-lived but more secure

## Security Considerations

### What if access token is stolen?
- Limited damage: Expires in 15 minutes
- Attacker can't get refresh token (HttpOnly cookie)
- User can logout to revoke all sessions

### What if refresh token is stolen?
- Attacker needs same IP + User-Agent (fingerprint check)
- User logout immediately revokes it
- Token rotation limits replay attacks

### What about XSS attacks?
- Access token in localStorage is vulnerable
- But short lifespan limits exposure
- Refresh token safe in HttpOnly cookie

### What about CSRF attacks?
- Refresh endpoint validates an HttpOnly refresh cookie plus token hash/fingerprint checks
- SameSite=Lax on cookies
- Explicit origin checking via CORS

## Rate Limiting

Rate limiting is applied on authentication endpoints. Recommended production thresholds:
- `/auth/register`: 5 attempts per IP per hour
- `/auth/token`: 10 attempts per IP per 15 minutes
- `/auth/refresh`: 30 attempts per IP per hour
- `/auth/forgot-password`: 10 attempts per IP per hour
- `/auth/reset-password`: 10 attempts per IP per hour

## Monitoring (Recommended)

Log and alert on:
- Multiple failed login attempts
- Refresh token reuse (potential breach)
- Fingerprint mismatches
- Unusual login locations
- High volume of registration attempts
