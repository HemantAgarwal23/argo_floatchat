#!/usr/bin/env python3
"""
setup_vector_db.py
Setup script to initialize ChromaDB vector database with ARGO metadata summaries
"""
import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.vector_db import vector_db_manager
import structlog

logger = structlog.get_logger()


def load_metadata_summaries():
    """Load metadata summaries from JSON file"""
    
    # Look for the JSON file in data/metadata_summaries/
    json_file = Path(__file__).parent.parent / "data" / "metadata_summaries" / "argo_metadata_summaries.json"
    
    if not json_file.exists():
        # Also check if it's in the root directory
        json_file = Path(__file__).parent.parent / "argo_metadata_summaries.json"
    
    if not json_file.exists():
        logger.error("Metadata summaries JSON file not found", expected_path=str(json_file))
        return None
    
    try:
        logger.info("Loading metadata summaries", file=str(json_file))
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            summaries = data
        elif isinstance(data, dict):
            # Check for common keys that might contain the summaries
            if 'summaries' in data:
                summaries = data['summaries']
            elif 'data' in data:
                summaries = data['data']
            elif 'profiles' in data:
                summaries = data['profiles']
            else:
                # If it's a dict with numeric keys, convert to list
                if all(str(k).isdigit() for k in data.keys()):
                    summaries = list(data.values())
                else:
                    logger.error("Unexpected JSON structure", keys=list(data.keys()))
                    return None
        else:
            logger.error("JSON data is not a list or dictionary", type=type(data))
            return None
        
        logger.info("Loaded metadata summaries", count=len(summaries))
        return summaries
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON file", error=str(e))
        return None
    except Exception as e:
        logger.error("Failed to load metadata summaries", error=str(e))
        return None


def validate_summaries(summaries):
    """Validate the structure of metadata summaries"""
    if not summaries:
        logger.error("No summaries to validate")
        return False
    
    logger.info("Validating summary structure")
    
    # Check first few summaries for expected structure
    sample_size = min(5, len(summaries))
    
    for i, summary in enumerate(summaries[:sample_size]):
        if not isinstance(summary, dict):
            logger.error(f"Summary {i} is not a dictionary", type=type(summary))
            return False
        
        # Check for required fields
        required_fields = ['id', 'text', 'metadata']
        missing_fields = []
        
        for field in required_fields:
            if field not in summary:
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Summary {i} missing fields", missing=missing_fields)
            # Try to fix common issues
            if 'id' not in summary:
                # Generate ID from other available fields
                if 'profile_id' in summary:
                    summary['id'] = summary['profile_id']
                elif 'metadata' in summary and 'profile_id' in summary['metadata']:
                    summary['id'] = summary['metadata']['profile_id']
                else:
                    summary['id'] = f"profile_{i}"
                    
            if 'text' not in summary:
                # Generate text from metadata
                summary['text'] = _generate_text_from_metadata(summary.get('metadata', {}))
            
            if 'metadata' not in summary:
                # Create minimal metadata
                summary['metadata'] = {"profile_id": summary.get('id', f"profile_{i}")}
    
    logger.info("Summary validation completed")
    return True


def _generate_text_from_metadata(metadata):
    """Generate searchable text from metadata"""
    text_parts = []
    
    if 'profile_id' in metadata:
        text_parts.append(f"Profile {metadata['profile_id']}")
    
    if 'float_id' in metadata:
        text_parts.append(f"from float {metadata['float_id']}")
    
    if 'latitude' in metadata and 'longitude' in metadata:
        text_parts.append(f"at location {metadata['latitude']}, {metadata['longitude']}")
    
    if 'date' in metadata:
        text_parts.append(f"on {metadata['date']}")
    
    if 'region' in metadata:
        text_parts.append(f"in {metadata['region']}")
    
    # Add parameter information
    params = []
    for param in ['temperature', 'salinity', 'dissolved_oxygen', 'ph', 'nitrate', 'chlorophyll']:
        if f"surface_{param}" in metadata or f"min_{param}" in metadata:
            params.append(param)
    
    if params:
        text_parts.append(f"with {', '.join(params)} data")
    
    return " ".join(text_parts) if text_parts else "ARGO float profile"


def initialize_vector_database():
    """Initialize the vector database"""
    try:
        logger.info("Initializing vector database")
        
        # Get collection stats to check if already populated
        stats = vector_db_manager.get_collection_stats()
        existing_docs = stats.get('total_documents', 0)
        
        if existing_docs > 0:
            logger.info("Vector database already has documents", count=existing_docs)
            user_input = input(f"Vector database already contains {existing_docs} documents. Recreate? (y/N): ")
            
            if user_input.lower() != 'y':
                logger.info("Skipping vector database initialization")
                return True
            
            # Clear existing collection
            logger.info("Clearing existing vector database")
            try:
                vector_db_manager.client.delete_collection(vector_db_manager.collection_name)
                vector_db_manager.collection = vector_db_manager._get_or_create_collection()
            except Exception as e:
                logger.warning("Failed to clear existing collection", error=str(e))
        
        logger.info("Vector database initialized")
        return True
        
    except Exception as e:
        logger.error("Vector database initialization failed", error=str(e))
        return False


def add_summaries_to_vector_db(summaries):
    """Add metadata summaries to vector database"""
    try:
        logger.info("Adding summaries to vector database", count=len(summaries))
        
        # Process summaries in batches
        batch_size = 100
        total_batches = (len(summaries) + batch_size - 1) // batch_size
        
        for i in range(0, len(summaries), batch_size):
            batch = summaries[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches}", size=len(batch))
            
            success = vector_db_manager.add_metadata_summaries(batch)
            
            if not success:
                logger.error(f"Failed to add batch {batch_num}")
                return False
        
        logger.info("All summaries added to vector database successfully")
        return True
        
    except Exception as e:
        logger.error("Failed to add summaries to vector database", error=str(e))
        return False


def verify_vector_db_setup():
    """Verify vector database setup"""
    try:
        logger.info("Verifying vector database setup")
        
        # Get final statistics
        stats = vector_db_manager.get_collection_stats()
        total_docs = stats.get('total_documents', 0)
        
        logger.info("Vector database statistics", 
                   total_documents=total_docs,
                   collection_name=stats.get('collection_name', ''),
                   embedding_model=stats.get('embedding_model', ''))
        
        if total_docs == 0:
            logger.error("No documents found in vector database")
            return False
        
        # Test search functionality
        logger.info("Testing search functionality")
        test_results = vector_db_manager.semantic_search("temperature ocean profile", limit=3)
        
        if test_results:
            logger.info("Search test successful", results_count=len(test_results))
            return True
        else:
            logger.error("Search test failed - no results returned")
            return False
            
    except Exception as e:
        logger.error("Vector database verification failed", error=str(e))
        return False


def main():
    """Main setup function"""
    logger.info("Starting vector database setup")
    
    # Step 1: Load metadata summaries
    summaries = load_metadata_summaries()
    if not summaries:
        logger.error("Failed to load metadata summaries")
        return False
    
    # Step 2: Validate summaries
    if not validate_summaries(summaries):
        logger.error("Summary validation failed")
        return False
    
    # Step 3: Initialize vector database
    if not initialize_vector_database():
        logger.error("Vector database initialization failed")
        return False
    
    # Step 4: Add summaries to vector database
    if not add_summaries_to_vector_db(summaries):
        logger.error("Failed to add summaries to vector database")
        return False
    
    # Step 5: Verify setup
    if not verify_vector_db_setup():
        logger.error("Vector database verification failed")
        return False
    
    logger.info("Vector database setup completed successfully")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)