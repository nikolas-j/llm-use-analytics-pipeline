from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.endpoints.v1.endpoints import router as v1_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="LLM Classifier API",
    description="API for retrieving classified conversation metrics and reports",
    version="1.0.0"
)

# Configure CORS
allowed_origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Include v1 router
app.include_router(v1_router, prefix="/v1", tags=["v1"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LLM Classifier API",
        "version": "1.0.0",
        "endpoints": {
            "/v1/metrics": "Get daily metrics by date",
            "/v1/reports": "Get daily reports by date"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

