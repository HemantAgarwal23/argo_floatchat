"""
vector_db.py
Vector database operations using ChromaDB for ARGO metadata and summaries
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import json
import os
import structlog
from sentence_transformers import SentenceTransformer
from app.config import settings

logger = structlog.get_logger()


class VectorDBManager:
    """Manages ChromaDB operations for ARGO metadata and summaries"""
    
    def __init__(self):
        self.persist_directory = settings.CHROMA_PERSIST_DIR
        self.embedding_model_name = settings.EMBEDDING_MODEL
        self.collection_name = "argo_metadata"
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Initialize ChromaDB client
        self._initialize_client()
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with persistence"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info("ChromaDB client initialized", persist_dir=self.persist_directory)
            
        except Exception as e:
            logger.error("Failed to initialize ChromaDB client", error=str(e))
            raise
    
    def _get_or_create_collection(self):
        """Get existing collection or create a new one"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(self.collection_name)
            logger.info("Retrieved existing ChromaDB collection", name=self.collection_name)
            return collection
        except:
            # Create new collection if it doesn't exist
            from chromadb.utils import embedding_functions
            
            # Use the default embedding function with our model
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model_name
            )
            
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "ARGO float metadata and summaries for semantic search"},
                embedding_function=embedding_function
            )
            logger.info("Created new ChromaDB collection", name=self.collection_name)
            return collection
    
    def add_metadata_summaries(self, summaries: List[Dict[str, Any]]) -> bool:
        """Add ARGO metadata summaries to vector database"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, summary in enumerate(summaries):
                # Create searchable text from summary
                text_content = self._create_searchable_text(summary)
                documents.append(text_content)
                
                # Prepare metadata (ChromaDB has limitations on nested objects)
                metadata = self._flatten_metadata(summary)
                metadatas.append(metadata)
                
                # Use profile_id as unique identifier, with fallback
                profile_id = summary.get('id', summary.get('profile_id', f"profile_{i}"))
                ids.append(str(profile_id))
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(summaries)} metadata summaries to vector database")
            return True
            
        except Exception as e:
            logger.error("Failed to add metadata summaries", error=str(e))
            return False
    
    def _create_searchable_text(self, summary: Dict[str, Any]) -> str:
        """Create searchable text from ARGO summary metadata"""
        text_parts = []
        
        # Add summary text
        if 'text' in summary:
            text_parts.append(summary['text'])
        
        # Add metadata information
        metadata = summary.get('metadata', {})
        
        # Location information
        if 'latitude' in metadata and 'longitude' in metadata:
            text_parts.append(f"Location: {metadata['latitude']}, {metadata['longitude']}")
        
        if 'region' in metadata:
            text_parts.append(f"Region: {metadata['region']}")
        
        # Date information
        if 'date' in metadata:
            text_parts.append(f"Date: {metadata['date']}")
        
        # Temperature information
        if 'surface_temperature' in metadata:
            text_parts.append(f"Surface temperature: {metadata['surface_temperature']}")
        if 'min_temperature' in metadata and 'max_temperature' in metadata:
            text_parts.append(f"Temperature range: {metadata['min_temperature']} to {metadata['max_temperature']}")
        
        # Salinity information
        if 'surface_salinity' in metadata:
            text_parts.append(f"Surface salinity: {metadata['surface_salinity']}")
        if 'min_salinity' in metadata and 'max_salinity' in metadata:
            text_parts.append(f"Salinity range: {metadata['min_salinity']} to {metadata['max_salinity']}")
        
        # Depth information
        if 'max_depth' in metadata:
            text_parts.append(f"Maximum depth: {metadata['max_depth']}")
        
        # BGC data
        if 'has_bgc' in metadata and metadata['has_bgc']:
            text_parts.append("Has biogeochemical data")
            
            bgc_params = []
            if metadata.get('has_oxygen'): bgc_params.append("dissolved oxygen")
            if metadata.get('has_ph'): bgc_params.append("pH")
            if metadata.get('has_nitrate'): bgc_params.append("nitrate")
            if metadata.get('has_chlorophyll'): bgc_params.append("chlorophyll")
            
            if bgc_params:
                text_parts.append(f"BGC parameters: {', '.join(bgc_params)}")
        
        # Float information
        if 'float_id' in metadata:
            text_parts.append(f"Float ID: {metadata['float_id']}")
        
        return " | ".join(text_parts)
    
    def _flatten_metadata(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested metadata for ChromaDB storage"""
        flattened = {}
        
        # Direct fields
        if 'id' in summary:
            flattened['id'] = str(summary['id'])
        
        # Flatten metadata
        metadata = summary.get('metadata', {})
        for key, value in metadata.items():
            # Convert all values to strings for ChromaDB compatibility
            if value is not None:
                flattened[key] = str(value)
        
        return flattened
    
    def semantic_search(self, query: str, limit: int = 10, 
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform semantic search on ARGO metadata"""
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        where_clause[key] = str(value)
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"Semantic search returned {len(formatted_results)} results", query=query)
            return formatted_results
            
        except Exception as e:
            logger.error("Semantic search failed", query=query, error=str(e))
            return []
    
    def search_by_region(self, region: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for profiles in a specific ocean region"""
        return self.semantic_search(
            query=f"ocean region {region}",
            limit=limit,
            filters={"region": region}
        )
    
    def search_by_parameter(self, parameter: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for profiles with specific oceanographic parameters"""
        query_map = {
            "temperature": "temperature measurements oceanographic data",
            "salinity": "salinity measurements ocean water",
            "dissolved_oxygen": "dissolved oxygen biogeochemical BGC",
            "ph": "pH acidity biogeochemical BGC",
            "nitrate": "nitrate nutrients biogeochemical BGC",
            "chlorophyll": "chlorophyll phytoplankton biogeochemical BGC"
        }
        
        query = query_map.get(parameter.lower(), f"{parameter} oceanographic measurements")
        return self.semantic_search(query, limit=limit)
    
    def search_by_date_range(self, start_date: str, end_date: str, 
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Search for profiles within a date range"""
        return self.semantic_search(
            query=f"ocean profile data from {start_date} to {end_date}",
            limit=limit
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database collection"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model_name
            }
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {}
    
    def load_metadata_from_json(self, json_file_path: str) -> bool:
        """Load metadata summaries from JSON file"""
        try:
            if not os.path.exists(json_file_path):
                logger.warning("JSON file not found", path=json_file_path)
                return False
            
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                summaries = data
            elif isinstance(data, dict) and 'summaries' in data:
                summaries = data['summaries']
            else:
                logger.error("Unexpected JSON structure", path=json_file_path)
                return False
            
            return self.add_metadata_summaries(summaries)
            
        except Exception as e:
            logger.error("Failed to load metadata from JSON", path=json_file_path, error=str(e))
            return False


# Global vector database manager instance
vector_db_manager = VectorDBManager()