"""
CONCORD FastAPI Application
Main entry point for the API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from app.config import settings
from app.database import engine, Base
from app.exceptions import (
    concord_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    ConcordException
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CONCORD API",
    description="Customer-level control plane for autonomous agent fleets",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(ConcordException, concord_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting CONCORD API server...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1]}")  # Log without credentials


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down CONCORD API server...")


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "service": "CONCORD",
        "version": "0.1.0",
        "status": "operational",
        "description": "Customer-level control plane for autonomous agent fleets"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler - should not be reached due to app.add_exception_handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )


# Import and include routers
from app.routes import actions, agents, decisions

app.include_router(actions.router, prefix="/api/v1", tags=["actions"])
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
app.include_router(decisions.router, prefix="/api/v1", tags=["decisions"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
