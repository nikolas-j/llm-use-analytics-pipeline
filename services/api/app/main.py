from fastapi import FastAPI

from app.endpoints.v1.endpoints import router as v1_router

app = FastAPI(
    title="LLM Classifier API",
    description="API for retrieving classified conversation metrics and reports",
    version="1.0.0"
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

