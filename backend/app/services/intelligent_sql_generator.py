"""
intelligent_sql_generator.py
Complete replacement for hardcoded SQL generation using LLM semantic understanding
"""
import re
from typing import Dict, Any, List, Optional
import structlog
from app.core.multi_llm_client import multi_llm_client
from app.config import settings

logger = structlog.get_logger()


class IntelligentSQLGenerator:
    """Generates SQL queries using LLM semantic understanding instead of hardcoded patterns"""
    
    def __init__(self):
        self.database_schema = self._get_database_schema()
    
    def _get_database_schema(self) -> str:
        """Get complete database schema for LLM context"""
        return """
        Database Schema for ARGO Oceanographic Data:
        
        Table: argo_floats
        - float_id (text, PRIMARY KEY) - Unique identifier for each ARGO float
        - platform_number (text) - Platform number identifier  
        - deployment_date (date) - When float was deployed
        - deployment_latitude (real) - Deployment latitude
        - deployment_longitude (real) - Deployment longitude
        - float_type (text) - Type of ARGO float
        - institution (text) - Operating institution
        - status (text) - Current status (ACTIVE, INACTIVE, etc.)
        - last_profile_date (date) - Date of most recent profile
        - total_profiles (integer) - Total number of profiles collected
        
        Table: argo_profiles  
        - profile_id (text, PRIMARY KEY) - Unique profile identifier
        - float_id (text) - References argo_floats.float_id
        - latitude (real) - Profile location latitude
        - longitude (real) - Profile location longitude
        - profile_date (date) - Date profile was collected
        - profile_time (time) - Time profile was collected
        - pressure (real[]) - Array of pressure measurements (dbar)
        - depth (real[]) - Array of depth measurements (meters)
        - temperature (real[]) - Array of temperature measurements (°C)
        - salinity (real[]) - Array of salinity measurements (PSU)
        - dissolved_oxygen (real[]) - Array of oxygen measurements (μmol/kg)
        - ph_in_situ (real[]) - Array of pH measurements
        - nitrate (real[]) - Array of nitrate measurements (μmol/kg)
        - chlorophyll_a (real[]) - Array of chlorophyll measurements (mg/m³)
        - max_pressure (real) - Maximum pressure in profile
        - n_levels (integer) - Number of measurement levels
        
        Geographic Regions:
        - Arabian Sea: latitude 10-25°N, longitude 50-80°E
        - Bay of Bengal: latitude 5-22°N, longitude 80-100°E  
        - Indian Ocean: latitude -60-30°N, longitude 20-120°E
        - Equatorial: latitude -5-5°N, any longitude
        - Southern Ocean: latitude <-60°N, any longitude
        """
    
    def generate_sql_from_query(self, user_query: str, entities: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate SQL using LLM semantic understanding - COMPLETELY FIXED VERSION"""
        
        try:
            # NEW: Detect explicit year vs year comparisons and build aggregation SQL directly
            year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', user_query)
            unique_years = sorted(list({int(y) for y in year_matches}))
            if len(unique_years) >= 2 and any(w in user_query.lower() for w in ["compare", "versus", "vs", "compare between"]):
                years_clause = ", ".join(str(y) for y in unique_years[:2])
                comparison_sql = f"""
                (SELECT 
                    EXTRACT(YEAR FROM profile_date) AS year,
                    profile_id,
                    float_id,
                    latitude,
                    longitude,
                    profile_date,
                    temperature[1] AS surface_temperature,
                    salinity[1] AS surface_salinity,
                    pressure[1] AS surface_pressure
                FROM argo_profiles
                WHERE EXTRACT(YEAR FROM profile_date) = {unique_years[1]}
                AND temperature IS NOT NULL 
                AND salinity IS NOT NULL
                ORDER BY profile_date DESC
                LIMIT 100)
                UNION ALL
                (SELECT 
                    EXTRACT(YEAR FROM profile_date) AS year,
                    profile_id,
                    float_id,
                    latitude,
                    longitude,
                    profile_date,
                    temperature[1] AS surface_temperature,
                    salinity[1] AS surface_salinity,
                    pressure[1] AS surface_pressure
                FROM argo_profiles
                WHERE EXTRACT(YEAR FROM profile_date) = {unique_years[0]}
                AND temperature IS NOT NULL 
                AND salinity IS NOT NULL
                ORDER BY profile_date DESC
                LIMIT 100)
                ORDER BY year DESC, profile_date DESC
                """
                return {
                    "sql_query": comparison_sql.strip(),
                    "explanation": f"Yearly comparison with oceanographic data for years: {', '.join(str(y) for y in unique_years[:2])}",
                    "estimated_results": "Profile data for requested years with surface measurements",
                    "parameters_used": ["profile_date", "temperature", "salinity"],
                    "generation_method": "year_comparison_direct"
                }

            # FIXED: Check for coordinate patterns BEFORE LLM call
            coordinate_patterns = [
            r'(\d+(?:\.\d+)?)[°\s]*([NS])\s*,?\s*(\d+(?:\.\d+)?)[°\s]*([EW])',  # 20N, 70E
            r'(\d+(?:\.\d+)?)\s*degrees?\s*([NS])\s*,?\s*(\d+(?:\.\d+)?)\s*degrees?\s*([EW])',  # 25 degrees North, 65 degrees East
            ]

            coord_match = None
            for pattern in coordinate_patterns:
                coord_match = re.search(pattern, user_query, re.IGNORECASE)
                if coord_match:
                    break
            if coord_match:
                lat_val = float(coord_match.group(1))
                lat_dir = coord_match.group(2)
                lon_val = float(coord_match.group(3))
                lon_dir = coord_match.group(4)
                
                # Convert to decimal degrees
                lat = lat_val if lat_dir == 'N' else -lat_val
                lon = lon_val if lon_dir == 'E' else -lon_val
                
                # Generate geographic SQL directly without LLM
                geographic_sql = f"""
                SELECT * FROM argo_profiles 
                WHERE latitude BETWEEN {lat-1} AND {lat+1} 
                AND longitude BETWEEN {lon-1} AND {lon+1}
                ORDER BY profile_date DESC 
                LIMIT 100
                """
                
                return {
                    "sql_query": geographic_sql.strip(),
                    "explanation": f"Geographic query for profiles near {lat}°N, {lon}°E",
                    "estimated_results": "Up to 100 profiles in geographic area",
                    "parameters_used": ["latitude", "longitude"],
                    "generation_method": "geographic_direct"
                }
            
            # Continue with LLM generation for non-coordinate queries
            system_prompt = f"""You are an expert SQL generator for ARGO oceanographic database queries.

{self.database_schema}

PROFILE/FLOAT ID HANDLING - CRITICAL RULES:

1. **Profile ID queries**: "Profile 1902681" → WHERE profile_id LIKE '1902681%'
2. **Float ID queries**: "Float 1902681" → WHERE float_id = '1902681'  
3. **NEVER ignore specific IDs mentioned by user**
4. **ALWAYS include exact ID constraints when user provides specific numbers**

CRITICAL GEOGRAPHIC CONSTRAINTS - ALWAYS APPLY THESE:

1. **Bay of Bengal**: latitude BETWEEN 5 AND 22 AND longitude BETWEEN 80 AND 100
2. **Arabian Sea**: latitude BETWEEN 10 AND 25 AND longitude BETWEEN 50 AND 80
3. **Equator/Equatorial**: latitude BETWEEN -5 AND 5
4. **Trajectories**: SELECT profile_id, float_id, latitude, longitude, profile_date

Generate ONLY the SQL query that directly answers the user's question.
Respond with a single SQL statement, nothing else.

Examples:
- "How many floats in Arabian Sea?" → SELECT COUNT(DISTINCT float_id) FROM argo_profiles WHERE latitude BETWEEN 10 AND 25 AND longitude BETWEEN 50 AND 80
- "How many profiles in 2023?" → SELECT COUNT(*) FROM argo_profiles WHERE EXTRACT(YEAR FROM profile_date) = 2023
- "Show profile number 1902681 trajectories as map coordinates" → SELECT profile_id, float_id, latitude, longitude, profile_date FROM argo_profiles WHERE profile_id LIKE '1902681%' ORDER BY profile_date DESC LIMIT 200
- "Float 1234567 temperature data" → SELECT profile_id, float_id, latitude, longitude, profile_date, temperature FROM argo_profiles WHERE float_id = '1234567' AND temperature IS NOT NULL ORDER BY profile_date DESC LIMIT 100
- "Bay of Bengal trajectories" → SELECT profile_id, float_id, latitude, longitude, profile_date FROM argo_profiles WHERE latitude BETWEEN 5 AND 22 AND longitude BETWEEN 80 AND 100 ORDER BY profile_date DESC LIMIT 200

CRITICAL RULES:
1. NEVER generate a query without ID constraints when user specifies profile/float numbers
2. NEVER ignore user-specified IDs
3. Use LIKE for profile_id (profile_id LIKE 'ID%') and = for float_id (float_id = 'ID')
"""
            
            user_message = f"Generate SQL for: {user_query}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Get SQL from LLM
            sql_response = multi_llm_client.generate_response(messages, temperature=0.1)
            
            # Clean the response to extract just the SQL
            sql_query = self._clean_sql_response(sql_response)
            
            # Validate the SQL
            if self._validate_sql(sql_query):
                return {
                    "sql_query": sql_query,
                    "explanation": f"Generated SQL to answer: {user_query}",
                    "estimated_results": "Variable based on query",
                    "parameters_used": self._extract_parameters(sql_query),
                    "generation_method": "intelligent_llm"
                }
            else:
                raise ValueError(f"Generated invalid SQL: {sql_query}")
            
        except Exception as e:
            logger.error("Intelligent SQL generation failed", error=str(e), query=user_query)
            
            # FIXED: Store user_query in a variable that's accessible in the exception scope
            query_for_fallback = user_query
            
            # Better fallback for coordinate queries
            if ('coordinate' in query_for_fallback.lower() or 
                'near' in query_for_fallback.lower() or 
                re.search(r'\d+[°\s]*[NS]', query_for_fallback)):
                
                return {
                    "sql_query": "SELECT COUNT(*) FROM argo_profiles WHERE latitude IS NOT NULL AND longitude IS NOT NULL",
                    "explanation": f"Fallback geographic query for: {query_for_fallback}",
                    "estimated_results": "Count of profiles with coordinates",
                    "parameters_used": ["latitude", "longitude"],
                    "error": str(e)
                }
            else:
                return {
                    "sql_query": "SELECT COUNT(*) FROM argo_profiles LIMIT 10",
                    "explanation": f"Fallback query due to generation error: {str(e)}",
                    "estimated_results": "10 profiles",
                    "parameters_used": [],
                    "error": str(e)
                }
    
    def _clean_sql_response(self, response: str) -> str:
        """Extract clean SQL from LLM response"""
        # Remove markdown code blocks
        response = re.sub(r'```sql\s*\n?', '', response)
        response = re.sub(r'```\s*$', '', response)
        
        # Remove extra whitespace and comments
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        cleaned_lines = [line for line in lines if not line.startswith('--')]
        
        return ' '.join(cleaned_lines).strip()
    
    def _validate_sql(self, sql: str) -> bool:
        """Basic SQL validation"""
        sql_lower = sql.lower()
        
        # Must start with SELECT
        if not sql_lower.strip().startswith('select'):
            return False
        
        # Must contain FROM
        if 'from' not in sql_lower:
            return False
        
        # Must reference valid tables
        valid_tables = ['argo_profiles', 'argo_floats']
        if not any(table in sql_lower for table in valid_tables):
            return False
        
        # No dangerous operations
        dangerous = ['drop', 'delete', 'insert', 'update', 'alter', 'create']
        if any(word in sql_lower for word in dangerous):
            return False
        
        return True
    
    def _extract_parameters(self, sql: str) -> List[str]:
        """Extract oceanographic parameters mentioned in SQL"""
        parameters = []
        param_columns = [
            'temperature', 'salinity', 'pressure', 'depth',
            'dissolved_oxygen', 'ph_in_situ', 'nitrate', 'chlorophyll_a'
        ]
        
        sql_lower = sql.lower()
        for param in param_columns:
            if param in sql_lower:
                parameters.append(param)
        
        return parameters


# Global intelligent SQL generator instance  
intelligent_sql_generator = IntelligentSQLGenerator()