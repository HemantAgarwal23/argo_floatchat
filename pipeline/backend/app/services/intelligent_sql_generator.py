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
            # Debug logging
            logger.info(f"Processing query: {user_query}")
            
            # NEW: Detect "operating for X years" queries and handle them specially
            operating_phrases = ["operating for", "been operating", "operating more than", "operating less than"]
            has_operating_phrase = any(phrase in user_query.lower() for phrase in operating_phrases)
            logger.info(f"Has operating phrase: {has_operating_phrase}, phrases checked: {operating_phrases}")
            
            if has_operating_phrase:
                logger.info(f"Detected operating duration query: {user_query}")
                # Extract number of years from the query
                years_pattern = r'(\d+)\s*years?'
                years_match = re.search(years_pattern, user_query.lower())
                logger.info(f"Years match: {years_match}")
                
                if years_match:
                    years = int(years_match.group(1))
                    
                    # Check if it's "more than" or "less than"
                    if "more than" in user_query.lower() or "over" in user_query.lower():
                        comparison = ">"
                    elif "less than" in user_query.lower() or "under" in user_query.lower():
                        comparison = "<"
                    else:
                        comparison = ">="  # Default to "at least"
                    
                    return {
                        "sql_query": f"""
                        SELECT float_id,
                               MIN(profile_date) as first_profile_date,
                               MAX(profile_date) as last_profile_date,
                               COUNT(*) as total_profiles,
                               (MAX(profile_date) - MIN(profile_date)) as operating_duration
                        FROM argo_profiles 
                        WHERE profile_date IS NOT NULL
                        GROUP BY float_id
                        HAVING EXTRACT(EPOCH FROM AGE(MAX(profile_date), MIN(profile_date))) {comparison} {years * 365.25 * 24 * 3600}
                        ORDER BY operating_duration DESC
                        LIMIT 100
                        """,
                        "explanation": f"Floats operating {comparison} {years} years based on profile data",
                        "estimated_results": f"Floats with operating duration {comparison} {years} years",
                        "parameters_used": ["profile_date"],
                        "generation_method": "operating_duration_direct"
                    }
            
            # NEW: Detect year-based count queries and handle them specially
            if any(phrase in user_query.lower() for phrase in ["how many", "number of profiles", "profiles in"]) and any(year in user_query for year in ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]):
                # Extract years from the query
                year_pattern = r'\b(201[8-9]|202[0-5])\b'
                years = re.findall(year_pattern, user_query)
                
                if years:
                    years_int = [int(year) for year in years]
                    years_str = ', '.join(map(str, years_int))
                    
                    return {
                        "sql_query": f"""
                        SELECT EXTRACT(YEAR FROM profile_date) as year, 
                               COUNT(*) as count
                        FROM argo_profiles 
                        WHERE profile_date IS NOT NULL
                          AND EXTRACT(YEAR FROM profile_date) IN ({years_str})
                        GROUP BY EXTRACT(YEAR FROM profile_date)
                        ORDER BY year
                        """,
                        "explanation": f"Year-by-year profile counts for years: {years_str}",
                        "estimated_results": f"Profile counts for {len(years_int)} years",
                        "parameters_used": ["profile_date"],
                        "generation_method": "year_count_direct"
                    }
            
            # NEW: Detect "nearest floats" queries and handle them specially
            if any(phrase in user_query.lower() for phrase in ["nearest", "closest", "near"]) and any(coord in user_query.lower() for coord in ["°", "degrees", "north", "south", "east", "west"]):
                # Extract coordinates using regex
                coord_pattern = r'(\d+(?:\.\d+)?)\s*°?\s*([NS])\s*,\s*(\d+(?:\.\d+)?)\s*°?\s*([EW])'
                coord_match = re.search(coord_pattern, user_query, re.IGNORECASE)
                
                if coord_match:
                    lat_val = float(coord_match.group(1))
                    lat_dir = coord_match.group(2).upper()
                    lon_val = float(coord_match.group(3))
                    lon_dir = coord_match.group(4).upper()
                    
                    # Convert to decimal degrees
                    latitude = lat_val if lat_dir == 'N' else -lat_val
                    longitude = lon_val if lon_dir == 'E' else -lon_val
                    
                    return {
                        "sql_query": f"""
                        SELECT DISTINCT
                            p.float_id,
                            p.latitude,
                            p.longitude,
                            p.profile_date,
                            f.status,
                            f.float_type,
                            f.institution,
                            MIN(6371 * acos(
                                cos(radians({latitude})) * cos(radians(p.latitude)) * 
                                cos(radians(p.longitude) - radians({longitude})) + 
                                sin(radians({latitude})) * sin(radians(p.latitude))
                            )) AS distance_km
                        FROM argo_profiles p
                        LEFT JOIN argo_floats f ON p.float_id = f.float_id
                        WHERE p.latitude IS NOT NULL 
                          AND p.longitude IS NOT NULL
                          AND (6371 * acos(
                                cos(radians({latitude})) * cos(radians(p.latitude)) * 
                                cos(radians(p.longitude) - radians({longitude})) + 
                                sin(radians({latitude})) * sin(radians(p.latitude))
                              )) <= 500
                        GROUP BY p.float_id, p.latitude, p.longitude, p.profile_date, f.status, f.float_type, f.institution
                        ORDER BY distance_km ASC
                        LIMIT 10
                        """,
                        "explanation": f"Found nearest ARGO floats to coordinates {latitude}°N, {longitude}°E using distance calculation",
                        "estimated_results": "Up to 10 closest floats within 500km",
                        "parameters_used": ["latitude", "longitude"],
                        "generation_method": "nearest_floats_direct"
                    }
            
            # NEW: Detect explicit year vs year comparisons and build aggregation SQL directly
            year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', user_query)
            unique_years = sorted(list({int(y) for y in year_matches}))
            if len(unique_years) >= 2 and any(w in user_query.lower() for w in ["compare", "versus", "vs", "compare between"]):
                years_clause = ", ".join(str(y) for y in unique_years[:2])
                # Check if this is an equatorial query
                is_equatorial = any(term in user_query.lower() for term in ['equator', 'equatorial', 'near the equator'])
                
                if is_equatorial:
                    # Add equatorial filter (latitude between -5 and 5 degrees)
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
                    AND latitude BETWEEN -5 AND 5
                    AND temperature IS NOT NULL 
                    AND salinity IS NOT NULL
                    ORDER BY profile_date DESC
                    )
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
                    AND latitude BETWEEN -5 AND 5
                    AND temperature IS NOT NULL 
                    AND salinity IS NOT NULL
                    ORDER BY profile_date DESC
                    )
                    ORDER BY year DESC, profile_date DESC
                    """
                else:
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
                    )
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
                    )
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
- "Temperature profiles in Indian Ocean for last month" → SELECT profile_id, float_id, latitude, longitude, profile_date, temperature[1] as surface_temp, temperature[array_length(temperature,1)] as deep_temp FROM argo_profiles WHERE latitude BETWEEN -60 AND 30 AND longitude BETWEEN 20 AND 120 AND profile_date >= CURRENT_DATE - INTERVAL '1 month' AND temperature IS NOT NULL ORDER BY profile_date DESC LIMIT 100

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
            
            # Fix common array aggregation issues
            sql_query = self._fix_array_aggregation(sql_query)
            
            # Additional fix for the specific error pattern we're seeing
            sql_query = self._fix_temperature_array_issue(sql_query)
            
            # Fix table selection for location queries
            sql_query = self._fix_table_selection(sql_query, user_query)
            
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
    
    def _fix_table_selection(self, sql: str, user_query: str) -> str:
        """Fix table selection for location queries"""
        sql_lower = sql.lower()
        user_query_lower = user_query.lower()
        
        # Check if this is a location query that should use argo_profiles
        location_keywords = ["location", "coordinate", "latitude", "longitude", "equator", "near", "trajectory", "trajectories"]
        is_location_query = any(keyword in user_query_lower for keyword in location_keywords)
        
        # If it's a location query and uses argo_floats, fix it
        if is_location_query and "from argo_floats" in sql_lower:
            # Replace argo_floats with argo_profiles and add profile_id, profile_date
            sql = sql.replace("FROM argo_floats", "FROM argo_profiles")
            sql = sql.replace("SELECT float_id, latitude, longitude", "SELECT profile_id, float_id, latitude, longitude, profile_date")
            logger.info("Fixed table selection: changed argo_floats to argo_profiles for location query")
        
        return sql
    
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
        
        # Check for problematic aggregate functions on array columns
        array_columns = ['temperature', 'salinity', 'pressure', 'depth', 'dissolved_oxygen', 'ph_in_situ', 'nitrate', 'chlorophyll_a']
        for col in array_columns:
            # Check for AVG(col), SUM(col), etc. without unnest()
            if f'avg({col})' in sql_lower or f'sum({col})' in sql_lower:
                logger.error(f"Invalid SQL: aggregate function on array column {col}", sql=sql)
                return False
        
        return True
    
    def _fix_array_aggregation(self, sql: str) -> str:
        """Fix common array aggregation issues in SQL"""
        sql_lower = sql.lower()
        
        # Fix AVG(temperature) -> AVG(temperature[1]) for surface values
        array_columns = ['temperature', 'salinity', 'pressure', 'depth', 'dissolved_oxygen', 'ph_in_situ', 'nitrate', 'chlorophyll_a']
        
        for col in array_columns:
            # Replace AVG(col) with AVG(col[1]) for surface values
            sql = re.sub(f'avg\\({col}\\)', f'AVG({col}[1])', sql, flags=re.IGNORECASE)
            # Replace SUM(col) with SUM(col[1]) for surface values  
            sql = re.sub(f'sum\\({col}\\)', f'SUM({col}[1])', sql, flags=re.IGNORECASE)
            # Replace MIN(col) with MIN(col[1]) for surface values
            sql = re.sub(f'min\\({col}\\)', f'MIN({col}[1])', sql, flags=re.IGNORECASE)
            # Replace MAX(col) with MAX(col[1]) for surface values
            sql = re.sub(f'max\\({col}\\)', f'MAX({col}[1])', sql, flags=re.IGNORECASE)
        
        return sql
    
    def _fix_temperature_array_issue(self, sql: str) -> str:
        """Fix the specific temperature array issue we're seeing in logs"""
        # Fix patterns like: SELECT AVG(T1.temperature) FROM argo_profiles AS T1
        sql = re.sub(r'AVG\(T\d+\.temperature\)', 'AVG(T1.temperature[1])', sql, flags=re.IGNORECASE)
        sql = re.sub(r'AVG\([a-zA-Z_]+\.temperature\)', 'AVG(temperature[1])', sql, flags=re.IGNORECASE)
        
        # Also fix other aggregate functions
        sql = re.sub(r'SUM\(T\d+\.temperature\)', 'SUM(T1.temperature[1])', sql, flags=re.IGNORECASE)
        sql = re.sub(r'MIN\(T\d+\.temperature\)', 'MIN(T1.temperature[1])', sql, flags=re.IGNORECASE)
        sql = re.sub(r'MAX\(T\d+\.temperature\)', 'MAX(T1.temperature[1])', sql, flags=re.IGNORECASE)
        
        return sql
    
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