"""
query.py
Missing query route for your backend API
Add this to your app/api/routes/ directory
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import structlog
from datetime import datetime

from app.models.requests import QueryRequest
from app.models.responses import QueryResponse, QueryClassification, QueryMetadata, VisualizationSuggestion
from app.services.rag_pipeline import rag_pipeline
from app.services.multilingual_service import multilingual_service

logger = structlog.get_logger()

router = APIRouter()


@router.post("/process", response_model=Dict[str, Any])
async def process_natural_language_query(request: QueryRequest):
    """
    Process natural language query using RAG pipeline
    This is the endpoint your frontend is calling
    """
    try:
        logger.info("Processing natural language query", query=request.query)
        
        # Process query through RAG pipeline
        result = await rag_pipeline.process_query(
            user_query=request.query,
            max_results=request.max_results,
            language=request.language
        )
        
        # Extract data from RAG pipeline result
        retrieved_data = result.get("retrieved_data", {})
        sql_results = retrieved_data.get("sql_results", [])
        vector_results = retrieved_data.get("vector_results", [])
        
        # Use visualization data from RAG pipeline if available, otherwise create suggestions
        rag_visualization = result.get("visualization", {})
        rag_viz_suggestions = result.get("visualization_suggestions", {})
        visualizations = []
        
        if rag_viz_suggestions and rag_viz_suggestions.get("suggestions"):
            # Use the RAG pipeline's visualization suggestions
            for suggestion in rag_viz_suggestions["suggestions"]:
                visualizations.append(VisualizationSuggestion(
                    type=suggestion.get("type", "map"),
                    title=suggestion.get("title", "Data Visualization"),
                    description=suggestion.get("description", "Visualization of the data"),
                    data_columns=suggestion.get("data_columns", []),
                    config=suggestion.get("config", {})
                ))
        elif rag_visualization:
            # Use the RAG pipeline's visualization data
            visualizations = rag_visualization
        elif sql_results and request.include_visualizations:
            # Fallback: Create visualization suggestions if we have data
            first_record = sql_results[0] if sql_results else {}
            
            if "latitude" in first_record and "longitude" in first_record:
                visualizations.append(VisualizationSuggestion(
                    type="map",
                    title="ARGO Float Locations",
                    description="Interactive map showing ARGO float positions",
                    data_columns=["latitude", "longitude", "temperature", "salinity"],
                    config={
                        "color_by": "temperature",
                        "zoom": 4,
                        "show_trajectories": False
                    }
                ))
            
            # Add profile visualization if we have depth/pressure data
            if any(key in first_record for key in ["depth", "pressure", "temperature", "salinity"]):
                visualizations.append(VisualizationSuggestion(
                    type="profile",
                    title="Ocean Parameter Profiles",
                    description="Depth profiles of oceanographic parameters",
                    data_columns=["depth", "temperature", "salinity"],
                    config={
                        "x_params": ["temperature", "salinity"],
                        "y_param": "depth" if "depth" in first_record else "pressure"
                    }
                ))
        
        # Format response for frontend compatibility
        response_data = {
            "success": True,
            "query": request.query,
            "answer": result.get("answer", result.get("response", multilingual_service.translate("responses.query_processed", request.language))),
            "response": result.get("answer", result.get("response", multilingual_service.translate("responses.query_processed", request.language))),  # Alternative key
            "classification": {
                "query_type": result.get("classification", {}).get("query_type", "unknown"),
                "confidence": result.get("classification", {}).get("confidence", 0.5),
                "reasoning": result.get("classification", {}).get("reasoning", "Processed query"),
                "extracted_entities": result.get("classification", {}).get("extracted_entities", {}),
                "preprocessing_suggestions": []
            },
            "data": {
                "records": sql_results,
                "total_count": len(sql_results),
                "sql_results": sql_results,
                "vector_results": vector_results,
                "query_type": result.get("classification", {}).get("query_type", "sql_retrieval")
            },
            "metadata": {
                "query_type": result.get("classification", {}).get("query_type", "unknown"),
                "confidence": result.get("classification", {}).get("confidence", 0.5),
                "data_sources_used": result.get("metadata", {}).get("data_sources_used", []),
                "total_results": result.get("metadata", {}).get("total_results", len(sql_results)),
                "processing_time_ms": result.get("metadata", {}).get("processing_time", 0) * 1000,
                "sql_query": retrieved_data.get("sql_query"),
                "vector_search_query": retrieved_data.get("search_query")
            },
            "visualizations": visualizations,
            "visualization_suggestions": rag_viz_suggestions,
            "suggestions": [
                "Try asking about specific oceanographic parameters",
                "Use geographic regions like 'Arabian Sea' or 'Indian Ocean'",
                "Ask for comparisons between different time periods"
            ],
            "response_id": f"query_{datetime.now().timestamp()}",
            "query_id": f"query_{datetime.now().timestamp()}",  # Alternative key
            "timestamp": datetime.now(),
            "processing_time": result.get("metadata", {}).get("processing_time", 0)
        }
        
        # Translate the response to the requested language
        response_data = multilingual_service.translate_response(response_data, request.language)
        
        return response_data
        
    except Exception as e:
        logger.error("Natural language query processing failed", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail={
                "success": False,
                "error": str(e),
                "response": f"I encountered an error processing your query: {str(e)}",
                "suggestions": [
                    "Try rephrasing your query",
                    "Check if the backend services are running",
                    "Verify the database connection"
                ]
            }
        )


@router.get("/")
async def query_endpoint_info():
    """Get information about available query endpoints"""
    return {
        "endpoints": {
            "process": "POST /process - Process natural language queries",
            "info": "GET / - This endpoint information"
        },
        "example_queries": [
            "Show me temperature profiles in the Indian Ocean",
            "Find ARGO floats near coordinates 20N, 70E",
            "Compare salinity data in different regions",
            "What are the BGC oxygen levels in the Arabian Sea?"
        ],
        "supported_formats": ["json"],
        "max_results": 1000
    }