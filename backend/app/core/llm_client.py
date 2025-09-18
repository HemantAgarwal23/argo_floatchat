"""
llm_client.py
Groq LLM client for natural language processing and query generation
"""
from groq import Groq
from typing import Dict, Any, List, Optional
import json
import structlog
from app.config import settings

logger = structlog.get_logger()


class GroqLLMClient:
    """Manages Groq API interactions for ARGO AI backend"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.max_tokens = settings.GROQ_MAX_TOKENS
        self.temperature = settings.GROQ_TEMPERATURE
    
    def generate_response(self, messages: List[Dict[str, str]], 
                         temperature: Optional[float] = None,
                         max_tokens: Optional[int] = None) -> str:
        """Generate response using Groq API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Groq API call failed", error=str(e))
            raise
    
    def classify_query_type(self, user_query: str) -> Dict[str, Any]:
        """Classify whether query needs SQL retrieval, vector retrieval, or hybrid"""
        
        system_prompt = """You are an expert system for classifying oceanographic data queries for ARGO float data.

ARGO floats collect oceanographic data including:
- Temperature and salinity profiles
- Biogeochemical (BGC) parameters: dissolved oxygen, pH, nitrate, chlorophyll-a
- Geographic location and temporal data
- Float metadata and deployment information

ENTITY EXTRACTION - Extract ALL relevant terms:
- Geographic: "Bay of Bengal", "equatorial Pacific", "Arabian Sea", "equator"
- Parameters: "temperature", "salinity", "trajectories", "anomaly"  
- Temporal: "2022", "2023", "between 2022 and 2023"
- Profile IDs: "profile 1902681", "profile number 1902681"
- Float IDs: "float 1902681", "ARGO float 1902681"

Examples:
- "Show profile 1902681 trajectories" → sql_retrieval, extract profile_id: "1902681"
- "Float 1234567 temperature data" → sql_retrieval, extract float_id: "1234567"
Classify the user query into one of these categories:

1. **sql_retrieval**: Queries requesting specific data filtering, aggregation, or structured data extraction
   - Examples: "Show me salinity profiles near the equator in March 2023"
   - "What are the temperature readings for float 7900617?"
   - "Find profiles with dissolved oxygen > 5 mg/L"

2. **vector_retrieval**: Queries asking for patterns, summaries, or conceptual information
   - Examples: "Summarize ocean warming patterns in the Indian Ocean"
   - "What are the general characteristics of BGC data in the Arabian Sea?"
   - "Describe seasonal variations in chlorophyll levels"

3. **hybrid_retrieval**: Complex queries requiring both structured data and semantic understanding
   - Examples: "Compare BGC parameters in the Arabian Sea for the last 6 months"
   - "Analyze temperature trends near major ocean currents"
   - "What can you tell me about recent changes in the Southern Ocean?"

Respond with JSON format:
{
  "query_type": "sql_retrieval|vector_retrieval|hybrid_retrieval",
  "confidence": 0.8,
  "reasoning": "Brief explanation of classification",
  "extracted_entities": {
    "parameters": ["temperature", "salinity"],
    "locations": ["equator", "Arabian Sea"],
    "dates": ["March 2023", "last 6 months"],
    "float_ids": ["7900617"],
    "regions": ["Indian Ocean"]
  }
}"""

        user_message = f"Classify this oceanographic query: {user_query}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.generate_response(messages, temperature=0.1)
            
            # Try to parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse classification JSON", response=response)
                return {
                    "query_type": "vector_retrieval",
                    "confidence": 0.5,
                    "reasoning": "Failed to parse classification, defaulting to vector retrieval",
                    "extracted_entities": {}
                }
                
        except Exception as e:
            logger.error("Query classification failed", error=str(e))
            return {
                "query_type": "vector_retrieval",
                "confidence": 0.3,
                "reasoning": f"Classification error: {str(e)}",
                "extracted_entities": {}
            }
    
    def generate_sql_query(self, user_query: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query from natural language"""
        
        system_prompt = """You are an expert SQL generator for ARGO oceanographic database queries.

Database Schema:
```sql
-- Float metadata table
argo_floats (
    float_id text PRIMARY KEY,
    platform_number text,
    deployment_date date,
    deployment_latitude real,
    deployment_longitude real,
    float_type text,
    institution text,
    status text,
    last_profile_date date,
    total_profiles integer
)

-- Profile data table  
argo_profiles (
    profile_id text PRIMARY KEY,
    float_id text,
    cycle_number integer,
    latitude real,
    longitude real,
    profile_date date,
    profile_time time,
    julian_day real,
    position_qc integer,
    pressure real[],          -- Array of pressure values
    depth real[],             -- Array of depth values  
    temperature real[],       -- Array of temperature values
    salinity real[],          -- Array of salinity values
    temperature_qc integer[], -- Quality control flags
    salinity_qc integer[],    -- Quality control flags
    dissolved_oxygen real[],  -- BGC parameter
    ph_in_situ real[],        -- BGC parameter
    nitrate real[],           -- BGC parameter
    chlorophyll_a real[],     -- BGC parameter
    dissolved_oxygen_qc integer[],
    ph_qc integer[],
    nitrate_qc integer[],
    chlorophyll_qc integer[],
    platform_number text,
    project_name text,
    institution text,
    data_mode character(1),
    n_levels integer,
    max_pressure real
)
```

Important Notes:
- Oceanographic parameters are stored as arrays (pressure, depth, temperature, salinity, BGC parameters)
- Use array operations when needed: pressure[1], unnest(temperature), etc.
- Geographic searches: use latitude/longitude with BETWEEN or distance calculations
- Date searches: use profile_date with BETWEEN or date comparisons
- BGC data availability: check if arrays are NOT NULL
- Join tables when you need both float metadata and profile data

Generate a PostgreSQL query for the user request. Respond with JSON:
{
  "sql_query": "SELECT ... FROM ... WHERE ...",
  "explanation": "Brief explanation of what the query does",
  "estimated_results": "rough estimate of result size",
  "parameters_used": ["temperature", "salinity"]
}"""

        entities_text = json.dumps(entities, indent=2)
        user_message = f"""
Generate SQL query for: {user_query}

Extracted entities: {entities_text}

Consider geographic regions, date ranges, oceanographic parameters, and float IDs from the entities.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.generate_response(messages, temperature=0.1)
            result = json.loads(response)
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse SQL generation JSON", error=str(e))
            return {
                "sql_query": "SELECT * FROM argo_profiles LIMIT 10",
                "explanation": "Fallback query due to parsing error",
                "estimated_results": "10 profiles",
                "parameters_used": []
            }
        except Exception as e:
            logger.error("SQL generation failed", error=str(e))
            raise
    
    def get_system_prompt(self, query_type: str, result_count: int, has_arrays: bool) -> str:
        """Generate appropriate system prompt based on query characteristics"""
        
        base_rules = """You are a database query results interpreter for ARGO oceanographic data.

    ABSOLUTE RULES - NEVER BREAK THESE:
    1. Report ONLY what exists in the provided database results
    2. If a field contains NULL, None, or is missing - say "not available" 
    3. NEVER estimate, calculate, or invent any numerical values
    4. NEVER provide temperature, salinity, depth, or pressure values unless they explicitly appear in the database results
    5. If no oceanographic measurements exist, say so clearly"""

        # Adapt based on query characteristics
        if result_count == 0:
            specific_instructions = """
    RESPONSE STRUCTURE:
    - State clearly: "No data found matching your query"
    - Suggest alternative search terms or broader criteria
    - Do not provide any oceanographic analysis"""
        
        elif has_arrays and result_count > 1:
            # Check if this looks like year comparison data
            specific_instructions = """
    RESPONSE STRUCTURE:
    1. Report the number of profiles/records found
    2. For measurement arrays (temperature, salinity, pressure):
    - If arrays contain data: provide meaningful summaries like "Surface temperature: [first_value]°C, Deep temperature: [last_value]°C"
    - If arrays are NULL/empty: state "[parameter] measurements not available"
    3. Focus on what the actual data tells us about ocean conditions
    4. Never invent array values - only use what's in the database
    5. If data spans multiple years, group by year and compare conditions between years"""
        
        elif result_count == 1 and not has_arrays:
            specific_instructions = """
    RESPONSE STRUCTURE:
    1. Start with: "Based on the retrieved data, here's what I found:"
    2. State exactly how many records were found
    3. For each piece of data:
    - If present: report the exact value from database
    - If NULL/None/missing: state "[parameter] data is not available"
    4. End with what this means for the user's query"""
        
        elif result_count > 100:
            specific_instructions = """
    RESPONSE STRUCTURE:
    1. Start with: "Found [X] records matching your query"
    2. Provide summary statistics from the data (counts, ranges if available)
    3. Highlight key patterns or notable findings
    4. For large datasets, focus on aggregate insights rather than individual records
    5. Only mention specific values that appear in the database results"""
        
        
        else:
            specific_instructions = """
    RESPONSE STRUCTURE:
    1. Start with: "Based on the retrieved data, here's what I found:"
    2. State exactly how many records were found
    3. Summarize the key findings from the actual database results
    4. Provide context about what this means for the user's query"""

        do_not_rules = """
    DO NOT:
    - Describe oceanographic patterns if no measurement data exists
    - Mention specific temperatures/salinities/depths unless they're in the database results
    - Use phrases like "suggests", "indicates", "likely" when referring to non-existent data
    - Provide scientific interpretations of measurements that don't exist
    - Invent any numerical values or ranges"""

        return f"{base_rules}\n{specific_instructions}\n{do_not_rules}"


    def generate_final_response(self, user_query: str, retrieved_data: Dict[str, Any], 
                        query_type: str) -> str:
        """Generate final user-friendly response using retrieved data - ADAPTIVE VERSION"""

        # Analyze the retrieved data characteristics
        sql_results = retrieved_data.get('sql_results', [])
        result_count = len(sql_results)
        
        # Check if results contain array data
        has_arrays = False
        if sql_results:
            first_result = sql_results[0]
            array_fields = ['temperature', 'salinity', 'pressure', 'depth', 'dissolved_oxygen']
            has_arrays = any(field in first_result and first_result[field] is not None 
                            for field in array_fields)
        
        # Get appropriate system prompt
        system_prompt = self.get_system_prompt(query_type, result_count, has_arrays)
        
        # Add query-specific context
        system_prompt += f"""
        
    The user asked: "{user_query}"
    Query type: {query_type}

    Your job: Report exactly what the database contains, nothing more."""

        data_summary = self._summarize_data_for_llm(retrieved_data)
        user_message = f"""Retrieved database results: {data_summary}

    Report exactly what this data contains for the user's query. Do not add any analysis beyond what the actual data supports."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Adjust temperature based on query type
            temp = 0.1 if query_type == 'sql_retrieval' else 0.2
            response = self.generate_response(messages, temperature=temp)
            
            return response
        except Exception as e:
            logger.error("Final response generation failed", error=str(e))
            return f"Found data related to your query, but encountered an error processing it. Please try rephrasing your question."
        
    def _is_geographic_query_mismatch(self, user_query: str, retrieved_data: Dict[str, Any]) -> bool:
        """Check if a geographic query returned total database count instead of geographic subset"""
        
        # Check if this was a geographic query
        if not ('coordinates' in user_query.lower() or 'near' in user_query.lower()):
            return False
        
        sql_results = retrieved_data.get('sql_results', [])
        
        # Check if we got a suspiciously high count that suggests total database count
        if len(sql_results) == 1 and 'count' in sql_results[0]:
            count_value = sql_results[0]['count']
            
            # If count is very high (likely total database), this is a mismatch
            if count_value > 50000:
                return True
        
        return False
        
    def _summarize_data_for_llm(self, data: Dict[str, Any]) -> str:
        """Summarize retrieved data for LLM context with precise details"""
        summary_parts = []
        
        if 'sql_results' in data and data['sql_results']:
            sql_data = data['sql_results']
            # Handle COUNT queries specifically
            if len(sql_data) == 1 and 'count' in sql_data[0]:
                count_value = sql_data[0]['count']
                summary_parts.append(f"SQL COUNT QUERY RESULT: {count_value}")
                summary_parts.append(f"This is the exact count returned by the database query")
                return " || ".join(summary_parts)
            
            # Handle GROUP BY results (multiple rows with year/count pairs)
            elif all('year' in row and 'count' in row for row in sql_data):
                summary_parts.append("SQL GROUP BY QUERY RESULTS - YEARLY BREAKDOWN:")
                for row in sql_data:
                    year = int(row['year']) if hasattr(row['year'], '__int__') else row['year']
                    count = row['count']
                    summary_parts.append(f"Year {year}: {count} profiles")
                return " || ".join(summary_parts)
        
            # Handle regular data queries (existing code)
            summary_parts.append(f"Database Query Results: {len(sql_data)} records found")
            
            # For count results, be very explicit
            if len(sql_data) == 1 and 'count' in sql_data[0]:
                count_value = sql_data[0]['count']
                summary_parts.append(f"EXACT COUNT FROM DATABASE: {count_value}")
            
            # Provide detailed data for each record
            for i, record in enumerate(sql_data[:3]):  # Limit to first 3 for context
                record_summary = [f"Record {i+1}:"]
                
                # Essential fields
                if 'profile_id' in record:
                    record_summary.append(f"Profile ID: {record['profile_id']}")
                if 'float_id' in record:
                    record_summary.append(f"Float ID: {record['float_id']}")
                if 'latitude' in record and 'longitude' in record:
                    record_summary.append(f"Location: {record['latitude']}°N, {record['longitude']}°E")
                if 'profile_date' in record:
                    record_summary.append(f"Date: {record['profile_date']}")
                
                # Measurement data with exact values
                if 'temperature' in record and record['temperature']:
                    temp_values = record['temperature']
                    record_summary.append(f"Temperature measurements: {temp_values} °C")
                
                if 'salinity' in record and record['salinity']:
                    sal_values = record['salinity']
                    record_summary.append(f"Salinity measurements: {sal_values} PSU")
                
                if 'pressure' in record and record['pressure']:
                    press_values = record['pressure']
                    record_summary.append(f"Pressure measurements: {press_values} dbar")
                
                if 'depth' in record and record['depth']:
                    depth_values = record['depth']
                    record_summary.append(f"Depth measurements: {depth_values} meters")
                
                # BGC parameters
                bgc_params = []
                if record.get('dissolved_oxygen'):
                    bgc_params.append(f"Dissolved Oxygen: {record['dissolved_oxygen']}")
                if record.get('ph_in_situ'):
                    bgc_params.append(f"pH: {record['ph_in_situ']}")
                if record.get('nitrate'):
                    bgc_params.append(f"Nitrate: {record['nitrate']}")
                if record.get('chlorophyll_a'):
                    bgc_params.append(f"Chlorophyll-a: {record['chlorophyll_a']}")
                
                if bgc_params:
                    record_summary.append(f"BGC data: {', '.join(bgc_params)}")
                else:
                    record_summary.append("No BGC data available")
                
                summary_parts.append(" | ".join(record_summary))
        
        if 'vector_results' in data and data['vector_results']:
            vector_data = data['vector_results']
            summary_parts.append(f"Vector Search Results: {len(vector_data)} relevant summaries found")
            
            # Include key metadata from top results
            for i, result in enumerate(vector_data[:2]):  # Top 2 results
                metadata = result.get('metadata', {})
                doc_text = result.get('document', '')[:200]  # First 200 chars
                summary_parts.append(f"Vector Result {i+1}: {doc_text}...")
        
        if 'database_stats' in data:
            stats = data['database_stats']
            summary_parts.append(f"Database contains {stats.get('total_profiles', 0)} total profiles and {stats.get('total_floats', 0)} floats")
        
        return " || ".join(summary_parts)
    
    def _handle_geographic_query_mismatch(self, user_query: str, retrieved_data: Dict[str, Any]) -> str:
        """Handle cases where geographic query returned total database count"""
        
        sql_results = retrieved_data.get('sql_results', [])
        
        if sql_results and 'count' in sql_results[0]:
            total_count = sql_results[0]['count']
            
            return f"""The query was intended to find profiles near specific coordinates, but the database query appears to have returned the total count of all profiles in the database ({total_count:,}).

    This suggests that the geographic filtering was not applied correctly. The coordinate-based search needs to be refined.

    **Suggestions:**
    - Try rephrasing with more specific location terms
    - Use a broader geographic area (e.g., "in the Arabian Sea" instead of exact coordinates)
    - Check if the database contains coordinate data for the specified location

    **Database Status:** The system contains {total_count:,} total profiles, but geographic filtering for specific coordinates needs improvement."""

        return "Geographic query processing encountered an issue. Please try a different location format or broader geographic terms."

    def _validate_geographic_response(self, response: str, retrieved_data: Dict[str, Any], user_query: str) -> str:
        """Special validation for geographic queries to prevent hallucination"""
        
        sql_results = retrieved_data.get('sql_results', [])
        
        # Check if this was supposed to be a geographic query but returned total count
        if len(sql_results) == 1 and 'count' in sql_results[0]:
            count_value = sql_results[0]['count']
            
            # If the count is suspiciously high AND the response claims it's geographic, flag as error
            if count_value > 50000 and ('near' in response.lower() or 'coordinates' in response.lower()):
                return self._handle_geographic_query_mismatch(user_query, retrieved_data)
        
        return response


# Global LLM client instance (backward compatibility: keep Groq-specific client)
llm_client = GroqLLMClient()