#!/usr/bin/env python3
"""
simple_database_setup.py
Simple database setup that creates tables if the dump fails
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import psycopg2
from app.config import settings
import structlog

logger = structlog.get_logger()

def create_tables_manually():
    """Create ARGO tables manually if dump fails"""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        with conn.cursor() as cur:
            # Create argo_floats table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS argo_floats (
                    float_id text PRIMARY KEY,
                    platform_number text,
                    deployment_date date,
                    deployment_latitude real,
                    deployment_longitude real,
                    float_type text,
                    institution text,
                    status text DEFAULT 'ACTIVE',
                    last_profile_date date,
                    total_profiles integer DEFAULT 0,
                    min_latitude real,
                    max_latitude real,
                    min_longitude real,
                    max_longitude real,
                    has_bgc_data boolean DEFAULT false,
                    created_at timestamp DEFAULT NOW(),
                    updated_at timestamp DEFAULT NOW()
                )
            """)
            
            # Create argo_profiles table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS argo_profiles (
                    profile_id text PRIMARY KEY,
                    float_id text,
                    cycle_number integer,
                    latitude real,
                    longitude real,
                    profile_date date,
                    profile_time time,
                    julian_day real,
                    position_qc integer,
                    pressure real[],
                    depth real[],
                    temperature real[],
                    salinity real[],
                    temperature_qc integer[],
                    salinity_qc integer[],
                    dissolved_oxygen real[],
                    ph_in_situ real[],
                    nitrate real[],
                    chlorophyll_a real[],
                    dissolved_oxygen_qc integer[],
                    ph_qc integer[],
                    nitrate_qc integer[],
                    chlorophyll_qc integer[],
                    platform_number text,
                    project_name text,
                    institution text,
                    data_mode character(1),
                    n_levels integer,
                    max_pressure real,
                    created_at timestamp DEFAULT NOW()
                )
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_float_id ON argo_profiles(float_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_date ON argo_profiles(profile_date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_location ON argo_profiles(latitude, longitude)")
            
            conn.commit()
            logger.info("Tables created successfully")
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error("Failed to create tables", error=str(e))
        return False

def insert_sample_data():
    """Insert some sample data for testing"""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        with conn.cursor() as cur:
            # Insert sample float
            cur.execute("""
                INSERT INTO argo_floats (float_id, platform_number, status, total_profiles)
                VALUES ('7900617', '7900617', 'ACTIVE', 1)
                ON CONFLICT (float_id) DO NOTHING
            """)
            
            # Insert sample profile
            cur.execute("""
                INSERT INTO argo_profiles (
                    profile_id, float_id, platform_number, latitude, longitude, 
                    profile_date, temperature, salinity, pressure, depth
                )
                VALUES (
                    'sample_profile_1', '7900617', '7900617', 15.5, 65.2, 
                    '2023-03-15', ARRAY[20.5, 18.2, 15.1], ARRAY[35.1, 35.3, 35.5],
                    ARRAY[0, 10, 20], ARRAY[0, 10, 20]
                )
                ON CONFLICT (profile_id) DO NOTHING
            """)
            
            conn.commit()
            logger.info("Sample data inserted")
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error("Failed to insert sample data", error=str(e))
        return False

def main():
    logger.info("Setting up database with manual table creation")
    
    if not create_tables_manually():
        return False
    
    if not insert_sample_data():
        return False
    
    logger.info("Database setup completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)