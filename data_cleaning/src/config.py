"""
Configuration settings for ARGO data processing system
"""

import os
from pathlib import Path

class Config:
    """Configuration settings for ARGO data processing with environment variable support"""
    
    # Database configuration - use environment variables for security
    # Users should set DATABASE_URL environment variable with their credentials
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/argo_database')
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    RAW_NETCDF_PATH = PROJECT_ROOT / "data" / "raw_netcdf"
    PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
    LOGS_PATH = PROJECT_ROOT / "logs"
    
    # ARGO Data processing settings
    INDIAN_OCEAN_BOUNDS = {
        'lon_min': 20.0,   # 20°E
        'lon_max': 146.0,  # 146°E
        'lat_min': -60.0,  # 60°S
        'lat_max': 30.0    # 30°N
    }
    
    # Quality Control flags (1=good, 2=probably good)
    ACCEPTED_QC_FLAGS = [1, 2]
    
    # Julian date reference (ARGO uses days since 1950-01-01)
    JULIAN_REFERENCE_DATE = "1950-01-01"
    
    # Processing batch size
    BATCH_SIZE = 100
    
    @classmethod
    def ensure_directories(cls):
        """Create required directories for data processing"""
        cls.PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
        cls.LOGS_PATH.mkdir(parents=True, exist_ok=True)
