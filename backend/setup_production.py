#!/usr/bin/env python3
"""
Production Setup Script for ARGO AI Backend

This script sets up the backend for production deployment on Render.
It handles database initialization, vector database setup, and health checks.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.core.database import db_manager
from app.core.vector_db import vector_db_manager

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_environment():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'GROQ_API_KEY',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    try:
        if db_manager.test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def setup_database():
    """Set up the database schema and initial data"""
    print("🔧 Setting up database...")
    
    # Run database setup script
    if not run_command("python scripts/setup_database.py", "Database setup"):
        return False
    
    return True

def setup_vector_database():
    """Set up the vector database"""
    print("🔧 Setting up vector database...")
    
    # Run vector database setup script
    if not run_command("python scripts/setup_vector_db.py", "Vector database setup"):
        return False
    
    return True

def run_health_checks():
    """Run comprehensive health checks"""
    print("🔍 Running health checks...")
    
    try:
        # Test database
        db_stats = db_manager.get_database_stats()
        print(f"✅ Database stats: {db_stats}")
        
        # Test vector database
        vector_stats = vector_db_manager.get_collection_stats()
        print(f"✅ Vector database stats: {vector_stats}")
        
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Starting ARGO AI Backend Production Setup")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Setup vector database
    if not setup_vector_database():
        print("❌ Vector database setup failed")
        sys.exit(1)
    
    # Run health checks
    if not run_health_checks():
        print("❌ Health checks failed")
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 Production setup completed successfully!")
    print("✅ Backend is ready for deployment")
    print(f"🌐 Backend URL: {settings.HOST}:{settings.PORT}")
    print("📊 API Documentation: /docs")
    print("❤️ Health Check: /health")

if __name__ == "__main__":
    main()
