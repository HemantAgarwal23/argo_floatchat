"""
Database interface for ARGO data - Designed for chatbot integration
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import List, Dict, Any

class ARGODatabaseInterface:
    """Interface for ARGO database operations with chatbot integration"""
    
    def __init__(self, database_url: str):
        """Initialize database interface with connection string"""
        self.database_url = database_url
        self.connection = None
    
    def connect(self):
        """Connect to PostgreSQL database"""
        self.connection = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
        return True
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            self.connection.close()
    
    def search_by_location(self, lat_min: float, lat_max: float, 
                          lon_min: float, lon_max: float, limit: int = 100) -> List[Dict]:
        """Search profiles by geographic bounds"""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT profile_id, float_id, profile_date, latitude, longitude,
                       temperature[1] as surface_temp, salinity[1] as surface_sal
                FROM argo_profiles 
                WHERE latitude BETWEEN %s AND %s 
                AND longitude BETWEEN %s AND %s
                LIMIT %s
            """, (lat_min, lat_max, lon_min, lon_max, limit))
            return cursor.fetchall()
    
    def search_by_temperature(self, min_temp: float, max_temp: float, limit: int = 100) -> List[Dict]:
        """Search profiles by surface temperature"""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT profile_id, temperature[1] as surface_temp,
                       latitude, longitude, profile_date
                FROM argo_profiles 
                WHERE temperature[1] BETWEEN %s AND %s
                LIMIT %s
            """, (min_temp, max_temp, limit))
            return cursor.fetchall()
    
    def search_by_date_range(self, start_date: str, end_date: str, limit: int = 100) -> List[Dict]:
        """Search profiles by date range"""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT profile_id, profile_date, latitude, longitude,
                       temperature[1] as surface_temp, salinity[1] as surface_sal
                FROM argo_profiles 
                WHERE profile_date BETWEEN %s AND %s
                ORDER BY profile_date DESC
                LIMIT %s
            """, (start_date, end_date, limit))
            return cursor.fetchall()
    
    def get_profile_details(self, profile_id: str) -> Dict:
        """Get detailed data for specific profile"""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM argo_profiles WHERE profile_id = %s
            """, (profile_id,))
            return cursor.fetchone()
    
    def search_profiles_semantic(self, query_text: str, n_results: int = 10) -> List[Dict]:
        """Semantic search using metadata summaries"""
        try:
            with open('data/exports/argo_metadata_summaries.json', 'r') as f:
                summaries = json.load(f)
            
            # Simple keyword matching (replace with vector search in production)
            matches = []
            query_words = query_text.lower().split()
            
            for summary in summaries['summaries']:
                text_lower = summary['text'].lower()
                score = sum(1 for word in query_words if word in text_lower)
                if score > 0:
                    summary['relevance_score'] = score
                    matches.append(summary)
            
            # Sort by relevance and return top results
            matches.sort(key=lambda x: x['relevance_score'], reverse=True)
            return matches[:n_results]
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []

# Usage example
if __name__ == "__main__":
    # Test the interface
    DATABASE_URL = "postgresql://username:password@localhost:5432/argo_database"
    
    db = ARGODatabaseInterface(DATABASE_URL)
    db.connect()
    
    # Test geographic search
    arabian_sea = db.search_by_location(10, 25, 50, 75, limit=5)
    print(f"Found {len(arabian_sea)} profiles in Arabian Sea")
    
    # Test temperature search  
    warm_waters = db.search_by_temperature(28, 32, limit=5)
    print(f"Found {len(warm_waters)} warm water profiles")
    
    # Test semantic search
    results = db.search_profiles_semantic("warm tropical waters", n_results=3)
    print(f"Semantic search found {len(results)} relevant profiles")
    
    db.disconnect()
