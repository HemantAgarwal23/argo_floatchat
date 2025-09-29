# app/models/requests.py

"""
Pydantic models for API requests
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date


class QueryRequest(BaseModel):
    """Main query request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="User's natural language query")
    max_results: Optional[int] = Field(default=10, ge=1, le=100, description="Maximum number of results")
    include_visualizations: Optional[bool] = Field(default=True, description="Include visualization suggestions")
    response_format: Optional[str] = Field(default="json", description="Response format: json, csv, netcdf")
    language: Optional[str] = Field(default="en", description="Response language code (e.g., 'en', 'es', 'fr', 'hi')")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class DataSearchRequest(BaseModel):
    """Request model for direct data searches"""
    parameters: Optional[List[str]] = Field(default=None, description="Oceanographic parameters to retrieve")
    start_date: Optional[date] = Field(default=None, description="Start date for temporal filtering")
    end_date: Optional[date] = Field(default=None, description="End date for temporal filtering")
    min_latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="Minimum latitude")
    max_latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="Maximum latitude")
    min_longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="Minimum longitude")
    max_longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="Maximum longitude")
    float_ids: Optional[List[str]] = Field(default=None, description="Specific float IDs to query")
    include_bgc: Optional[bool] = Field(default=False, description="Include only profiles with BGC data")
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    
    @validator('max_latitude')
    def validate_latitude_range(cls, v, values):
        if v is not None and 'min_latitude' in values and values['min_latitude'] is not None:
            if v <= values['min_latitude']:
                raise ValueError('max_latitude must be greater than min_latitude')
        return v
    
    @validator('max_longitude')
    def validate_longitude_range(cls, v, values):
        if v is not None and 'min_longitude' in values and values['min_longitude'] is not None:
            if v <= values['min_longitude']:
                raise ValueError('max_longitude must be greater than min_longitude')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class SemanticSearchRequest(BaseModel):
    """Request model for semantic/vector searches"""
    query: str = Field(..., min_length=1, max_length=500, description="Semantic search query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters for vector search")
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum number of results")
    similarity_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")


class FloatInfoRequest(BaseModel):
    """Request model for float information queries"""
    float_id: Optional[str] = Field(default=None, description="Specific float ID")
    platform_number: Optional[str] = Field(default=None, description="Platform number")
    include_profiles: Optional[bool] = Field(default=False, description="Include profile data")
    profile_limit: Optional[int] = Field(default=10, ge=1, le=100, description="Max profiles to include")


class ProfileAnalysisRequest(BaseModel):
    """Request model for profile analysis"""
    profile_ids: Optional[List[str]] = Field(default=None, description="Specific profile IDs")
    float_id: Optional[str] = Field(default=None, description="Analyze all profiles from a float")
    analysis_type: str = Field(default="summary", description="Type of analysis: summary, trends, comparison")
    parameters: Optional[List[str]] = Field(default=None, description="Parameters to analyze")
    
    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        allowed_types = ['summary', 'trends', 'comparison', 'quality_check']
        if v not in allowed_types:
            raise ValueError(f'analysis_type must be one of: {allowed_types}')
        return v


class BulkQueryRequest(BaseModel):
    """Request model for bulk queries"""
    queries: List[str] = Field(..., min_items=1, max_items=10, description="List of queries to process")
    max_results_per_query: Optional[int] = Field(default=5, ge=1, le=50, description="Max results per query")
    include_summaries: Optional[bool] = Field(default=True, description="Include query summaries")


class ExportRequest(BaseModel):
    """Request model for data export"""
    query: Optional[str] = Field(default=None, description="Query to determine export data")
    data_filters: Optional[DataSearchRequest] = Field(default=None, description="Direct data filters")
    export_format: str = Field(default="csv", description="Export format: csv, xlsx, json, png, docx")
    include_metadata: Optional[bool] = Field(default=True, description="Include metadata in export")
    
    @validator('export_format')
    def validate_export_format(cls, v):
        allowed_formats = ['csv', 'xlsx', 'json', 'png', 'docx']
        if v not in allowed_formats:
            raise ValueError(f'export_format must be one of: {allowed_formats}')
        return v


class FeedbackRequest(BaseModel):
    """Request model for user feedback"""
    query: str = Field(..., description="Original query")
    response_id: Optional[str] = Field(default=None, description="Response ID if available")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(default=None, description="Additional feedback text")
    issues: Optional[List[str]] = Field(default=None, description="Specific issues encountered")
    suggestions: Optional[str] = Field(default=None, description="Suggestions for improvement")