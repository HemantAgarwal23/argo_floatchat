"""
health.py
Health check API routes
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import structlog
from app.models.responses import SystemHealth, DatabaseStats
from app.core.database import db_manager
from app.core.vector_db import vector_db_manager
from app.services.rag_pipeline import rag_pipeline

logger = structlog.get_logger()

router = APIRouter()


@router.get("/", response_model=SystemHealth)
async def health_check():
    """
    Comprehensive health check for all system components
    """
    try:
        # Check RAG pipeline health
        rag_health = await rag_pipeline.health_check()
        
        return SystemHealth(
            database=rag_health.get("database", False),
            vector_db=rag_health.get("vector_db", False),
            llm=rag_health.get("llm", False),
            overall=rag_health.get("overall", False),
            details=rag_health,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return SystemHealth(
            database=False,
            vector_db=False,
            llm=False,
            overall=False,
            details={"error": str(e)},
            timestamp=datetime.now()
        )


@router.get("/database", response_model=DatabaseStats)
async def database_health():
    """
    Detailed database health and statistics
    """
    try:
        if not db_manager.test_connection():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        stats = db_manager.get_database_stats()
        
        return DatabaseStats(
            total_floats=stats.get("total_floats", 0),
            total_profiles=stats.get("total_profiles", 0),
            date_range=stats.get("date_range", {}),
            profiles_with_bgc=stats.get("profiles_with_bgc", 0),
            latest_update=datetime.now(),
            geographic_coverage={
                "description": "Global coverage with focus on Indian Ocean",
                "regions": ["Indian Ocean", "Arabian Sea", "Bay of Bengal"]
            },
            parameter_availability={
                "temperature": stats.get("total_profiles", 0),
                "salinity": stats.get("total_profiles", 0),
                "bgc_parameters": stats.get("profiles_with_bgc", 0)
            }
        )
        
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Database health check failed: {str(e)}")


@router.get("/vector-db")
async def vector_db_health():
    """
    Vector database health and statistics
    """
    try:
        stats = vector_db_manager.get_collection_stats()
        
        return {
            "status": "healthy" if stats.get("total_documents", 0) > 0 else "no_data",
            "total_documents": stats.get("total_documents", 0),
            "collection_name": stats.get("collection_name", ""),
            "embedding_model": stats.get("embedding_model", ""),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error("Vector DB health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Vector database health check failed: {str(e)}")


@router.get("/llm")
async def llm_health():
    """
    LLM service health check
    """
    try:
        from app.core.llm_client import llm_client
        
        # Simple test query
        test_result = llm_client.classify_query_type("test health check query")
        
        return {
            "status": "healthy" if test_result.get("query_type") else "failed",
            "model": "llama-3.1-70b-versatile",
            "provider": "groq",
            "test_response": bool(test_result.get("query_type")),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error("LLM health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"LLM service health check failed: {str(e)}")


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes-style readiness check
    """
    try:
        health = await health_check()
        
        if health.overall:
            return {"status": "ready", "timestamp": datetime.now()}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
            
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness check
    """
    return {"status": "alive", "timestamp": datetime.now()}