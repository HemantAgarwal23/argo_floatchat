#!/usr/bin/env python3
"""
setup_database.py
Setup script to initialize PostgreSQL database with ARGO data
"""
import os
import sys
import subprocess
import gzip
import shutil
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from app.core.database import db_manager
import structlog

logger = structlog.get_logger()


def extract_sql_dump():
    """Extract the gzipped SQL dump file"""
    dump_file = Path(__file__).parent / "argo_database_20250914.sql.gz"
    extracted_file = Path(__file__).parent / "argo_database_20250914.sql"
    
    if not dump_file.exists():
        logger.error("SQL dump file not found", path=str(dump_file))
        return None
    
    logger.info("Extracting SQL dump file")
    
    try:
        with gzip.open(dump_file, 'rb') as f_in:
            with open(extracted_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info("SQL dump extracted successfully", path=str(extracted_file))
        return extracted_file
        
    except Exception as e:
        logger.error("Failed to extract SQL dump", error=str(e))
        return None


def check_database_connection():
    """Check if we can connect to the database"""
    try:
        connection_successful = db_manager.test_connection()
        if connection_successful:
            logger.info("Database connection successful")
            return True
        else:
            logger.error("Database connection failed")
            return False
    except Exception as e:
        logger.error("Database connection test failed", error=str(e))
        return False


def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        # Try to connect to postgres database to create our target database
        import psycopg2
        
        conn_params = {
            'host': settings.DB_HOST,
            'port': settings.DB_PORT,
            'database': 'postgres',  # Connect to default postgres database
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD
        }
        
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Check if database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.DB_NAME,))
            exists = cur.fetchone()
            
            if not exists:
                logger.info("Creating database", name=settings.DB_NAME)
                cur.execute(f"CREATE DATABASE {settings.DB_NAME}")
                logger.info("Database created successfully")
            else:
                logger.info("Database already exists", name=settings.DB_NAME)
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error("Failed to create database", error=str(e))
        return False


def load_sql_dump(sql_file_path):
    """Load the SQL dump into the database"""
    try:
        logger.info("Loading SQL dump into database", file=str(sql_file_path))
        
        # Build psql command
        cmd = [
            'psql',
            '-h', settings.DB_HOST,
            '-p', str(settings.DB_PORT),
            '-U', settings.DB_USER,
            '-d', settings.DB_NAME,
            '-f', str(sql_file_path)
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = settings.DB_PASSWORD
        
        # Execute psql command
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("SQL dump loaded successfully")
            return True
        else:
            logger.error("Failed to load SQL dump", 
                        error=result.stderr,
                        stdout=result.stdout)
            return False
            
    except Exception as e:
        logger.error("SQL dump loading failed", error=str(e))
        return False


def verify_data_loading():
    """Verify that data was loaded correctly"""
    try:
        logger.info("Verifying data loading")
        
        # Check if tables exist and have data
        stats = db_manager.get_database_stats()
        
        total_floats = stats.get('total_floats', 0)
        total_profiles = stats.get('total_profiles', 0)
        
        logger.info("Database statistics", 
                   total_floats=total_floats,
                   total_profiles=total_profiles)
        
        if total_floats > 0 and total_profiles > 0:
            logger.info("Data verification successful")
            return True
        else:
            logger.error("Data verification failed - no data found")
            return False
            
    except Exception as e:
        logger.error("Data verification failed", error=str(e))
        return False


def cleanup_extracted_file(sql_file_path):
    """Clean up the extracted SQL file"""
    try:
        if sql_file_path and sql_file_path.exists():
            sql_file_path.unlink()
            logger.info("Cleaned up extracted SQL file")
    except Exception as e:
        logger.warning("Failed to cleanup extracted file", error=str(e))


def main():
    """Main setup function"""
    logger.info("Starting database setup")
    
    # Step 1: Create database if it doesn't exist
    if not create_database_if_not_exists():
        logger.error("Database creation failed")
        return False
    
    # Step 2: Check database connection
    if not check_database_connection():
        logger.error("Cannot connect to database")
        return False
    
    # Step 3: Extract SQL dump
    sql_file_path = extract_sql_dump()
    if not sql_file_path:
        logger.error("SQL dump extraction failed")
        return False
    
    try:
        # Step 4: Load SQL dump
        if not load_sql_dump(sql_file_path):
            logger.error("SQL dump loading failed")
            return False
        
        # Step 5: Verify data loading
        if not verify_data_loading():
            logger.error("Data verification failed")
            return False
        
        logger.info("Database setup completed successfully")
        return True
        
    finally:
        # Step 6: Cleanup
        cleanup_extracted_file(sql_file_path)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)