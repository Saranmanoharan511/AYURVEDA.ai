from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from app.core.config import settings

# Create rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else "memory://",
)

# Custom rate limit exceeded handler
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    raise HTTPException(
        status_code=429,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Maximum {exc.detail} requests per minute.",
            "retry_after": 60,  # seconds
        }
    )

# Apply custom handler
limiter._rate_limit_exceeded_handler = rate_limit_exceeded_handler


# Rate limit decorators for different endpoint types
def public_rate_limit():
    """Rate limit for public endpoints (e.g., health check)."""
    return limiter.limit("10/minute")


def auth_rate_limit():
    """Rate limit for authentication endpoints (e.g., login, register)."""
    return limiter.limit("5/minute")


def standard_rate_limit():
    """Rate limit for standard authenticated endpoints."""
    return limiter.limit("30/minute")


def strict_rate_limit():
    """Rate limit for sensitive operations (e.g., document upload)."""
    return limiter.limit("10/minute")


def ai_rate_limit():
    """Rate limit for AI endpoints (resource-intensive)."""
    return limiter.limit("20/minute")
