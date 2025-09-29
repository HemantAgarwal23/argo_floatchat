"""
Configuration Management for ARGO AI Backend

This module contains all configuration settings for the ARGO AI Backend system.
It uses Pydantic Settings to manage environment variables and provide type validation.
The configuration covers API settings, database connections, LLM providers, and data processing parameters.

Key Components:
- API Configuration: FastAPI server settings
- Database Configuration: PostgreSQL connection parameters
- LLM Configuration: Groq and Hugging Face API settings
- Vector Database: ChromaDB configuration for semantic search
- Query Processing: Parameters for data retrieval and processing
- ARGO Data: Oceanographic data specific settings

Author: ARGO AI Team
Version: 1.0.0
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """
    Central configuration class for ARGO AI Backend
    
    This class manages all application settings using Pydantic's BaseSettings,
    which automatically loads values from environment variables and .env files.
    All settings are type-validated and can be overridden via environment variables.
    
    Environment Variables:
        - GROQ_API_KEY: Required API key for Groq LLM service
        - DB_PASSWORD: Required PostgreSQL database password
        - HUGGINGFACE_API_KEY: Optional API key for Hugging Face fallback
    """
    
    # =============================================================================
    # API CONFIGURATION
    # =============================================================================
    # FastAPI server settings
    APP_NAME: str = "ARGO AI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True  # Set to False in production
    HOST: str = "127.0.0.1"  # Server host address
    PORT: int = 8000  # Server port number
    
    # =============================================================================
    # LLM PROVIDER CONFIGURATION
    # =============================================================================
    # Groq API Configuration (Primary LLM Provider)
    GROQ_API_KEY: str  # Required: Get from https://console.groq.com/
    GROQ_MODEL: str = "llama-3.1-8b-instant"  # Fast, efficient model for most queries
    GROQ_MAX_TOKENS: int = 2048  # Maximum tokens per response
    GROQ_TEMPERATURE: float = 0.1  # Low temperature for consistent, factual responses
    GROQ_HARD_TOKEN_LIMIT: int = 100  # Token threshold for switching to fallback provider
    
    # PostgreSQL Database Configuration
    DB_HOST: str = "localhost"  # Database server host
    DB_PORT: int = 5432  # PostgreSQL default port
    DB_NAME: str = "argo_database"  # Database name
    DB_USER: str = "jayansh"  # Database username
    DB_PASSWORD: str  # Required: Database password

    # Hugging Face Inference API Configuration (Fallback Provider)
    HUGGINGFACE_API_KEY: Optional[str] = None  # Optional: For fallback when Groq limits exceeded
    HUGGINGFACE_API_URL: str = "https://api-inference.huggingface.co/models/"
    HF_TEXT_MODEL: str = "microsoft/DialoGPT-small"  # Text generation model (smaller, more reliable)
    HF_CODE_MODEL: str = "microsoft/DialoGPT-small"  # Code generation model (same as text)
    HF_FALLBACK_MODEL: str = "distilgpt2"  # Ultimate fallback model (more reliable than gpt2)
    HF_MAX_TOKENS: int = 4096  # Higher token limit for complex queries
    HF_TEMPERATURE: float = 0.2  # Slightly higher temperature for more creative responses

    # LLM Provider Selection Logic
    PROVIDER_PRIMARY: str = "groq"  # Primary provider for most queries
    PROVIDER_FALLBACK: str = "huggingface"  # Fallback when primary fails or limits exceeded
    TOKEN_SELECTION_THRESHOLD: int = 100  # Switch to HF if estimated tokens > this value
    
    @property
    def DATABASE_URL(self) -> str:
        """
        Construct PostgreSQL database URL from individual components
        
        Returns:
            str: Complete database connection URL
        """
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # =============================================================================
    # VECTOR DATABASE CONFIGURATION
    # =============================================================================
    # ChromaDB settings for semantic search and vector operations
    VECTOR_DB_TYPE: str = "chroma"  # Vector database type (chroma or faiss)
    CHROMA_PERSIST_DIR: str = "./data/vector_db"  # Directory to store vector database
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Sentence transformer model for embeddings
    EMBEDDING_DIMENSION: int = 384  # Dimension of embedding vectors
    
    # =============================================================================
    # QUERY PROCESSING CONFIGURATION
    # =============================================================================
    # Parameters for data retrieval and processing
    MAX_SEARCH_RESULTS: int = 10  # Maximum number of results to return per query
    SIMILARITY_THRESHOLD: float = 0.7  # Minimum similarity score for vector search results
    SQL_QUERY_TIMEOUT: int = 30  # SQL query timeout in seconds
    
    # =============================================================================
    # ARGO OCEANOGRAPHIC DATA CONFIGURATION
    # =============================================================================
    # ARGO float data specific settings
    ARGO_DATE_FORMAT: str = "%Y-%m-%d"  # Standard date format for ARGO data
    
    # Supported oceanographic parameters that can be queried
    SUPPORTED_PARAMETERS: List[str] = [
        "temperature",      # Water temperature measurements
        "salinity",         # Salt concentration
        "pressure",         # Water pressure (depth indicator)
        "depth",           # Water depth
        "dissolved_oxygen", # Oxygen content in water
        "ph_in_situ",      # Acidity level
        "nitrate",         # Nutrient concentration
        "chlorophyll_a"    # Phytoplankton indicator
    ]
    
    # =============================================================================
    # GEOGRAPHIC VALIDATION CONFIGURATION
    # =============================================================================
    # Bounds for validating latitude and longitude coordinates
    MAX_LATITUDE: float = 90.0   # Maximum valid latitude (North Pole)
    MIN_LATITUDE: float = -90.0  # Minimum valid latitude (South Pole)
    MAX_LONGITUDE: float = 180.0 # Maximum valid longitude (International Date Line)
    MIN_LONGITUDE: float = -180.0 # Minimum valid longitude (International Date Line)
    
    # Ocean regions for geographic classification and filtering
    OCEAN_REGIONS: List[str] = [
        "indian_ocean",     # Indian Ocean region
        "pacific_ocean",    # Pacific Ocean region
        "atlantic_ocean",   # Atlantic Ocean region
        "southern_ocean",   # Southern Ocean region
        "arctic_ocean",     # Arctic Ocean region
        "arabian_sea",      # Arabian Sea sub-region
        "bay_of_bengal",    # Bay of Bengal sub-region
        "mediterranean_sea" # Mediterranean Sea sub-region
    ]
    
    class Config:
        """Pydantic configuration settings"""
        env_file = ".env"  # Load environment variables from .env file
        case_sensitive = True  # Environment variable names are case-sensitive


# =============================================================================
# GLOBAL CONFIGURATION INSTANCE
# =============================================================================
# Create global settings instance that can be imported throughout the application
settings = Settings()


# =============================================================================
# QUERY TYPE CLASSIFICATIONS
# =============================================================================
class QueryTypes:
    """
    Enumeration of query types for the RAG pipeline
    
    The system classifies user queries into different types to determine
    the most appropriate data retrieval strategy.
    """
    SQL_RETRIEVAL = "sql_retrieval"        # Direct SQL database queries
    VECTOR_RETRIEVAL = "vector_retrieval"  # Semantic search using embeddings
    HYBRID_RETRIEVAL = "hybrid_retrieval"  # Combination of SQL and vector search
    
    @classmethod
    def all_types(cls):
        """Return all available query types"""
        return [cls.SQL_RETRIEVAL, cls.VECTOR_RETRIEVAL, cls.HYBRID_RETRIEVAL]


# =============================================================================
# RESPONSE FORMAT OPTIONS
# =============================================================================
class ResponseFormats:
    """
    Available response formats for data export and visualization
    
    Users can request data in different formats depending on their needs.
    """
    JSON = "json"              # JSON format for API responses
    CSV = "csv"                # CSV format for spreadsheet applications
    NETCDF = "netcdf"          # NetCDF format for scientific data analysis
    VISUALIZATION = "visualization"  # Interactive visualizations and maps