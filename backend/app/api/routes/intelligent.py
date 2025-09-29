"""
intelligent.py
MCP-enhanced intelligent API endpoints for ARGO FloatChat
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import structlog
from app.services.intelligent_analysis import intelligent_analysis_service

logger = structlog.get_logger()

router = APIRouter(prefix="/api/intelligent", tags=["intelligent"])


class OceanAnalysisRequest(BaseModel):
    """Request model for ocean condition analysis"""
    region: str = Field(..., description="Ocean region (e.g., 'Arabian Sea', 'Bay of Bengal')")
    parameter: str = Field(..., description="Ocean parameter (temperature, salinity, oxygen, chlorophyll, etc.)")
    time_period: Optional[str] = Field(default="", description="Time period for analysis")
    analysis_type: str = Field(default="statistical", description="Type of analysis: statistical, trend, anomaly, comparison, correlation")


class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection"""
    query: str = Field(..., description="Query to analyze for anomalies")
    threshold: float = Field(default=2.0, ge=1.0, le=5.0, description="Anomaly detection threshold (standard deviations)")


class TrendAnalysisRequest(BaseModel):
    """Request model for trend analysis"""
    parameter: str = Field(..., description="Parameter to analyze for trends")
    region: str = Field(..., description="Ocean region")
    time_range: Optional[str] = Field(default="", description="Time range for trend analysis")


class CorrelationAnalysisRequest(BaseModel):
    """Request model for correlation analysis"""
    parameters: List[str] = Field(..., min_items=2, max_items=5, description="Parameters to correlate (2-5 parameters)")
    region: Optional[str] = Field(default="", description="Ocean region filter")


class SmartSuggestionsRequest(BaseModel):
    """Request model for smart suggestions"""
    current_query: str = Field(..., description="Current user query")
    user_history: Optional[List[str]] = Field(default=None, description="Previous user queries for context")


@router.post("/analyze-ocean-conditions")
async def analyze_ocean_conditions(request: OceanAnalysisRequest) -> Dict[str, Any]:
    """Perform intelligent oceanographic analysis"""
    try:
        logger.info("Intelligent ocean analysis requested", 
                   region=request.region, parameter=request.parameter, analysis_type=request.analysis_type)
        
        result = await intelligent_analysis_service.analyze_ocean_conditions(
            region=request.region,
            parameter=request.parameter,
            time_period=request.time_period,
            analysis_type=request.analysis_type
        )
        
        return {
            "success": True,
            "endpoint": "analyze-ocean-conditions",
            "request": request.dict(),
            "result": result
        }
        
    except Exception as e:
        logger.error("Error in ocean analysis endpoint", error=str(e))
        raise HTTPException(status_code=500, detail=f"Ocean analysis failed: {str(e)}")


@router.post("/detect-anomalies")
async def detect_anomalies(request: AnomalyDetectionRequest) -> Dict[str, Any]:
    """Detect anomalies in oceanographic data"""
    try:
        logger.info("Anomaly detection requested", query=request.query, threshold=request.threshold)
        
        result = await intelligent_analysis_service.detect_anomalies(
            query=request.query,
            threshold=request.threshold
        )
        
        return {
            "success": True,
            "endpoint": "detect-anomalies",
            "request": request.dict(),
            "result": result
        }
        
    except Exception as e:
        logger.error("Error in anomaly detection endpoint", error=str(e))
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


@router.post("/analyze-trends")
async def analyze_trends(request: TrendAnalysisRequest) -> Dict[str, Any]:
    """Analyze trends in oceanographic parameters"""
    try:
        logger.info("Trend analysis requested", parameter=request.parameter, region=request.region)
        
        result = await intelligent_analysis_service.analyze_trends(
            parameter=request.parameter,
            region=request.region,
            time_range=request.time_range
        )
        
        return {
            "success": True,
            "endpoint": "analyze-trends",
            "request": request.dict(),
            "result": result
        }
        
    except Exception as e:
        logger.error("Error in trend analysis endpoint", error=str(e))
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.post("/find-correlations")
async def find_correlations(request: CorrelationAnalysisRequest) -> Dict[str, Any]:
    """Find correlations between oceanographic parameters"""
    try:
        logger.info("Correlation analysis requested", parameters=request.parameters, region=request.region)
        
        result = await intelligent_analysis_service.find_correlations(
            parameters=request.parameters,
            region=request.region
        )
        
        return {
            "success": True,
            "endpoint": "find-correlations",
            "request": request.dict(),
            "result": result
        }
        
    except Exception as e:
        logger.error("Error in correlation analysis endpoint", error=str(e))
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")


@router.post("/smart-suggestions")
async def get_smart_suggestions(request: SmartSuggestionsRequest) -> Dict[str, Any]:
    """Generate intelligent suggestions based on current query"""
    try:
        logger.info("Smart suggestions requested", query=request.current_query)
        
        result = await intelligent_analysis_service.generate_smart_suggestions(
            current_query=request.current_query,
            user_history=request.user_history
        )
        
        return {
            "success": True,
            "endpoint": "smart-suggestions",
            "request": request.dict(),
            "result": result
        }
        
    except Exception as e:
        logger.error("Error in smart suggestions endpoint", error=str(e))
        raise HTTPException(status_code=500, detail=f"Smart suggestions failed: {str(e)}")


@router.get("/available-parameters")
async def get_available_parameters() -> Dict[str, Any]:
    """Get list of available oceanographic parameters"""
    try:
        parameters = {
            "core_parameters": [
                "temperature", "salinity", "pressure", "depth"
            ],
            "bgc_parameters": [
                "dissolved_oxygen", "chlorophyll", "nitrate", "ph"
            ],
            "parameter_descriptions": {
                "temperature": "Sea water temperature in degrees Celsius",
                "salinity": "Practical salinity units (PSU)",
                "pressure": "Sea pressure in decibars",
                "depth": "Depth in meters",
                "dissolved_oxygen": "Dissolved oxygen concentration (μmol/kg)",
                "chlorophyll": "Chlorophyll-a concentration (mg/m³)",
                "nitrate": "Nitrate concentration (μmol/kg)",
                "ph": "pH level (dimensionless)"
            },
            "analysis_types": [
                "statistical", "trend", "anomaly", "comparison", "correlation"
            ],
            "regions": [
                "Indian Ocean", "Arabian Sea", "Bay of Bengal", "Southern Ocean"
            ]
        }
        
        return {
            "success": True,
            "endpoint": "available-parameters",
            "parameters": parameters
        }
        
    except Exception as e:
        logger.error("Error getting available parameters", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get parameters: {str(e)}")


@router.get("/analysis-capabilities")
async def get_analysis_capabilities() -> Dict[str, Any]:
    """Get information about intelligent analysis capabilities"""
    try:
        capabilities = {
            "ocean_analysis": {
                "description": "Comprehensive oceanographic condition analysis",
                "features": [
                    "Statistical analysis of ocean parameters",
                    "Trend detection and analysis",
                    "Anomaly identification",
                    "Parameter comparison",
                    "Correlation analysis"
                ]
            },
            "anomaly_detection": {
                "description": "Advanced anomaly detection using statistical methods",
                "features": [
                    "Z-score based anomaly detection",
                    "Configurable threshold settings",
                    "Severity classification",
                    "Contextual insights",
                    "Recommendations for further investigation"
                ]
            },
            "trend_analysis": {
                "description": "Temporal trend analysis of oceanographic parameters",
                "features": [
                    "Linear trend calculation",
                    "Trend strength assessment",
                    "Temporal pattern analysis",
                    "Predictive modeling",
                    "Significance testing"
                ]
            },
            "correlation_analysis": {
                "description": "Multi-parameter correlation analysis",
                "features": [
                    "Pearson correlation matrix",
                    "Strongest correlation identification",
                    "Oceanographic significance assessment",
                    "Parameter relationship insights",
                    "Statistical strength classification"
                ]
            },
            "smart_suggestions": {
                "description": "AI-powered intelligent suggestions",
                "features": [
                    "Context-aware query suggestions",
                    "Follow-up question generation",
                    "Related analysis recommendations",
                    "User behavior adaptation",
                    "Scientific insight suggestions"
                ]
            }
        }
        
        return {
            "success": True,
            "endpoint": "analysis-capabilities",
            "capabilities": capabilities,
            "supported_languages": [
                "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "ar", "hi"
            ],
            "data_constraints": {
                "scope": "Indian Ocean ARGO data only",
                "external_sources": False,
                "data_freshness": "Real-time from database"
            }
        }
        
    except Exception as e:
        logger.error("Error getting analysis capabilities", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.get("/health")
async def intelligent_health_check() -> Dict[str, Any]:
    """Health check for intelligent analysis services"""
    try:
        # Test service initialization
        service_status = {
            "intelligent_analysis_service": "operational",
            "database_connection": "connected" if intelligent_analysis_service.db_manager else "disconnected",
            "llm_client": "connected" if intelligent_analysis_service.llm_client else "disconnected",
            "query_classifier": "operational" if intelligent_analysis_service.query_classifier else "disconnected"
        }
        
        # Test basic functionality
        test_result = await intelligent_analysis_service.generate_smart_suggestions(
            current_query="test query"
        )
        
        return {
            "success": True,
            "endpoint": "intelligent-health",
            "status": "healthy",
            "services": service_status,
            "test_result": "passed" if test_result.get("success") else "failed",
            "timestamp": "2025-09-26T01:00:00Z"
        }
        
    except Exception as e:
        logger.error("Error in intelligent health check", error=str(e))
        return {
            "success": False,
            "endpoint": "intelligent-health",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-09-26T01:00:00Z"
        }
