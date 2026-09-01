from fastapi import APIRouter
from sqlalchemy import text
from app.core.config import settings
from app.db.session import database_engine

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint to verify server and database connectivity."""
    
    health_status = {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "disconnected"
    }
    
    # Check database connectivity
    try:
        with database_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status
