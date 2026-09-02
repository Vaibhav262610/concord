"""
CONCORD FastAPI Application
Main entry point for the API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.database import engine, Base

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
    """Global exception handler"""
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


# Import and include routers (will be added in later phases)
# from app.routes import actions, agents, customers, decisions, policies, simulation, analytics
# app.include_router(actions.router, prefix="/api/v1", tags=["actions"])
# app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
# app.include_router(customers.router, prefix="/api/v1", tags=["customers"])
# app.include_router(decisions.router, prefix="/api/v1", tags=["decisions"])
# app.include_router(policies.router, prefix="/api/v1", tags=["policies"])
# app.include_router(simulation.router, prefix="/api/v1", tags=["simulation"])
# app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
