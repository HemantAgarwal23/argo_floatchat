#!/usr/bin/env python3
"""
Startup script for ARGO FloatChat MCP Server
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.mcp_server import ARGOMCPServer

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('mcp_server.log')
        ]
    )

def check_requirements():
    """Check if all requirements are met"""
    try:
        # Check if MCP package is installed
        import mcp
        logging.info("✅ MCP package is installed")
        
        # Check if database is accessible
        from app.core.database import DatabaseManager
        db = DatabaseManager()
        stats = db.get_database_stats()
        logging.info(f"✅ Database accessible: {stats.get('total_profiles', 0)} profiles")
        
        # Check if other services are available
        from app.services.rag_pipeline import RAGPipeline
        from app.services.query_classifier import QueryClassifier
        from app.services.visualization_generator import VisualizationGenerator
        from app.core.llm_client import LLMClient
        
        logging.info("✅ All ARGO services are available")
        return True
        
    except ImportError as e:
        logging.error(f"❌ Missing required package: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Service check failed: {e}")
        return False

async def main():
    """Main entry point"""
    setup_logging()
    
    logging.info("🚀 Starting ARGO FloatChat MCP Server...")
    
    # Check requirements
    if not check_requirements():
        logging.error("❌ Requirements check failed. Exiting.")
        sys.exit(1)
    
    try:
        # Create and run MCP server
        server = ARGOMCPServer()
        await server.run()
        
    except KeyboardInterrupt:
        logging.info("🛑 Server stopped by user")
    except Exception as e:
        logging.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
