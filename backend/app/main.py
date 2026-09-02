from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import health, auth, clinical, documents, ai, admin
from app.core.logging import setup_logging
from app.core.rate_limit import limiter

# Setup logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="Ayurveda AI Platform",
    description="AI-Assisted Ayurveda Consultation Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Apply rate limiter to the app
app.state.limiter = limiter

# Configure CORS for testing/staging - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,  # Allow credentials for auth
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Add logging middleware


 
@app.middleware("http")
async def log_requests(request, call_next):
    
    response = await call_next(request)
    
    return response

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(clinical.router, prefix="/api/v1/clinical", tags=["clinical"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Ayurveda AI Platform API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
