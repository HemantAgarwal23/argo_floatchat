"""
responses.py
Pydantic models for API responses
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date


class QueryClassification(BaseModel):
    """Query classification results"""
    query_type: str
    confidence: float
    reasoning: str
    extracted_entities: Dict[str, Any]
    preprocessing_suggestions: List[str]


class VisualizationSuggestion(BaseModel):
    """Visualization suggestion"""
    type: str  # "map", "time_series", "profile", "scatter", "histogram"
    title: str
    description: str
    data_columns: List[str]
    config: Dict[str, Any]


class QueryMetadata(BaseModel):
    """Metadata about query processing"""
    query_type: str
    confidence: float
    data_sources_used: List[str]
    total_results: int
    processing_time_ms: Optional[float] = None
    sql_query: Optional[str] = None
    vector_search_query: Optional[str] = None


class QueryResponse(BaseModel):
    """Main query response model"""
    query: str
    answer: str
    classification: QueryClassification
    metadata: QueryMetadata
    data: Optional[Dict[str, Any]] = None
    visualizations: Optional[List[VisualizationSuggestion]] = None
    suggestions: Optional[List[str]] = None
    response_id: Optional[str] = None
    timestamp: datetime


class DataSearchResponse(BaseModel):
    """Response for direct data searches"""
    results: List[Dict[str, Any]]
    total_count: int
    filters_applied: Dict[str, Any]
    columns: List[str]
    metadata: Dict[str, Any]


class SemanticSearchResponse(BaseModel):
    """Response for semantic searches"""
    results: List[Dict[str, Any]]
    query: str
    total_results: int
    search_metadata: Dict[str, Any]


class FloatInfo(BaseModel):
    """Float information model"""
    float_id: str
    platform_number: Optional[str] = None
    deployment_date: Optional[date] = None
    deployment_latitude: Optional[float] = None
    deployment_longitude: Optional[float] = None
    float_type: Optional[str] = None
    institution: Optional[str] = None
    status: Optional[str] = None
    last_profile_date: Optional[date] = None
    total_profiles: Optional[int] = None


class ProfileSummary(BaseModel):
    """Profile summary model"""
    profile_id: str
    float_id: str
    latitude: float
    longitude: float
    profile_date: date
    max_depth: Optional[float] = None
    parameters_available: List[str]
    has_bgc_data: bool
    quality_flags: Dict[str, Any]


class FloatInfoResponse(BaseModel):
    """Response for float information queries"""
    float_info: FloatInfo
    profiles: Optional[List[ProfileSummary]] = None
    summary_stats: Dict[str, Any]


class ProfileData(BaseModel):
    """Detailed profile data model"""
    profile_id: str
    float_id: str
    metadata: Dict[str, Any]
    measurements: Dict[str, List[float]]
    quality_control: Dict[str, List[int]]
    location: Dict[str, float]
    timestamp: datetime


class ProfileAnalysisResponse(BaseModel):
    """Response for profile analysis"""
    analysis_type: str
    profiles_analyzed: int
    results: Dict[str, Any]
    statistics: Dict[str, Any]
    trends: Optional[Dict[str, Any]] = None
    quality_assessment: Optional[Dict[str, Any]] = None
    visualizations: Optional[List[VisualizationSuggestion]] = None


class DatabaseStats(BaseModel):
    """Database statistics model"""
    total_floats: int
    total_profiles: int
    date_range: Dict[str, Optional[date]]
    profiles_with_bgc: int
    latest_update: Optional[datetime] = None
    geographic_coverage: Dict[str, Any]
    parameter_availability: Dict[str, int]


class SystemHealth(BaseModel):
    """System health status"""
    database: bool
    vector_db: bool
    llm: bool
    overall: bool
    details: Dict[str, Any]
    timestamp: datetime


class BulkQueryResponse(BaseModel):
    """Response for bulk queries"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    results: List[QueryResponse]
    summary: Dict[str, Any]
    processing_time_ms: float


class ExportResponse(BaseModel):
    """Response for data export requests"""
    export_id: str
    format: str
    status: str  # "pending", "processing", "completed", "failed"
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    record_count: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: Optional[str] = None


class APIInfo(BaseModel):
    """API information model"""
    name: str
    version: str
    description: str
    endpoints: Dict[str, str]
    supported_parameters: List[str]
    ocean_regions: List[str]
    rate_limits: Dict[str, Any]
    documentation_url: str


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime


# Union types for different response scenarios
QueryResult = Union[QueryResponse, ErrorResponse]
DataResult = Union[DataSearchResponse, ErrorResponse]
FloatResult = Union[FloatInfoResponse, ErrorResponse]
AnalysisResult = Union[ProfileAnalysisResponse, ErrorResponse]