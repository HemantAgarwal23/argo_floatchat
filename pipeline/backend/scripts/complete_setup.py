#!/usr/bin/env python3
"""
Complete setup script for ARGO AI Backend
This script sets up everything needed to run the system
"""
import sys
import subprocess
from pathlib import Path
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def run_script(script_path, description):
    """Run a setup script and return success status"""
    try:
        logger.info(f"Running {description}")
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"{description} completed successfully")
            return True
        else:
            logger.error(f"{description} failed", 
                        error=result.stderr, 
                        stdout=result.stdout)
            return False
            
    except Exception as e:
        logger.error(f"{description} failed with exception", error=str(e))
        return False


def check_prerequisites():
    """Check if all prerequisites are installed"""
    logger.info("Checking prerequisites")
    
    # Check Python packages
    try:
        import fastapi
        import groq
        import chromadb
        import psycopg2
        import sentence_transformers
        logger.info("All required Python packages are installed")
    except ImportError as e:
        logger.error("Missing required package", package=str(e))
        logger.info("Please run: pip install -r requirements.txt")
        return False
    
    # Check PostgreSQL
    try:
        result = subprocess.run(['psql', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("PostgreSQL client found")
        else:
            logger.warning("PostgreSQL client not found - database setup may fail")
    except FileNotFoundError:
        logger.warning("PostgreSQL client not found - database setup may fail")
    
    return True


def main():
    """Main setup function"""
    logger.info("Starting complete ARGO AI Backend setup")
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites check failed")
        return False
    
    scripts_dir = Path(__file__).parent
    
    # Setup steps
    setup_steps = [
        (scripts_dir / "setup_database.py", "Database setup"),
        (scripts_dir / "setup_vector_db.py", "Vector database setup")
    ]
    
    success_count = 0
    total_steps = len(setup_steps)
    
    for script_path, description in setup_steps:
        if not script_path.exists():
            logger.error(f"Setup script not found", path=str(script_path))
            continue
            
        success = run_script(script_path, description)
        if success:
            success_count += 1
        else:
            logger.error(f"Setup step failed: {description}")
            # Ask user if they want to continue
            user_input = input(f"Continue with remaining setup steps? (y/N): ")
            if user_input.lower() != 'y':
                break
    
    # Final status
    if success_count == total_steps:
        logger.info("🎉 Complete setup finished successfully!")
        logger.info("You can now start the server with: python run.py")
        
        # Show next steps
        print("\n" + "="*60)
        print("SETUP COMPLETE!")
        print("="*60)
        print("\nNext steps:")
        print("1. Update your .env file with correct database credentials")
        print("2. Start the server: python run.py")
        print("3. Test the API at: http://localhost:8000/docs")
        print("4. Try a sample query: http://localhost:8000/api/v1/query")
        print("\nSample API usage:")
        print("curl -X POST 'http://localhost:8000/api/v1/query' \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{\"query\": \"Show me temperature profiles near the equator\"}'")
        print("\n" + "="*60)
        
        return True
    else:
        logger.error(f"Setup partially completed: {success_count}/{total_steps} steps successful")
        print("\n" + "="*60)
        print("SETUP PARTIALLY COMPLETED")
        print("="*60)
        print(f"\nCompleted: {success_count}/{total_steps} steps")
        print("\nPlease check the errors above and run individual setup scripts:")
        print("- Database: python scripts/setup_database.py")
        print("- Vector DB: python scripts/setup_vector_db.py")
        print("\n" + "="*60)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)