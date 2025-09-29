"""
data.py
Direct data access API routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import structlog
from datetime import datetime

from app.models.requests import DataSearchRequest, SemanticSearchRequest, FloatInfoRequest
from app.models.responses import (
    DataSearchResponse, SemanticSearchResponse, FloatInfoResponse,
    FloatInfo, ProfileSummary
)
from app.core.database import db_manager
from app.core.vector_db import vector_db_manager

logger = structlog.get_logger()

router = APIRouter()


@router.post("/search", response_model=DataSearchResponse)
async def search_data(request: DataSearchRequest):
    """
    Direct search of ARGO profile data with filters
    """
    try:
        logger.info("Direct data search", filters=request.dict())
        
        # Build SQL query based on filters
        query_parts = ["SELECT * FROM argo_profiles"]
        conditions = []
        params = []
        
        # Date filters
        if request.start_date:
            conditions.append("profile_date >= %s")
            params.append(request.start_date)
        
        if request.end_date:
            conditions.append("profile_date <= %s")
            params.append(request.end_date)
        
        # Geographic filters
        if request.min_latitude is not None:
            conditions.append("latitude >= %s")
            params.append(request.min_latitude)
        
        if request.max_latitude is not None:
            conditions.append("latitude <= %s")
            params.append(request.max_latitude)
        
        if request.min_longitude is not None:
            conditions.append("longitude >= %s")
            params.append(request.min_longitude)
        
        if request.max_longitude is not None:
            conditions.append("longitude <= %s")
            params.append(request.max_longitude)
        
        # Float ID filters
        if request.float_ids:
            placeholders = ','.join(['%s'] * len(request.float_ids))
            conditions.append(f"float_id IN ({placeholders})")
            params.extend(request.float_ids)
        
        # BGC data filter
        if request.include_bgc:
            conditions.append(
                "(dissolved_oxygen IS NOT NULL OR ph_in_situ IS NOT NULL OR "
                "nitrate IS NOT NULL OR chlorophyll_a IS NOT NULL)"
            )
        
        # Parameter-specific filters
        if request.parameters:
            param_conditions = []
            for param in request.parameters:
                if param in ["temperature", "salinity", "dissolved_oxygen", "ph_in_situ", "nitrate", "chlorophyll_a"]:
                    param_conditions.append(f"{param} IS NOT NULL")
            
            if param_conditions:
                conditions.append(f"({' OR '.join(param_conditions)})")
        
        # Build complete query
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query_parts.append("ORDER BY profile_date DESC")
        query_parts.append(f"LIMIT {request.limit}")
        
        sql_query = " ".join(query_parts)
        
        # Execute query
        results = db_manager.execute_query(sql_query, tuple(params) if params else None)
        
        # Get total count (without limit)
        count_query = sql_query.replace("SELECT *", "SELECT COUNT(*)")
        count_query = count_query.split("ORDER BY")[0]  # Remove ORDER BY and LIMIT
        count_result = db_manager.execute_query(count_query, tuple(params) if params else None)
        total_count = count_result[0]['count'] if count_result else 0
        
        # Determine columns
        columns = list(results[0].keys()) if results else []
        
        return DataSearchResponse(
            results=results,
            total_count=total_count,
            filters_applied=request.dict(exclude_none=True),
            columns=columns,
            metadata={
                "query_executed": sql_query,
                "execution_time": datetime.now(),
                "result_count": len(results)
            }
        )
        
    except Exception as e:
        logger.error("Data search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Data search failed: {str(e)}")


@router.post("/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic search using vector database
    """
    try:
        logger.info("Semantic search", query=request.query)
        
        # Perform semantic search
        results = vector_db_manager.semantic_search(
            query=request.query,
            limit=request.limit,
            filters=request.filters
        )
        
        # Filter by similarity threshold
        filtered_results = [
            result for result in results 
            if result.get('distance', 0) <= (1 - request.similarity_threshold)
        ]
        
        return SemanticSearchResponse(
            results=filtered_results,
            query=request.query,
            total_results=len(filtered_results),
            search_metadata={
                "similarity_threshold": request.similarity_threshold,
                "filters_applied": request.filters,
                "search_time": datetime.now()
            }
        )
        
    except Exception as e:
        logger.error("Semantic search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@router.post("/floats", response_model=FloatInfoResponse)
async def get_float_info(request: FloatInfoRequest):
    """
    Get detailed information about specific ARGO floats
    """
    try:
        logger.info("Float info request", float_id=request.float_id)
        
        # Get float information
        if request.float_id:
            float_query = "SELECT * FROM argo_floats WHERE float_id = %s"
            float_results = db_manager.execute_query(float_query, (request.float_id,))
        elif request.platform_number:
            float_query = "SELECT * FROM argo_floats WHERE platform_number = %s"
            float_results = db_manager.execute_query(float_query, (request.platform_number,))
        else:
            raise HTTPException(status_code=400, detail="Either float_id or platform_number must be provided")
        
        if not float_results:
            raise HTTPException(status_code=404, detail="Float not found")
        
        float_data = float_results[0]
        
        # Create FloatInfo object
        float_info = FloatInfo(
            float_id=float_data['float_id'],
            platform_number=float_data.get('platform_number'),
            deployment_date=float_data.get('deployment_date'),
            deployment_latitude=float_data.get('deployment_latitude'),
            deployment_longitude=float_data.get('deployment_longitude'),
            float_type=float_data.get('float_type'),
            institution=float_data.get('institution'),
            status=float_data.get('status'),
            last_profile_date=float_data.get('last_profile_date'),
            total_profiles=float_data.get('total_profiles')
        )
        
        # Get profiles if requested
        profiles = None
        if request.include_profiles:
            profile_query = """
                SELECT profile_id, float_id, latitude, longitude, profile_date,
                       max_pressure, n_levels,
                       CASE WHEN dissolved_oxygen IS NOT NULL OR ph_in_situ IS NOT NULL 
                            OR nitrate IS NOT NULL OR chlorophyll_a IS NOT NULL 
                            THEN true ELSE false END as has_bgc_data
                FROM argo_profiles 
                WHERE float_id = %s 
                ORDER BY profile_date DESC 
                LIMIT %s
            """
            profile_results = db_manager.execute_query(
                profile_query, 
                (float_data['float_id'], request.profile_limit)
            )
            
            profiles = []
            for profile in profile_results:
                # Determine available parameters
                parameters_available = ['temperature', 'salinity']  # Always available
                if profile.get('has_bgc_data'):
                    parameters_available.extend(['dissolved_oxygen', 'ph_in_situ', 'nitrate', 'chlorophyll_a'])
                
                profile_summary = ProfileSummary(
                    profile_id=profile['profile_id'],
                    float_id=profile['float_id'],
                    latitude=profile['latitude'],
                    longitude=profile['longitude'],
                    profile_date=profile['profile_date'],
                    max_depth=profile.get('max_pressure'),  # Using max_pressure as depth proxy
                    parameters_available=parameters_available,
                    has_bgc_data=profile.get('has_bgc_data', False),
                    quality_flags={"status": "available"}  # Simplified for now
                )
                profiles.append(profile_summary)
        
        # Generate summary statistics
        summary_stats = {
            "total_profiles": float_info.total_profiles or 0,
            "date_range": {
                "first_profile": None,  # Would need additional query
                "last_profile": float_info.last_profile_date
            },
            "geographic_range": {
                "deployment_location": {
                    "latitude": float_info.deployment_latitude,
                    "longitude": float_info.deployment_longitude
                }
            },
            "data_availability": {
                "has_bgc": False  # Would need to check profiles
            }
        }
        
        return FloatInfoResponse(
            float_info=float_info,
            profiles=profiles,
            summary_stats=summary_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Float info request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Float info request failed: {str(e)}")


@router.get("/floats/list")
async def list_floats(
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    has_bgc: Optional[bool] = Query(default=None)
):
    """
    List ARGO floats with pagination and filters
    """
    try:
        # Build query
        query_parts = ["SELECT * FROM argo_floats"]
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if has_bgc is not None:
            if has_bgc:
                conditions.append("has_bgc_data = true")
            else:
                conditions.append("has_bgc_data = false")
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query_parts.append("ORDER BY last_profile_date DESC")
        query_parts.append(f"LIMIT {limit} OFFSET {offset}")
        
        sql_query = " ".join(query_parts)
        results = db_manager.execute_query(sql_query, tuple(params) if params else None)
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM argo_floats"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
        
        count_result = db_manager.execute_query(count_query, tuple(params) if params else None)
        total_count = count_result[0]['count'] if count_result else 0
        
        return {
            "floats": results,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_next": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error("Float listing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Float listing failed: {str(e)}")


@router.get("/parameters")
async def get_available_parameters():
    """
    Get list of available oceanographic parameters and their availability
    """
    try:
        # Get parameter availability statistics
        availability_query = """
        SELECT 
            COUNT(*) as total_profiles,
            COUNT(CASE WHEN temperature IS NOT NULL THEN 1 END) as temperature_count,
            COUNT(CASE WHEN salinity IS NOT NULL THEN 1 END) as salinity_count,
            COUNT(CASE WHEN dissolved_oxygen IS NOT NULL THEN 1 END) as dissolved_oxygen_count,
            COUNT(CASE WHEN ph_in_situ IS NOT NULL THEN 1 END) as ph_count,
            COUNT(CASE WHEN nitrate IS NOT NULL THEN 1 END) as nitrate_count,
            COUNT(CASE WHEN chlorophyll_a IS NOT NULL THEN 1 END) as chlorophyll_count,
            COUNT(CASE WHEN pressure IS NOT NULL THEN 1 END) as pressure_count,
            COUNT(CASE WHEN depth IS NOT NULL THEN 1 END) as depth_count
        FROM argo_profiles
        """
        
        stats = db_manager.execute_query(availability_query)[0]
        total = stats['total_profiles']
        
        parameters = {
            "core_parameters": [
                {
                    "name": "temperature",
                    "unit": "degrees Celsius",
                    "description": "Water temperature",
                    "availability_percent": round((stats['temperature_count'] / total) * 100, 1) if total > 0 else 0,
                    "profile_count": stats['temperature_count']
                },
                {
                    "name": "salinity", 
                    "unit": "PSU (Practical Salinity Units)",
                    "description": "Water salinity",
                    "availability_percent": round((stats['salinity_count'] / total) * 100, 1) if total > 0 else 0,
                    "profile_count": stats['salinity_count']
                },
                {
                    "name": "pressure",
                    "unit": "dbar",
                    "description": "Water pressure",
                    "availability_percent": round((stats['pressure_count'] / total) * 100, 1) if total > 0 else 0,
                    "profile_count": stats['pressure_count']
                },
                {
                    "name": "depth",
                    "unit": "meters",
                    "description": "Water depth",
                    "availability_percent": round((stats['depth_count'] / total) * 100, 1) if total > 0 else 0,
                    "profile_count": stats['depth_count']
                }
            ],
            "bgc_parameters": [
                {
                    "name": "dissolved_oxygen",
                    "unit": "μmol/kg",
                    "description": "Dissolved oxygen concentration",
                    "availability_percent": round((stats['dissolved_oxygen_count'] / total) * 100, 1) if total > 0 else 0,
                    "profile_count": stats['dissolved_oxygen_count']
                },
                {
                    "name": "ph_in_situ",
                    "unit": "pH units",
                    "description": "pH measured in situ",
                    "availability_percent": round((stats['ph_count'] / total) * 100, 1) if total > 0 else 0,
                    "profile_count": stats['ph_count']
                },
                {
                    "name": "nitrate",
                    "unit": "μmol/kg",
                    "description": "Nitrate concentration",
                    "availability_percent": round((stats['nitrate_count'] / total) * 100, 1) if total > 0 else 0,
                    "profile_count": stats['nitrate_count']
                },
                {
                    "name": "chlorophyll_a",
                    "unit": "mg/m³",
                    "description": "Chlorophyll-a concentration",
                    "availability_percent": round((stats['chlorophyll_count'] / total) * 100, 1) if total > 0 else 0,
                    "profile_count": stats['chlorophyll_count']
                }
            ],
            "summary": {
                "total_profiles": total,
                "core_parameter_availability": "95%+",
                "bgc_parameter_availability": f"{round((max(stats['dissolved_oxygen_count'], stats['ph_count'], stats['nitrate_count'], stats['chlorophyll_count']) / total) * 100, 1)}%" if total > 0 else "0%"
            }
        }
        
        return parameters
        
    except Exception as e:
        logger.error("Parameter availability check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Parameter availability check failed: {str(e)}")


@router.get("/regions")
async def get_geographic_regions():
    """
    Get available geographic regions with data coverage
    """
    try:
        # Get geographic coverage statistics
        region_query = """
        SELECT 
            CASE 
                WHEN latitude BETWEEN 10 AND 25 AND longitude BETWEEN 50 AND 80 THEN 'arabian_sea'
                WHEN latitude BETWEEN 5 AND 22 AND longitude BETWEEN 80 AND 100 THEN 'bay_of_bengal'
                WHEN latitude BETWEEN -60 AND 30 AND longitude BETWEEN 20 AND 120 THEN 'indian_ocean'
                WHEN latitude BETWEEN -5 AND 5 THEN 'equatorial'
                WHEN latitude < -60 THEN 'southern_ocean'
                ELSE 'other'
            END as region,
            COUNT(*) as profile_count,
            MIN(latitude) as min_lat,
            MAX(latitude) as max_lat,
            MIN(longitude) as min_lon,
            MAX(longitude) as max_lon,
            MIN(profile_date) as earliest_data,
            MAX(profile_date) as latest_data
        FROM argo_profiles 
        GROUP BY region
        ORDER BY profile_count DESC
        """
        
        region_stats = db_manager.execute_query(region_query)
        
        regions = []
        for stat in region_stats:
            if stat['region'] != 'other':  # Skip the catch-all category
                regions.append({
                    "name": stat['region'],
                    "display_name": stat['region'].replace('_', ' ').title(),
                    "profile_count": stat['profile_count'],
                    "geographic_bounds": {
                        "min_latitude": float(stat['min_lat']) if stat['min_lat'] else None,
                        "max_latitude": float(stat['max_lat']) if stat['max_lat'] else None,
                        "min_longitude": float(stat['min_lon']) if stat['min_lon'] else None,
                        "max_longitude": float(stat['max_lon']) if stat['max_lon'] else None
                    },
                    "temporal_coverage": {
                        "earliest_data": stat['earliest_data'],
                        "latest_data": stat['latest_data']
                    }
                })
        
        return {
            "regions": regions,
            "total_regions": len(regions),
            "coverage_notes": "Regions are automatically classified based on geographic coordinates"
        }
        
    except Exception as e:
        logger.error("Region information request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Region information request failed: {str(e)}")


@router.get("/recent")
async def get_recent_data(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=50, le=200)
):
    """
    Get most recent ARGO data
    """
    try:
        recent_query = """
        SELECT profile_id, float_id, latitude, longitude, profile_date,
               CASE WHEN dissolved_oxygen IS NOT NULL OR ph_in_situ IS NOT NULL 
                    OR nitrate IS NOT NULL OR chlorophyll_a IS NOT NULL 
                    THEN true ELSE false END as has_bgc_data,
               max_pressure
        FROM argo_profiles 
        WHERE profile_date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY profile_date DESC, created_at DESC 
        LIMIT %s
        """
        
        results = db_manager.execute_query(recent_query, (days, limit))
        
        return {
            "recent_profiles": results,
            "count": len(results),
            "days_back": days,
            "query_date": datetime.now().date()
        }
        
    except Exception as e:
        logger.error("Recent data request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Recent data request failed: {str(e)}")
    
@router.get("/metadata")
async def get_metadata():
    """Get system metadata for frontend"""
    try:
        stats = db_manager.get_database_stats()
        vector_stats = vector_db_manager.get_collection_stats()
        
        return {
            "dataset": stats,
            "vector_database": vector_stats,
            "parameters": settings.SUPPORTED_PARAMETERS,
            "regions": settings.OCEAN_REGIONS,
            "api_version": settings.APP_VERSION
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))