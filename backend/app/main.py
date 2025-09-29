"""
Main FastAPI Application for ARGO AI Backend

This is the main entry point for the ARGO AI Backend API server. It provides
a RESTful API for querying ARGO oceanographic data using natural language
queries and AI-powered responses.

Key Features:
- Natural language query processing using RAG (Retrieval-Augmented Generation)
- Multiple data sources: PostgreSQL database and vector database
- Interactive visualizations and maps
- Support for various oceanographic parameters
- Geographic filtering and region-specific queries
- Multiple LLM providers with fallback support

API Endpoints:
- /health: System health and status checks
- /api/v1/query: Natural language query processing
- /api/v1/data: Direct data access and search
- /docs: Interactive API documentation (Swagger UI)
- /redoc: Alternative API documentation (ReDoc)

Author: ARGO AI Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager

# Import application components
from app.config import settings
from app.api.routes import query, data, health, intelligent, visualizations, export
from app.core.database import db_manager
from app.core.vector_db import vector_db_manager
from app.services.rag_pipeline import rag_pipeline

# =============================================================================
# STRUCTURED LOGGING CONFIGURATION
# =============================================================================
# Configure structured logging for better observability and debugging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,           # Filter log levels
        structlog.stdlib.add_logger_name,           # Add logger name to log records
        structlog.stdlib.add_log_level,             # Add log level to log records
        structlog.stdlib.PositionalArgumentsFormatter(),  # Format positional arguments
        structlog.processors.TimeStamper(fmt="iso"), # Add ISO timestamp
        structlog.processors.StackInfoRenderer(),    # Add stack trace info
        structlog.processors.format_exc_info,        # Format exception information
        structlog.processors.UnicodeDecoder(),       # Decode unicode strings
        structlog.processors.JSONRenderer()          # Output as JSON for structured logging
    ],
    context_class=dict,                             # Use dict for context
    logger_factory=structlog.stdlib.LoggerFactory(), # Use standard library logger
    wrapper_class=structlog.stdlib.BoundLogger,     # Use bound logger for context
    cache_logger_on_first_use=True,                 # Cache loggers for performance
)

# Create application logger
logger = structlog.get_logger()


# =============================================================================
# APPLICATION LIFECYCLE MANAGEMENT
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management for startup and shutdown operations
    
    This context manager handles:
    - Database connection testing during startup
    - Vector database initialization and health checks
    - RAG pipeline health verification
    - Graceful shutdown procedures
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None: Application runs normally after startup checks
    """
    # =============================================================================
    # STARTUP SEQUENCE
    # =============================================================================
    logger.info("Starting ARGO AI Backend")
    
    try:
        # Test PostgreSQL database connection
        if not db_manager.test_connection():
            logger.warning("Database connection failed during startup")
        else:
            logger.info("Database connection successful")
        
        # Test vector database and get collection statistics
        vector_stats = vector_db_manager.get_collection_stats()
        logger.info("Vector database stats", stats=vector_stats)
        
        # Perform comprehensive health check on RAG pipeline
        health = await rag_pipeline.health_check()
        logger.info("RAG pipeline health check", health=health)
        
    except Exception as e:
        logger.error("Startup health checks failed", error=str(e))
    
    # Application is ready to serve requests
    yield
    
    # =============================================================================
    # SHUTDOWN SEQUENCE
    # =============================================================================
    logger.info("Shutting down ARGO AI Backend")


# =============================================================================
# FASTAPI APPLICATION INITIALIZATION
# =============================================================================
# Create the main FastAPI application with metadata and configuration
app = FastAPI(
    title=settings.APP_NAME,                    # Application name for documentation
    version=settings.APP_VERSION,               # Version number
    description="AI-powered conversational system for ARGO float oceanographic data",
    lifespan=lifespan                           # Attach lifecycle management
)

# =============================================================================
# CORS MIDDLEWARE CONFIGURATION
# =============================================================================
# Add Cross-Origin Resource Sharing middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins (configure properly for production)
    allow_credentials=True,     # Allow cookies and authentication headers
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)


# =============================================================================
# GLOBAL EXCEPTION HANDLING
# =============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    
    This handler catches any unhandled exceptions and returns a standardized
    error response to prevent sensitive information from being exposed to clients.
    
    Args:
        request: The HTTP request that caused the exception
        exc: The exception that was raised
        
    Returns:
        JSONResponse: Standardized error response
    """
    logger.error("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred while processing your request."
        }
    )


# =============================================================================
# API ROUTE REGISTRATION
# =============================================================================
# Register API route modules with their respective prefixes and tags
app.include_router(health.router, prefix="/health", tags=["Health"])      # Health check endpoints
app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])  # Natural language query processing
app.include_router(data.router, prefix="/api/v1/data", tags=["Data"])     # Direct data access endpoints
app.include_router(visualizations.router, prefix="/api/v1/visualizations", tags=["Visualizations"])  # Visualization generation endpoints
app.include_router(export.router, prefix="/api/v1", tags=["Export"])      # Data export endpoints
app.include_router(intelligent.router, tags=["Intelligent"])              # MCP-enhanced intelligent analysis


# =============================================================================
# ROOT ENDPOINTS
# =============================================================================
@app.get("/")
async def root():
    """
    Root endpoint providing basic API information
    
    Returns:
        dict: Basic API information including available endpoints
    """
    return {
        "message": "ARGO AI Backend API",
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",           # System health checks
            "query": "/api/v1/query",      # Natural language queries
            "data": "/api/v1/data",        # Direct data access
            "intelligent": "/api/intelligent", # MCP-enhanced intelligent analysis
            "docs": "/docs",               # Swagger UI documentation
            "redoc": "/redoc"              # ReDoc documentation
        }
    }


@app.get("/info")
async def get_api_info():
    """
    Comprehensive API and system information endpoint
    
    Provides detailed information about the API, database status,
    vector database statistics, and RAG pipeline health.
    
    Returns:
        dict: Comprehensive system information
        
    Raises:
        HTTPException: If system information cannot be retrieved
    """
    try:
        # Get database statistics
        db_stats = db_manager.get_database_stats()
        
        # Get vector database statistics
        vector_stats = vector_db_manager.get_collection_stats()
        
        # Get RAG pipeline health status
        rag_health = await rag_pipeline.health_check()
        
        return {
            "api": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "debug": settings.DEBUG
            },
            "database": db_stats,                          # PostgreSQL database stats
            "vector_database": vector_stats,               # ChromaDB vector database stats
            "rag_pipeline": rag_health,                    # RAG pipeline health status
            "supported_parameters": settings.SUPPORTED_PARAMETERS,  # Available oceanographic parameters
            "ocean_regions": settings.OCEAN_REGIONS        # Supported ocean regions
        }
        
    except Exception as e:
        logger.error("Failed to get API info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve API information")


# =============================================================================
# DEVELOPMENT SERVER CONFIGURATION
# =============================================================================
if __name__ == "__main__":
    """
    Development server entry point
    
    This block runs the FastAPI application using Uvicorn when the script
    is executed directly (not imported as a module).
    """
    import uvicorn
    uvicorn.run(
        "app.main:app",           # Application module path
        host=settings.HOST,       # Server host address
        port=settings.PORT,       # Server port number
        reload=settings.DEBUG,    # Enable auto-reload in debug mode
        log_level="info"          # Logging level
    )