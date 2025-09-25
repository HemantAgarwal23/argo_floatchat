"""
PostgreSQL Database Manager for ARGO Oceanographic Data

This module provides a comprehensive database interface for managing ARGO float
oceanographic data stored in PostgreSQL. It handles connection management,
query execution, and data retrieval operations for the ARGO AI Backend system.

Key Features:
- Connection pooling and management
- ARGO-specific query methods
- Data validation and error handling
- Performance optimization with prepared statements
- Support for complex oceanographic queries

Database Schema:
- argo_floats: Float metadata and deployment information
- argo_profiles: Individual profile measurements and parameters

Author: ARGO AI Team
Version: 1.0.0
"""

import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from contextlib import contextmanager
import structlog
from app.config import settings

# Configure structured logging
logger = structlog.get_logger()


class DatabaseManager:
    """
    PostgreSQL Database Manager for ARGO Oceanographic Data
    
    This class provides a high-level interface for interacting with the ARGO
    database. It manages connections, executes queries, and provides specialized
    methods for oceanographic data retrieval.
    
    The database contains two main tables:
    - argo_floats: Metadata about ARGO floats (deployment info, status, etc.)
    - argo_profiles: Individual oceanographic measurements and parameters
    
    Attributes:
        connection_params (dict): Database connection parameters
        _connection: Internal connection object (managed by context managers)
    """
    
    def __init__(self):
        """
        Initialize the database manager with connection parameters
        
        Loads database configuration from settings and prepares connection
        parameters for PostgreSQL database access.
        """
        self.connection_params = {
            'host': settings.DB_HOST,           # Database server hostname
            'port': settings.DB_PORT,           # Database server port
            'database': settings.DB_NAME,       # ARGO database name
            'user': settings.DB_USER,           # Database username
            'password': settings.DB_PASSWORD    # Database password
        }
        self._connection = None  # Connection object (managed by context managers)
    
    # =============================================================================
    # CONNECTION MANAGEMENT
    # =============================================================================
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        
        Provides safe database connection management with automatic cleanup.
        Ensures connections are properly closed and transactions are rolled back
        on errors.
        
        Yields:
            psycopg2.connection: Database connection object
            
        Raises:
            Exception: If connection fails or query execution fails
        """
        conn = None
        try:
            # Establish database connection using configured parameters
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except Exception as e:
            # Rollback any pending transactions on error
            if conn:
                conn.rollback()
            logger.error("Database connection error", error=str(e))
            raise
        finally:
            # Always close the connection to prevent leaks
            if conn:
                conn.close()
    
    def test_connection(self) -> bool:
        """
        Test database connectivity
        
        Performs a simple query to verify that the database is accessible
        and responsive. Used during application startup and health checks.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Simple test query to verify connectivity
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error("Database connection test failed", error=str(e))
            return False
    
    # =============================================================================
    # QUERY EXECUTION METHODS
    # =============================================================================
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries
        
        This is the primary method for executing database queries. It uses
        RealDictCursor to return results as dictionaries for easier access.
        
        Args:
            query (str): SQL SELECT query to execute
            params (Optional[Tuple]): Query parameters for prepared statements
            
        Returns:
            List[Dict[str, Any]]: Query results as list of dictionaries
            
        Raises:
            Exception: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                # Use RealDictCursor to return results as dictionaries
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(query, params)
                    results = cur.fetchall()
                    # Convert RealDictRow objects to regular dictionaries
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error("Query execution failed", query=query, error=str(e))
            raise
    
    def execute_query_df(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        Execute query and return results as pandas DataFrame
        
        Convenience method for data analysis workflows that require pandas
        DataFrames. Uses pandas.read_sql_query for efficient data loading.
        
        Args:
            query (str): SQL SELECT query to execute
            params (Optional[Tuple]): Query parameters for prepared statements
            
        Returns:
            pd.DataFrame: Query results as pandas DataFrame
            
        Raises:
            Exception: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                # Use pandas for efficient DataFrame creation
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error("DataFrame query execution failed", query=query, error=str(e))
            raise
    
    # ARGO-specific query methods
    
    def get_floats_by_region(self, min_lat: float, max_lat: float, 
                           min_lon: float, max_lon: float) -> List[Dict[str, Any]]:
        """Get floats within a geographic region"""
        query = """
        SELECT DISTINCT f.* FROM argo_floats f
        JOIN argo_profiles p ON f.float_id = p.float_id
        WHERE p.latitude BETWEEN %s AND %s 
        AND p.longitude BETWEEN %s AND %s
        """
        return self.execute_query(query, (min_lat, max_lat, min_lon, max_lon))
    
    def get_profiles_by_date_range(self, start_date: str, end_date: str, 
                                 limit: int = 1000) -> List[Dict[str, Any]]:
        """Get profiles within a date range"""
        query = """
        SELECT * FROM argo_profiles 
        WHERE profile_date BETWEEN %s AND %s
        ORDER BY profile_date DESC
        LIMIT %s
        """
        return self.execute_query(query, (start_date, end_date, limit))
    
    def get_profiles_by_location_and_date(self, lat: float, lon: float, 
                                        radius_km: float, start_date: str, 
                                        end_date: str) -> List[Dict[str, Any]]:
        """Get profiles near a location within date range"""
        # Using Haversine formula approximation for nearby profiles
        query = """
        SELECT *, 
               (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * 
                           cos(radians(longitude) - radians(%s)) + 
                           sin(radians(%s)) * sin(radians(latitude)))) AS distance_km
        FROM argo_profiles 
        WHERE profile_date BETWEEN %s AND %s
        HAVING distance_km <= %s
        ORDER BY distance_km, profile_date DESC
        """
        return self.execute_query(query, (lat, lon, lat, start_date, end_date, radius_km))
    
    def get_nearest_floats(self, lat: float, lon: float, max_distance_km: float = 500, 
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Get the nearest ARGO floats to a given coordinate using Haversine distance"""
        query = """
        SELECT DISTINCT
            p.float_id,
            p.latitude,
            p.longitude,
            p.profile_date,
            f.status,
            f.float_type,
            f.institution,
            MIN(6371 * acos(
                cos(radians(%s)) * cos(radians(p.latitude)) * 
                cos(radians(p.longitude) - radians(%s)) + 
                sin(radians(%s)) * sin(radians(p.latitude))
            )) AS min_distance_km
        FROM argo_profiles p
        LEFT JOIN argo_floats f ON p.float_id = f.float_id
        WHERE p.latitude IS NOT NULL 
          AND p.longitude IS NOT NULL
          AND (6371 * acos(
                cos(radians(%s)) * cos(radians(p.latitude)) * 
                cos(radians(p.longitude) - radians(%s)) + 
                sin(radians(%s)) * sin(radians(p.latitude))
              )) <= %s
        GROUP BY p.float_id, p.latitude, p.longitude, p.profile_date, f.status, f.float_type, f.institution
        ORDER BY min_distance_km ASC
        LIMIT %s
        """
        return self.execute_query(query, (lat, lon, lat, lat, lon, lat, max_distance_km, limit))
    
    def get_profiles_with_bgc_data(self, parameter: str = None) -> List[Dict[str, Any]]:
        """Get profiles that have BGC (biogeochemical) data"""
        if parameter == "dissolved_oxygen":
            condition = "dissolved_oxygen IS NOT NULL"
        elif parameter == "ph":
            condition = "ph_in_situ IS NOT NULL"
        elif parameter == "nitrate":
            condition = "nitrate IS NOT NULL"
        elif parameter == "chlorophyll":
            condition = "chlorophyll_a IS NOT NULL"
        else:
            condition = """(dissolved_oxygen IS NOT NULL OR ph_in_situ IS NOT NULL 
                          OR nitrate IS NOT NULL OR chlorophyll_a IS NOT NULL)"""
        
        query = f"""
        SELECT * FROM argo_profiles 
        WHERE {condition}
        ORDER BY profile_date DESC
        """
        return self.execute_query(query)
    
    def get_temperature_salinity_profiles(self, float_id: str = None, 
                                        profile_id: str = None) -> List[Dict[str, Any]]:
        """Get temperature and salinity profile data"""
        if profile_id:
            query = """
            SELECT profile_id, float_id, latitude, longitude, profile_date,
                   pressure, depth, temperature, salinity, 
                   temperature_qc, salinity_qc
            FROM argo_profiles 
            WHERE profile_id = %s
            """
            params = (profile_id,)
        elif float_id:
            query = """
            SELECT profile_id, float_id, latitude, longitude, profile_date,
                   pressure, depth, temperature, salinity,
                   temperature_qc, salinity_qc
            FROM argo_profiles 
            WHERE float_id = %s
            ORDER BY profile_date DESC
            """
            params = (float_id,)
        else:
            raise ValueError("Either float_id or profile_id must be provided")
        
        return self.execute_query(query, params)
    
    def search_floats_by_platform_number(self, platform_numbers: List[str]) -> List[Dict[str, Any]]:
        """Search floats by platform numbers"""
        placeholders = ','.join(['%s'] * len(platform_numbers))
        query = f"""
        SELECT * FROM argo_floats 
        WHERE platform_number IN ({placeholders})
        """
        return self.execute_query(query, tuple(platform_numbers))
    
    def get_recent_profiles(self, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """Get most recent profiles within specified days"""
        query = """
        SELECT * FROM argo_profiles 
        WHERE profile_date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY profile_date DESC, created_at DESC
        LIMIT %s
        """
        return self.execute_query(query, (days, limit))
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the database"""
        stats = {}
        
        # Count floats
        result = self.execute_query("SELECT COUNT(*) as count FROM argo_floats")
        stats['total_floats'] = result[0]['count']
        
        # Count profiles
        result = self.execute_query("SELECT COUNT(*) as count FROM argo_profiles")
        stats['total_profiles'] = result[0]['count']
        
        # Date range
        result = self.execute_query("""
            SELECT MIN(profile_date) as min_date, MAX(profile_date) as max_date 
            FROM argo_profiles
        """)
        stats['date_range'] = result[0]
        
        # BGC data availability
        result = self.execute_query("""
            SELECT COUNT(*) as count FROM argo_profiles 
            WHERE dissolved_oxygen IS NOT NULL OR ph_in_situ IS NOT NULL 
               OR nitrate IS NOT NULL OR chlorophyll_a IS NOT NULL
        """)
        stats['profiles_with_bgc'] = result[0]['count']
        
        return stats


# Global database manager instance
db_manager = DatabaseManager()