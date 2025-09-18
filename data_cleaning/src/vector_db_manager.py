"""
Vector Database Manager - Semantic search for ARGO data using ChromaDB and embeddings
"""

import os
import logging
import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from sentence_transformers import SentenceTransformer
from .config import Config

class VectorDBManager: 
    """Manages vector database for semantic search of ARGO oceanographic data"""
    
    def __init__(self):
        """Initialize vector database manager with ChromaDB and embeddings"""
        self.setup_logging()
        
        # Vector database configuration
        self.vector_db_path = Config.PROJECT_ROOT / "vector_db"
        self.collection_name = "argo_profiles"
        
        # Initialize database and ML components
        self.connection = None
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        
        self.setup_vector_db()
        self.setup_embedding_model()
    
    def setup_logging(self):
        """Setup logging configuration"""
        Config.ensure_directories()
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(Config.LOGS_PATH / 'vector_db.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_vector_db(self):
        """Initialize ChromaDB vector database"""
        try:
            # Create vector database directory
            Path(self.vector_db_path).mkdir(exist_ok=True)
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.vector_db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.collection_name
                )
                self.logger.info(f"✅ Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "ARGO oceanographic profile embeddings"}
                )
                self.logger.info(f"✅ Created new collection: {self.collection_name}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to setup vector database: {e}")
            raise
    
    def setup_embedding_model(self):
        """Initialize sentence transformer model for embeddings"""
        try:
            model_name = "all-MiniLM-L6-v2"
            self.embedding_model = SentenceTransformer(model_name)
            self.logger.info(f"✅ Loaded embedding model: {model_name}")
        except Exception as e:
            self.logger.error(f"❌ Failed to load embedding model: {e}")
            raise
    
    def connect_postgres(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(
                Config.DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            self.logger.info("✅ Connected to PostgreSQL database")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            return False
    
    def disconnect_postgres(self):
        """Disconnect from PostgreSQL database"""
        if self.connection:
            self.connection.close()
            self.logger.info("📝 Disconnected from PostgreSQL")
    
    def get_database_stats(self) -> dict:
        """Get database statistics for display"""
        try:
            if not self.connect_postgres():
                return {}
            
            with self.connection.cursor() as cursor:
                # Total profiles
                cursor.execute("SELECT COUNT(*) as count FROM argo_profiles")
                total_profiles = cursor.fetchone()['count']
                
                # Date range
                cursor.execute("SELECT MIN(profile_date) as min_date, MAX(profile_date) as max_date FROM argo_profiles")
                date_range = cursor.fetchone()
                
                # Column info
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'argo_profiles'
                """)
                columns = [row['column_name'] for row in cursor.fetchall()]
                
                stats = {
                    'total_profiles': total_profiles,
                    'min_date': date_range['min_date'],
                    'max_date': date_range['max_date'],
                    'columns': len(columns),
                    'column_names': columns[:10]  # First 10 columns
                }
                
                self.disconnect_postgres()
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    def safe_string_conversion(self, value: Any) -> str:
        """Safely convert any value to string, handling datetime objects"""
        if value is None:
            return ""
        elif isinstance(value, (date, datetime)):
            return value.strftime('%Y-%m-%d') if isinstance(value, date) else value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, (list, tuple)):
            return ', '.join([self.safe_string_conversion(item) for item in value])
        elif isinstance(value, np.ndarray):
            return ', '.join(map(str, value.tolist()))
        else:
            return str(value)
    
    def generate_profile_summary(self, profile_data: dict) -> str:
        """Generate a text summary from profile data for vectorization"""
        try:
            summary_parts = []
            
            # Essential fields to include in summary
            key_fields = [
                'profile_id', 'float_id', 'profile_date', 'latitude', 'longitude',
                'cycle_number', 'n_levels', 'max_pressure', 'platform_number'
            ]
            
            # Process key fields first
            for field in key_fields:
                if field in profile_data and profile_data[field] is not None:
                    value = profile_data[field]
                    safe_value = self.safe_string_conversion(value)
                    summary_parts.append(f"{field}: {safe_value}")
            
            # Add temperature and salinity ranges if available
            if 'temperature' in profile_data and profile_data['temperature'] is not None:
                temp_data = profile_data['temperature']
                if isinstance(temp_data, (list, np.ndarray)) and len(temp_data) > 0:
                    # Filter out None/null values
                    valid_temps = [t for t in temp_data if t is not None]
                    if valid_temps:
                        temp_range = f"{min(valid_temps):.2f} to {max(valid_temps):.2f}°C"
                        summary_parts.append(f"temperature_range: {temp_range}")
            
            if 'salinity' in profile_data and profile_data['salinity'] is not None:
                sal_data = profile_data['salinity']
                if isinstance(sal_data, (list, np.ndarray)) and len(sal_data) > 0:
                    # Filter out None/null values  
                    valid_sals = [s for s in sal_data if s is not None]
                    if valid_sals:
                        sal_range = f"{min(valid_sals):.2f} to {max(valid_sals):.2f} PSU"
                        summary_parts.append(f"salinity_range: {sal_range}")
            
            # Add depth information if available
            if 'depth' in profile_data and profile_data['depth'] is not None:
                depth_data = profile_data['depth']
                if isinstance(depth_data, (list, np.ndarray)) and len(depth_data) > 0:
                    valid_depths = [d for d in depth_data if d is not None]
                    if valid_depths:
                        depth_range = f"{min(valid_depths):.1f} to {max(valid_depths):.1f}m"
                        summary_parts.append(f"depth_range: {depth_range}")
            
            return " | ".join(summary_parts) if summary_parts else "Empty profile"
            
        except Exception as e:
            self.logger.error(f"Error generating summary for profile: {e}")
            return f"Error processing profile: {str(e)}"
    
    def fetch_sample_profiles(self, sample_size: int = 10) -> List[dict]:
        """Fetch a small sample of profiles for testing"""
        try:
            with self.connection.cursor() as cursor:
                query = """
                SELECT profile_id, float_id, cycle_number, profile_date, 
                       latitude, longitude, n_levels, max_pressure, 
                       platform_number, temperature, salinity, pressure, depth
                FROM argo_profiles 
                ORDER BY RANDOM()
                LIMIT %s
                """
                
                cursor.execute(query, (sample_size,))
                profiles = cursor.fetchall()
                
                return [dict(profile) for profile in profiles]
                
        except Exception as e:
            self.logger.error(f"Error fetching sample profiles: {e}")
            return []
    
    def fetch_profiles_batch(self, batch_size: int = 1000, offset: int = 0) -> List[dict]:
        """Fetch a batch of profiles from PostgreSQL"""
        try:
            with self.connection.cursor() as cursor:
                query = """
                SELECT profile_id, float_id, cycle_number, profile_date, 
                       latitude, longitude, n_levels, max_pressure, 
                       platform_number, temperature, salinity, pressure, depth
                FROM argo_profiles 
                ORDER BY profile_id 
                LIMIT %s OFFSET %s
                """
                
                cursor.execute(query, (batch_size, offset))
                profiles = cursor.fetchall()
                
                return [dict(profile) for profile in profiles]
                
        except Exception as e:
            self.logger.error(f"Error fetching profiles batch: {e}")
            return []
    
    def create_embeddings_batch(self, profiles: List[dict]) -> tuple:
        """Create embeddings for a batch of profiles"""
        try:
            if not profiles:
                return [], [], []
            
            # Generate summaries for all profiles
            summaries = []
            profile_ids = []
            metadatas = []
            
            for profile in profiles:
                try:
                    # Generate summary safely
                    summary = self.generate_profile_summary(profile)
                    summaries.append(summary)
                    
                    # Extract profile ID
                    profile_id = str(profile.get('profile_id', ''))
                    profile_ids.append(profile_id)
                    
                    # Create metadata (convert datetime objects safely)
                    metadata = {}
                    for key, value in profile.items():
                        if key not in ['temperature', 'salinity', 'pressure', 'depth']:  # Skip large arrays
                            safe_value = self.safe_string_conversion(value)
                            # ChromaDB metadata values must be strings, numbers, or booleans
                            if isinstance(value, (int, float, bool)):
                                metadata[key] = value
                            else:
                                metadata[key] = safe_value
                    
                    metadatas.append(metadata)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing profile {profile.get('profile_id', 'unknown')}: {e}")
                    continue
            
            if not summaries:
                return [], [], []
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(summaries, show_progress_bar=False)
            
            return embeddings.tolist(), profile_ids, metadatas
            
        except Exception as e:
            self.logger.error(f"Error creating embeddings batch: {e}")
            return [], [], []
    
    def add_embeddings_to_vector_db(self, embeddings: List[List[float]], 
                                  ids: List[str], metadatas: List[dict],
                                  documents: List[str]):
        """Add embeddings to ChromaDB collection"""
        try:
            if not embeddings or not ids:
                self.logger.warning("No embeddings or IDs to add")
                return False
            
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"✅ Added {len(embeddings)} embeddings to vector database")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error adding embeddings to vector database: {e}")
            return False
    
    def test_sample_processing(self, sample_size: int = 10) -> bool:
        """Test all processing steps with a small sample first"""
        try:
            print(f"\n🧪 Starting sample test with {sample_size} profiles...")
            
            # Connect to database
            if not self.connect_postgres():
                print("❌ Failed to connect to database")
                return False
            
            # Fetch sample profiles
            sample_profiles = self.fetch_sample_profiles(sample_size)
            if not sample_profiles:
                print("❌ No sample profiles found")
                return False
            
            print(f"📋 Fetched {len(sample_profiles)} sample profiles")
            
            # Test summary generation
            print("🔍 Testing summary generation...")
            for i, profile in enumerate(sample_profiles[:3]):
                summary = self.generate_profile_summary(profile)
                print(f"  Sample {i+1} summary: {summary[:80]}...")
            
            # Test embedding creation
            print("🧠 Testing embedding creation...")
            embeddings, ids, metadatas = self.create_embeddings_batch(sample_profiles)
            
            if not embeddings:
                print("❌ Failed to create embeddings")
                return False
            
            print(f"✅ Created {len(embeddings)} embeddings successfully")
            
            # Test vector database insertion
            print("💾 Testing vector database insertion...")
            documents = [self.generate_profile_summary(profile) for profile in sample_profiles]
            success = self.add_embeddings_to_vector_db(embeddings, ids, metadatas, documents)
            
            if not success:
                print("❌ Failed to add embeddings to vector database")
                return False
            
            print("✅ Added embeddings to vector database")
            
            # Test search functionality
            print("🔍 Testing search functionality...")
            test_query = "temperature profile"
            results = self.search_similar_profiles(test_query, n_results=3)
            
            if results and 'documents' in results and results['documents']:
                print(f"✅ Search test successful - found {len(results['documents'][0])} results")
                for i, doc in enumerate(results['documents'][0][:2]):
                    print(f"  Result {i+1}: {doc[:60]}...")
            else:
                print("⚠️ Search returned no results (this might be normal for small samples)")
            
            self.disconnect_postgres()
            print("🎉 Sample test completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Sample test failed: {e}")
            print(f"❌ Sample test failed: {e}")
            return False
    
    def process_all_profiles(self, batch_size: int = 100):
        """Process all profiles from PostgreSQL and add to vector database"""
        try:
            if not self.connect_postgres():
                return False
            
            # Get total count
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM argo_profiles")
                total_count = cursor.fetchone()['count']
            
            self.logger.info(f"📊 Processing {total_count:,} profiles in batches of {batch_size}")
            print(f"📊 Processing {total_count:,} profiles in batches of {batch_size}")
            
            processed_count = 0
            batch_num = 0
            
            while processed_count < total_count:
                batch_num += 1
                offset = processed_count
                
                self.logger.info(f"🔄 Processing batch {batch_num} (profiles {offset + 1} to {min(offset + batch_size, total_count)})")
                
                # Show progress
                if batch_num % 10 == 1 or batch_num <= 5:
                    print(f"🔄 Processing batch {batch_num}/{(total_count + batch_size - 1) // batch_size}")
                
                # Fetch batch
                profiles = self.fetch_profiles_batch(batch_size, offset)
                if not profiles:
                    break
                
                # Create embeddings
                embeddings, ids, metadatas = self.create_embeddings_batch(profiles)
                
                if embeddings:
                    # Generate documents (summaries for storage)
                    documents = [self.generate_profile_summary(profile) for profile in profiles]
                    
                    # Add to vector database
                    success = self.add_embeddings_to_vector_db(
                        embeddings, ids, metadatas, documents[:len(embeddings)]
                    )
                    
                    if success:
                        processed_count += len(embeddings)
                        
                        # Show progress every 10 batches
                        if batch_num % 10 == 0:
                            progress = (processed_count / total_count) * 100
                            print(f"✅ Progress: {processed_count:,}/{total_count:,} profiles ({progress:.1f}%)")
                    else:
                        self.logger.error(f"❌ Failed to add batch {batch_num} to vector database")
                else:
                    self.logger.warning(f"⚠️ No valid embeddings generated for batch {batch_num}")
                    processed_count += len(profiles)  # Skip this batch
            
            self.logger.info(f"🎉 Completed processing {processed_count} profiles")
            print(f"🎉 Completed processing {processed_count:,} profiles")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in process_all_profiles: {e}")
            print(f"❌ Error in process_all_profiles: {e}")
            return False
        finally:
            self.disconnect_postgres()
    
    def search_similar_profiles(self, query: str, n_results: int = 5) -> dict:
        """Search for similar profiles using semantic similarity"""
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query])
            
            # Search in vector database
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching similar profiles: {e}")
            return {}
    
    def get_collection_stats(self) -> dict:
        """Get statistics about the vector database collection"""
        try:
            count = self.collection.count()
            return {
                'total_profiles': count,
                'collection_name': self.collection_name
            }
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            return {}


def main():
    """Main function with interactive sample testing"""
    try:
        print("🚀 ARGO Vector Database Manager")
        print("=" * 50)
        
        # Initialize vector database manager
        vector_manager = VectorDBManager()
        
        # Get database statistics
        print("\n📊 Getting database statistics...")
        db_stats = vector_manager.get_database_stats()
        if db_stats:
            print(f"  📈 Total profiles: {db_stats.get('total_profiles', 'Unknown'):,}")
            print(f"  📅 Date range: {db_stats.get('min_date', 'Unknown')} to {db_stats.get('max_date', 'Unknown')}")
            print(f"  🏛️ Columns: {db_stats.get('columns', 'Unknown')} fields")
        
        # Check current collection stats
        stats = vector_manager.get_collection_stats()
        print(f"  🗂️ Current vector database: {stats.get('total_profiles', 0)} profiles")
        
        # Interactive menu
        print(f"\n🎯 Choose processing mode:")
        print("1. Test with sample data first (recommended)")
        print("2. Process full dataset immediately")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            # Test with sample first
            success = vector_manager.test_sample_processing(sample_size=10)
            
            if success:
                proceed = input("\n🤔 Sample test successful! Proceed with full dataset? (y/n): ").strip().lower()
                if proceed == 'y':
                    print("\n🚀 Starting full dataset processing...")
                    vector_manager.process_all_profiles(batch_size=50)
                else:
                    print("👍 Sample test completed. Full processing skipped.")
            else:
                print("❌ Sample test failed. Please check the logs for errors.")
                
        elif choice == "2":
            # Process full dataset immediately
            print("\n🚀 Starting full dataset processing...")
            success = vector_manager.process_all_profiles(batch_size=50)
            
        else:
            print("❌ Invalid choice. Exiting.")
            return
        
        # Final statistics
        final_stats = vector_manager.get_collection_stats()
        print(f"\n📊 Final vector database stats: {final_stats}")
        
        # Test search functionality
        print("\n🔍 Testing search functionality...")
        test_queries = [
            "warm tropical surface waters",
            "deep ocean temperature profiles", 
            "high salinity water"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = vector_manager.search_similar_profiles(query, n_results=2)
            
            if results and 'documents' in results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 'N/A'
                    print(f"  {i+1}. {doc[:80]}... (similarity: {1-distance:.3f})")
            else:
                print("  No results found")
        
        print("\n🎉 Vector database processing complete!")
            
    except Exception as e:
        logging.error(f"❌ Main execution failed: {e}")
        print(f"❌ Main execution failed: {e}")
        raise


if __name__ == "__main__":
    main()
