"""
visualizations.py
API routes for visualization generation
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import structlog
from pydantic import BaseModel

from app.services.visualization_generator import visualization_generator

logger = structlog.get_logger()

router = APIRouter()


class BarChartRequest(BaseModel):
    sql_results: List[Dict[str, Any]]
    chart_type: str = "auto"
    user_query: str = ""


class DataTableRequest(BaseModel):
    sql_results: List[Dict[str, Any]]
    table_type: str = "auto"


@router.post("/bar-chart")
async def generate_bar_chart(request: BarChartRequest):
    """Generate bar chart visualization from SQL results"""
    try:
        logger.info("Generating bar chart", 
                   chart_type=request.chart_type, 
                   data_count=len(request.sql_results))
        
        result = visualization_generator.generate_bar_chart(
            request.sql_results, 
            request.chart_type,
            request.user_query
        )
        
        return result
        
    except Exception as e:
        logger.error("Bar chart generation failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate bar chart: {str(e)}"
        )


@router.post("/data-table")
async def generate_data_table(request: DataTableRequest):
    """Generate data table visualization from SQL results"""
    try:
        logger.info("Generating data table", 
                   table_type=request.table_type, 
                   data_count=len(request.sql_results))
        
        result = visualization_generator.generate_data_table(
            request.sql_results, 
            request.table_type
        )
        
        return result
        
    except Exception as e:
        logger.error("Data table generation failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate data table: {str(e)}"
        )


@router.get("/")
async def visualizations_info():
    """Get information about available visualization endpoints"""
    return {
        "endpoints": {
            "bar_chart": "POST /bar-chart - Generate bar chart visualizations",
            "data_table": "POST /data-table - Generate data table visualizations"
        },
        "supported_chart_types": [
            "auto", "parameter_comparison", "temporal_distribution", 
            "regional_comparison", "depth_analysis", "float_statistics"
        ],
        "supported_table_types": [
            "auto", "summary_statistics", "detailed_records", 
            "comparison_table", "aggregated_data"
        ]
    }
