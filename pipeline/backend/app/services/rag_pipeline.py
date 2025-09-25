"""
rag_pipeline.py
Complete RAG (Retrieval-Augmented Generation) pipeline for ARGO queries
"""
from typing import Dict, Any, List, Optional
import asyncio
import re
import structlog
from app.core.database import db_manager
from app.core.vector_db import vector_db_manager
from app.core.multi_llm_client import multi_llm_client
from app.services.query_classifier import query_classifier
from app.services.geographic_validator import GeographicValidator
from app.config import settings, QueryTypes
from app.services.visualization_generator import visualization_generator

logger = structlog.get_logger()


class RAGPipeline:
    """Complete RAG pipeline for ARGO oceanographic data queries"""
    
    def __init__(self):
        self.max_sql_results = settings.MAX_SEARCH_RESULTS
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.geographic_validator = GeographicValidator()
    
    async def process_query(self, user_query: str, max_results: int = None) -> Dict[str, Any]:
        """Main RAG pipeline processing method"""
        try:
            max_results = max_results or self.max_sql_results
            
            logger.info("Starting RAG pipeline", query=user_query)
            
            # Step 1: Classify the query
            classification = query_classifier.classify_query(user_query)
            
            # Step 1.5: Check if user is asking about data coverage
            if any(phrase in user_query.lower() for phrase in ["what data", "data coverage", "ocean regions", "available data", "what oceans"]):
                coverage_info = self.geographic_validator.get_coverage_info()
                return {
                    "answer": f"Our ARGO float database contains {coverage_info['total_profiles']:,} profiles from the {coverage_info['description']}. "
                             f"Longitude range: {coverage_info['longitude_range'][0]}°E to {coverage_info['longitude_range'][1]}°E, "
                             f"Latitude range: {coverage_info['latitude_range'][0]}°S to {coverage_info['latitude_range'][1]}°N. "
                             f"We do not have data for the Atlantic Ocean, Pacific Ocean, Arctic Ocean, or Mediterranean Sea.",
                    "classification": {"query_type": "coverage_info"},
                    "data": {"records": []},
                    "visualization": {},
                    "response_id": "coverage_info"
                }
            
            # Step 1.6: Validate geographic coverage to prevent hallucination
            geographic_validation = self.geographic_validator.validate_geographic_coverage(user_query)
            if not geographic_validation['is_valid']:
                logger.warning("Query requests data from unavailable ocean regions", 
                             unavailable_regions=geographic_validation['unavailable_regions'],
                             available_regions=geographic_validation['available_regions'])
                return {
                    "answer": geographic_validation['message'],
                    "classification": classification,
                    "data": {"records": []},
                    "visualization": {},
                    "response_id": "geographic_validation_failed"
                }
            
            # Force SQL retrieval for ALL data queries to prevent hallucination
            # Only use vector search for pure informational questions, not data requests
            if any(k in user_query.lower() for k in ["show", "find", "get", "list", "display", "float", "data", "profile", "temperature", "salinity", "trajectory", "trajectories", "location", "coordinates", "map", "bay", "ocean", "sea", "equator", "near"]):
                logger.info("Forcing SQL retrieval for data query to prevent hallucination")
                classification['query_type'] = QueryTypes.SQL_RETRIEVAL
                classification['confidence'] = 1.0
                classification['reasoning'] = "Forced SQL retrieval for data query to prevent hallucination"
            
            # Step 2: Retrieve relevant data based on classification
            retrieved_data = await self._retrieve_data(user_query, classification, max_results)
            
            # Step 3: Generate final response
            final_response = await self._generate_response(user_query, classification, retrieved_data)
            logger.info(f"Generated final response: {len(final_response) if final_response else 0} characters")
            
            # Step 4: Prepare complete result
            result = {
                "success": True,
                "query": user_query,
                "classification": classification,
                "retrieved_data": retrieved_data,
                "response": final_response,
                "visualization": {},
                "metadata": {
                    "query_type": classification['query_type'],
                    "confidence": classification['confidence'],
                    "data_sources_used": self._get_data_sources_used(retrieved_data),
                    "total_results": self._count_total_results(retrieved_data)
                }
            }
            
            logger.info("RAG pipeline completed successfully", 
                       query_type=classification['query_type'],
                       total_results=result['metadata']['total_results'])
            
            # If visualization-related query OR year comparison, attach visualization payload
            should_generate_visualization = (
                any(k in user_query.lower() for k in ["map", "coordinates", "visualization", "plot", "geojson", "trajectory", "trajectories"]) or
                (retrieved_data.get('generation_method') == 'year_comparison_direct' and retrieved_data.get('sql_results'))
            )
            
            if should_generate_visualization:
                try:
                    logger.info("Generating visualization...")
                    # Use sql_results if available, otherwise use vector_results
                    results_for_visualization = retrieved_data.get('sql_results', [])
                    if not results_for_visualization:
                        # Convert vector results to format expected by visualization generator
                        vector_results = retrieved_data.get('vector_results', [])
                        results_for_visualization = []
                        for vector_result in vector_results:
                            metadata = vector_result.get('metadata', {})
                            if metadata.get('latitude') and metadata.get('longitude'):
                                results_for_visualization.append({
                                    'latitude': float(metadata['latitude']),
                                    'longitude': float(metadata['longitude']),
                                    'profile_date': metadata.get('date'),
                                    'profile_id': metadata.get('profile_id'),
                                    'float_id': metadata.get('float_id')
                                })
                    logger.info(f"Generated {len(results_for_visualization)} visualization data points")
                    result["visualization"] = visualization_generator.build_visualization_payload(results_for_visualization)
                    logger.info("Visualization generation completed successfully")
                except Exception as e:
                    logger.error("Visualization generation failed", error=str(e))
                    import traceback
                    traceback.print_exc()
                    result["visualization"] = {"error": str(e)}

            return result
            
        except Exception as e:
            logger.error("RAG pipeline failed", query=user_query, error=str(e))
            import traceback
            traceback.print_exc()
            return self._create_error_response(user_query, str(e))
    
    async def _retrieve_data(self, query: str, classification: Dict[str, Any], 
                           max_results: int) -> Dict[str, Any]:
        """Retrieve data based on query classification"""
        
        query_type = classification['query_type']
        entities = classification.get('extracted_entities', {})
        
        retrieved_data = {
            "sql_results": [],
            "vector_results": [],
            "hybrid_results": {},
            "database_stats": {}
        }
        
        try:
            if query_type == QueryTypes.SQL_RETRIEVAL:
                retrieved_data = await self._sql_retrieval(query, entities, max_results)
            
            elif query_type == QueryTypes.VECTOR_RETRIEVAL:
                retrieved_data = await self._vector_retrieval(query, entities, max_results)
            
            elif query_type == QueryTypes.HYBRID_RETRIEVAL:
                retrieved_data = await self._hybrid_retrieval(query, entities, max_results)
            
            # Always get basic database statistics for context
            retrieved_data["database_stats"] = db_manager.get_database_stats()
            
        except Exception as e:
            logger.error("Data retrieval failed", query_type=query_type, error=str(e))
            retrieved_data["error"] = str(e)
        
        return retrieved_data
    
    async def _sql_retrieval(self, query: str, entities: Dict[str, Any], 
                   max_results: int) -> Dict[str, Any]:
        """Retrieve data using intelligent SQL generation - IMPROVED ERROR HANDLING"""
        
        try:
            # Import the intelligent SQL generator
            from app.services.intelligent_sql_generator import intelligent_sql_generator
            
            logger.info("Using intelligent SQL generation", query=query)
            
            # Generate SQL using LLM semantic understanding
            sql_generation_result = intelligent_sql_generator.generate_sql_from_query(query, entities)
            sql_query = sql_generation_result.get('sql_query', '')
            
            if not sql_query:
                raise ValueError("Failed to generate SQL query")
            
            # FIXED: Don't add LIMIT to COUNT queries or geographic queries that already have LIMIT
            if ('count(' not in sql_query.lower() and 
                'limit' not in sql_query.lower() and
                sql_generation_result.get('generation_method') not in ['geographic_direct', 'nearest_floats_direct', 'year_comparison_direct']):
                sql_query += f" LIMIT 25"  # Show 20-25 records as requested
            
            # Get total count first (for display purposes)
            count_query = self._get_count_query(sql_query)
            total_count = 0
            if count_query:
                try:
                    count_results = db_manager.execute_query(count_query)
                    total_count = count_results[0]['count'] if count_results else 0
                except Exception as e:
                    logger.warning("Failed to get total count", error=str(e))
                    total_count = 0
            
            # For nearest floats queries, use the actual result count since they have LIMIT already
            if sql_generation_result.get('generation_method') == 'nearest_floats_direct':
                total_count = 0  # Will be set to len(sql_results) after execution
            
            # Execute SQL query
            logger.info("Executing intelligent SQL query", query=sql_query)
            sql_results = db_manager.execute_query(sql_query)
            
            # Store total count and SQL query for response generation
            # For nearest floats queries, use actual result count
            if sql_generation_result.get('generation_method') == 'nearest_floats_direct':
                self._current_total_count = len(sql_results)
            else:
                self._current_total_count = total_count
            self._current_sql_query = sql_query
            
            # FIXED: Log if this looks like a fallback query was used
            if sql_generation_result.get('error'):
                logger.warning("SQL generation had errors", 
                            error=sql_generation_result['error'],
                            fallback_used=True)
            
            logger.info("SQL query executed successfully", 
                    result_count=len(sql_results),
                    generation_method=sql_generation_result.get('generation_method'))
            
            return {
                "sql_results": sql_results,
                "sql_query": sql_query,
                "sql_explanation": sql_generation_result.get('explanation', ''),
                "estimated_results": sql_generation_result.get('estimated_results', ''),
                "parameters_used": sql_generation_result.get('parameters_used', []),
                "generation_method": sql_generation_result.get('generation_method', 'intelligent'),
                "generation_error": sql_generation_result.get('error'),  # Include any errors
                "vector_results": [],
                "hybrid_results": {}
            }
            
        except Exception as e:
            logger.error("Intelligent SQL retrieval failed", error=str(e))
            # Fallback to vector retrieval instead of failing completely
            return await self._vector_retrieval(query, entities, max_results)
    
    async def _vector_retrieval(self, query: str, entities: Dict[str, Any], 
                              max_results: int) -> Dict[str, Any]:
        """Retrieve data using vector/semantic search"""
        
        try:
            # Perform semantic search on metadata summaries
            vector_results = vector_db_manager.semantic_search(query, limit=max_results)
            
            # Apply geographic filtering based on query
            logger.info(f"Before geographic filtering: {len(vector_results)} results")
            vector_results = self._filter_by_geographic_region(query, vector_results)
            logger.info(f"After geographic filtering: {len(vector_results)} results")
            
            # If we have specific parameters or regions, also search for those
            additional_results = []
            
            if entities.get('parameters'):
                for param in entities['parameters']:
                    param_results = vector_db_manager.search_by_parameter(param, limit=5)
                    additional_results.extend(param_results)
            
            if entities.get('regions'):
                for region in entities['regions']:
                    region_results = vector_db_manager.search_by_region(region, limit=5)
                    additional_results.extend(region_results)
            
            # Combine and deduplicate results
            all_vector_results = vector_results + additional_results
            seen_ids = set()
            unique_results = []
            
            for result in all_vector_results:
                result_id = result.get('id')
                if result_id not in seen_ids:
                    seen_ids.add(result_id)
                    unique_results.append(result)
                    if len(unique_results) >= max_results:
                        break
            
            return {
                "sql_results": [],
                "vector_results": unique_results,
                "search_query": query,
                "entities_searched": entities,
                "hybrid_results": {}
            }
            
        except Exception as e:
            logger.error("Vector retrieval failed", error=str(e))
            return {
                "sql_results": [],
                "vector_results": [],
                "error": f"Vector retrieval failed: {str(e)}",
                "hybrid_results": {}
            }
    
    async def _hybrid_retrieval(self, query: str, entities: Dict[str, Any], 
                              max_results: int) -> Dict[str, Any]:
        """Retrieve data using both SQL and vector search"""
        
        try:
            # Run both retrieval methods concurrently
            sql_task = asyncio.create_task(self._sql_retrieval(query, entities, max_results // 2))
            vector_task = asyncio.create_task(self._vector_retrieval(query, entities, max_results // 2))
            
            sql_data, vector_data = await asyncio.gather(sql_task, vector_task)
            
            # Combine results
            hybrid_results = {
                "sql_component": sql_data,
                "vector_component": vector_data,
                "combination_strategy": "parallel_retrieval"
            }
            
            return {
                "sql_results": sql_data.get('sql_results', []),
                "vector_results": vector_data.get('vector_results', []),
                "hybrid_results": hybrid_results,
                "sql_query": sql_data.get('sql_query', ''),
                "search_query": vector_data.get('search_query', query),
                "generation_method": sql_data.get('generation_method', 'intelligent')
            }
            
        except Exception as e:
            logger.error("Hybrid retrieval failed", error=str(e))
            # Fallback to vector retrieval only
            return await self._vector_retrieval(query, entities, max_results)
    
    async def _generate_response(self, query: str, classification: Dict[str, Any], 
                               retrieved_data: Dict[str, Any]) -> str:
        """Generate final user-friendly response"""
        
        try:
            query_type = classification['query_type']
            
            # Check if we have any useful data
            sql_results = retrieved_data.get('sql_results', [])
            vector_results = retrieved_data.get('vector_results', [])
            
            if not sql_results and not vector_results:
                return self._generate_no_results_response(query, classification)
            
            # Special handling for year comparison queries to avoid LLM hallucinations
            if self._is_year_comparison_query(query, retrieved_data):
                return self._generate_year_comparison_response(query, sql_results)
            
            # Special handling for float not found queries to avoid LLM hallucinations
            if self._is_float_not_found_query(query, sql_results):
                return self._generate_float_not_found_response(query, sql_results)
            
            

            # For ALL data queries, use data-based response to avoid LLM hallucinations
            if any(k in query.lower() for k in ["show", "find", "get", "list", "display", "float", "data", "profile", "temperature", "salinity", "trajectory", "trajectories", "location", "coordinates", "map", "bay", "ocean", "sea"]):
                logger.info("Using data-based response for data query to avoid hallucinations")
                try:
                    response = self._generate_data_response(query, retrieved_data, query_type)
                    logger.info(f"Data response generated successfully: {len(response)} characters")
                    return response
                except Exception as e:
                    logger.error(f"Error in data response generation: {e}")
                    # Return no data available instead of falling back to LLM
                    return {
                        "answer": "No data available for your query.",
                        "classification": {"query_type": "no_data"},
                        "data": {"records": []},
                        "visualization": {},
                        "response_id": "no_data_available"
                    }
            
            # Generate response using multi-provider LLM for other queries
            try:
                response = multi_llm_client.generate_final_response(query, retrieved_data, query_type)
                # Check if LLM returned a meaningful response or just generic messages
                if (response and response.strip() and 
                    "query processed successfully" not in response.lower() and
                    "no data found" not in response.lower() and
                    "no data available" not in response.lower() and
                    len(response) > 50):  # Ensure it's a substantial response
                    return response
                else:
                    # LLM failed or returned generic message, generate data-based response
                    logger.info("LLM returned generic response, using data-based fallback")
                    return self._generate_data_response(query, retrieved_data, query_type)
            except Exception as e:
                logger.error("LLM response generation failed", error=str(e))
                # Generate data-based response when LLM fails
                return self._generate_data_response(query, retrieved_data, query_type)
            
        except Exception as e:
            logger.error("Response generation failed", error=str(e))
            return f"I found some relevant data for your query, but encountered an error while generating the response. Error: {str(e)}"
    
    def _generate_data_response(self, query: str, retrieved_data: Dict[str, Any], query_type: str) -> str:
        """Generate response based on actual data - NO INTERPRETATION"""
        logger.info(f"Generating data response for query: {query}")
        logger.info(f"Retrieved data keys: {list(retrieved_data.keys())}")
        
        sql_results = retrieved_data.get('sql_results', [])
        vector_results = retrieved_data.get('vector_results', [])
        
        logger.info(f"SQL results count: {len(sql_results)}")
        logger.info(f"Vector results count: {len(vector_results)}")
        
        # Use SQL results if available, otherwise use vector results
        if sql_results:
            results = sql_results
            data_source = "SQL database"
        elif vector_results:
            results = vector_results
            data_source = "vector search"
        else:
            logger.warning("No data found in retrieved_data")
            return "No data available for your query."
        
        if not results:
            logger.warning("Results list is empty")
            return "No data available for your query."
        
        # Present raw data without interpretation
        sql_query = getattr(self, '_current_sql_query', '')
        return self._generate_raw_data_response(query, results, data_source, sql_query)
    
    def _generate_raw_data_response(self, query: str, results: list, data_source: str, sql_query: str = '') -> str:
        """Generate response with raw data only - NO INTERPRETATION"""
        logger.info(f"Generating raw data response with {len(results)} results")
        
        if not results:
            return "No data available for your query."
        
        # Check if this is a count query (single result with count field)
        if len(results) == 1 and 'count' in results[0]:
            count_value = results[0]['count']
            response = f"**Database Results** (1 record found):\n\n"
            response += f"**Total Count**: {count_value:,}\n"
            return response
        
        # Check if this is a year-based count query
        if any(keyword in query.lower() for keyword in ['how many', 'count', 'number of profiles', 'profiles in']):
            # Try to extract year information from results
            year_data = {}
            for result in results:
                if 'year' in result and 'count' in result:
                    year = int(result['year'])
                    count = result['count']
                    year_data[year] = count
            
            if year_data:
                # Use total count if available, otherwise use len(results)
                total_count = getattr(self, '_current_total_count', len(results))
                response = f"**Database Results** ({total_count:,} records found):\n\n"
                response += "**Profile Counts by Year:**\n\n"
                
                # Sort years
                for year in sorted(year_data.keys()):
                    count = year_data[year]
                    response += f"**{year}**: {count:,} profiles\n"
                
                total = sum(year_data.values())
                response += f"\n**Total**: {total:,} profiles\n"
                return response
        
        # Use total count if available, otherwise use len(results)
        total_count = getattr(self, '_current_total_count', len(results))
        response = f"**Database Results** ({total_count:,} records found):\n\n"
        
        # Add "Displaying a few of them:" if we have many records but only showing a sample
        if total_count > len(results):
            response += "**Displaying a few of them:**\n\n"
        
        # Check if this is an aggregate query (has min, max, avg, count but no float_id)
        if (len(results) > 0 and 
            'float_id' not in results[0] and
            any(key in results[0] for key in ['min', 'max', 'avg', 'count', 'sum'])):
            
            record = results[0]
            
            # Format aggregate results nicely
            for key, value in record.items():
                if key in ['min', 'max', 'avg']:
                    if 'temperature' in sql_query.lower():
                        response += f"**{key.title()} Temperature**: {value:.2f}°C\n"
                    elif 'salinity' in sql_query.lower():
                        response += f"**{key.title()} Salinity**: {value:.2f} PSU\n"
                    elif 'depth' in sql_query.lower() or 'pressure' in sql_query.lower():
                        response += f"**{key.title()} Depth**: {value:.1f}m\n"
                    else:
                        response += f"**{key.title()}**: {value}\n"
                elif key == 'count':
                    response += f"**Total Count**: {value:,}\n"
                elif key == 'sum':
                    response += f"**Total Sum**: {value}\n"
            
            return response
        
        # Check if this is a temperature variation query (has latitude and temperature data)
        if (len(results) > 0 and 
            'latitude' in results[0] and 
            ('surface_temp' in results[0] or 'deep_temp' in results[0]) and
            'float_id' not in results[0]):
            
            for i, record in enumerate(results):  # Show all latitude bands (up to 25)
                lat = record.get('latitude', 0)
                surface_temp = record.get('surface_temp')
                deep_temp = record.get('deep_temp')
                
                # Format latitude nicely
                lat_str = f"{abs(lat):.3f}°{'N' if lat >= 0 else 'S'}"
                
                response += f"**{lat_str}**:\n"
                if surface_temp is not None:
                    response += f"  - Surface Temperature: {surface_temp:.2f}°C\n"
                if deep_temp is not None:
                    response += f"  - Deep Temperature: {deep_temp:.2f}°C\n"
                response += "\n"
            
            return response
        
        # Group by float_id for better organization (original logic)
        float_groups = {}
        for result in results:
            # Handle both SQL results and vector search results
            if 'metadata' in result:
                # Vector search result - extract from metadata
                metadata = result.get('metadata', {})
                float_id = metadata.get('float_id', 'Unknown')
                # Flatten the metadata for easier access
                flattened_result = {
                    'float_id': float_id,
                    'latitude': metadata.get('latitude'),
                    'longitude': metadata.get('longitude'),
                    'profile_date': metadata.get('date'),
                    'profile_id': metadata.get('profile_id', 'Unknown')
                }
            else:
                # SQL result - use directly
                float_id = result.get('float_id', 'Unknown')
                flattened_result = result
            
            if float_id not in float_groups:
                float_groups[float_id] = []
            float_groups[float_id].append(flattened_result)
        
        # Display up to 20 floats, max 5 records per float
        displayed_floats = 0
        for float_id, records in list(float_groups.items())[:20]:
            displayed_floats += 1
            response += f"**Float {float_id}** ({len(records)} records):\n"
            
            for i, record in enumerate(records[:5]):  # Max 5 records per float
                lat = record.get('latitude')
                lon = record.get('longitude')
                date = record.get('profile_date', 'Unknown')
                profile_id = record.get('profile_id', 'Unknown')
                max_pressure = record.get('max_pressure')
                
                # Check if this is a location-based record or a summary record
                if lat is not None and lon is not None and isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                    # Location-based record - format coordinates nicely
                    lat_str = f"{abs(lat):.3f}°{'N' if lat >= 0 else 'S'}"
                    lon_str = f"{abs(lon):.3f}°{'E' if lon >= 0 else 'W'}"
                    
                    # Add depth information if available
                    depth_info = ""
                    if max_pressure is not None:
                        # Convert decibars to meters (1 decibar ≈ 1 meter for ocean depth)
                        depth_m = round(max_pressure, 1)
                        depth_info = f" - {depth_m}m depth"
                    
                    response += f"  {i+1}. {profile_id}: {lat_str}, {lon_str} ({date}){depth_info}\n"
                else:
                    # Summary record - show available data
                    first_date = record.get('first_profile_date', 'Unknown')
                    last_date = record.get('last_profile_date', 'Unknown')
                    total_profiles = record.get('total_profiles', 'Unknown')
                    operating_duration = record.get('operating_duration', 'Unknown')
                    
                    # Format operating duration nicely
                    if operating_duration != 'Unknown' and hasattr(operating_duration, 'days'):
                        days = operating_duration.days
                        years = days // 365
                        remaining_days = days % 365
                        if years > 0:
                            duration_str = f"{years} years, {remaining_days} days"
                        else:
                            duration_str = f"{days} days"
                    else:
                        duration_str = str(operating_duration)
                    
                    response += f"  {i+1}. {float_id}: {first_date} to {last_date} ({total_profiles} profiles, {duration_str})\n"
            
            if len(records) > 5:
                response += f"     ... and {len(records) - 5} more records\n"
            response += "\n"
        
        if len(float_groups) > 20:
            response += f"... and {len(float_groups) - 20} more floats\n"
        
        return response
    
    def _get_count_query(self, sql_query: str) -> str:
        """Generate a COUNT query from a SELECT query"""
        try:
            # Remove LIMIT clause if present
            count_query = re.sub(r'\s+LIMIT\s+\d+', '', sql_query, flags=re.IGNORECASE)
            
            # Remove ORDER BY clause if present (not needed for count)
            count_query = re.sub(r'\s+ORDER\s+BY\s+.*$', '', count_query, flags=re.IGNORECASE | re.DOTALL)
            
            # Replace SELECT ... FROM with SELECT COUNT(*) FROM
            # Handle complex SELECT clauses
            if 'GROUP BY' in count_query.upper():
                # For GROUP BY queries, we need to count the groups
                # Extract the part before GROUP BY
                before_group_by = count_query.split('GROUP BY')[0]
                from_match = re.search(r'FROM\s+(\w+)', before_group_by, re.IGNORECASE)
                if from_match:
                    table_name = from_match.group(1)
                    # Get the WHERE clause if present
                    where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|$)', count_query, re.IGNORECASE | re.DOTALL)
                    if where_match:
                        where_clause = where_match.group(1).strip()
                        return f"SELECT COUNT(*) as count FROM {table_name} WHERE {where_clause}"
                    else:
                        return f"SELECT COUNT(*) as count FROM {table_name}"
            else:
                # Simple case: replace SELECT ... with SELECT COUNT(*)
                count_query = re.sub(r'SELECT\s+.*?\s+FROM', 'SELECT COUNT(*) as count FROM', count_query, flags=re.IGNORECASE | re.DOTALL)
                return count_query
        except Exception as e:
            logger.warning("Failed to generate count query", error=str(e))
            return None
    
    def _generate_trajectory_response(self, query: str, results: list, data_source: str) -> str:
        """Generate response for trajectory/map queries"""
        logger.info(f"Generating trajectory response with {len(results)} results")
        
        if not results:
            return "No ARGO float trajectory data found for the specified criteria."
        
        # Extract unique floats and their locations
        float_data = {}
        for i, result in enumerate(results[:10]):  # Limit to first 10 results
            logger.info(f"Processing result {i}: {list(result.keys())}")
            
            # Check if float_id is in metadata
            metadata = result.get('metadata', {})
            if 'float_id' in metadata:
                float_id = metadata['float_id']
                if float_id not in float_data:
                    float_data[float_id] = []
                
                # Extract location data from metadata
                if 'latitude' in metadata and 'longitude' in metadata:
                    lat = float(metadata['latitude'])
                    lon = float(metadata['longitude'])
                    date = metadata.get('date', 'Unknown date')
                    float_data[float_id].append({
                        'latitude': lat,
                        'longitude': lon,
                        'date': date
                    })
                    logger.info(f"Added location for float {float_id}: {lat}, {lon}, {date}")
                else:
                    logger.warning(f"No latitude/longitude in metadata for result {i}")
            else:
                logger.warning(f"No float_id in metadata for result {i}")
        
        logger.info(f"Extracted data for {len(float_data)} floats")
        
        if not float_data:
            logger.warning("No float data extracted")
            return "ARGO float data found, but location information is not available."
        
        logger.info("Building response...")
        response = f"Found ARGO float trajectory data from {data_source}:\n\n"
        
        for float_id, locations in float_data.items():
            response += f"**Float {float_id}:**\n"
            for i, loc in enumerate(locations[:5]):  # Show up to 5 locations per float
                response += f"  - {loc['latitude']:.3f}°N, {loc['longitude']:.3f}°E ({loc['date']})\n"
            if len(locations) > 5:
                response += f"  - ... and {len(locations) - 5} more locations\n"
            response += "\n"
        
        response += f"Total floats found: {len(float_data)}\n"
        response += f"Total data points: {sum(len(locs) for locs in float_data.values())}"
        
        logger.info(f"Generated response with {len(response)} characters")
        return response
    
    def _generate_temperature_profile_response(self, query: str, results: list, data_source: str) -> str:
        """Generate response for temperature profile queries with better formatting"""
        logger.info(f"Generating temperature profile response with {len(results)} results")
        
        if not results:
            return "No temperature profile data found for your query."
        
        response = f"Temperature Profile Analysis - {len(results)} profiles found:\n\n"
        
        # Group results by date for better organization
        profiles_by_date = {}
        for result in results:
            date = result.get('profile_date', 'Unknown date')
            if date not in profiles_by_date:
                profiles_by_date[date] = []
            profiles_by_date[date].append(result)
        
        # Sort dates (most recent first)
        sorted_dates = sorted(profiles_by_date.keys(), reverse=True)
        
        for date in sorted_dates[:10]:  # Show up to 10 different dates
            profiles = profiles_by_date[date]
            response += f"**{date}** - {len(profiles)} profiles:\n"
            
            for i, profile in enumerate(profiles[:5]):  # Show up to 5 profiles per date
                profile_id = profile.get('profile_id', 'Unknown')
                lat = profile.get('latitude', 0)
                lon = profile.get('longitude', 0)
                
                # Format coordinates
                lat_str = f"{abs(lat):.3f}°{'N' if lat >= 0 else 'S'}"
                lon_str = f"{abs(lon):.3f}°{'E' if lon >= 0 else 'W'}"
                
                response += f"  {i+1}. **{profile_id}** at {lat_str}, {lon_str}\n"
                
                # Extract temperature data if available
                surface_temp = profile.get('surface_temp')
                deep_temp = profile.get('deep_temp')
                
                if surface_temp is not None and deep_temp is not None:
                    response += f"     Surface: {surface_temp:.2f}°C, Deep: {deep_temp:.2f}°C\n"
                elif 'temperature' in profile:
                    # Handle array temperature data
                    temp_array = profile['temperature']
                    if isinstance(temp_array, list) and len(temp_array) > 0:
                        surface = temp_array[0] if temp_array[0] is not None else "N/A"
                        deep = temp_array[-1] if temp_array[-1] is not None else "N/A"
                        response += f"     Surface: {surface}°C, Deep: {deep}°C\n"
                    else:
                        response += f"     Temperature data available\n"
                else:
                    response += f"     Temperature profile data available\n"
                
            if len(profiles) > 5:
                response += f"     ... and {len(profiles) - 5} more profiles\n"
            
            response += "\n"
        
        # Add summary statistics
        if len(results) > 0:
            response += f"**Summary:**\n"
            response += f"- Total profiles: {len(results)}\n"
            response += f"- Date range: {sorted_dates[-1]} to {sorted_dates[0]}\n"
            response += f"- Geographic coverage: Indian Ocean region\n"
        
        return response
    
    def _generate_parameter_response(self, query: str, results: list, data_source: str) -> str:
        """Generate response for parameter queries"""
        if not results:
            return "No oceanographic parameter data found for the specified criteria."
        
        response = f"Found oceanographic data from {data_source}:\n\n"
        
        for i, result in enumerate(results[:5]):  # Show first 5 results
            float_id = result.get('float_id', 'Unknown')
            date = result.get('profile_date', result.get('date', 'Unknown date'))
            
            response += f"**Profile {i+1} (Float {float_id}, {date}):**\n"
            
            if 'surface_temperature' in result:
                response += f"  - Surface Temperature: {result['surface_temperature']:.2f}°C\n"
            if 'surface_salinity' in result:
                response += f"  - Surface Salinity: {result['surface_salinity']:.2f} PSU\n"
            if 'max_depth' in result:
                response += f"  - Maximum Depth: {result['max_depth']:.1f}m\n"
            if 'latitude' in result and 'longitude' in result:
                response += f"  - Location: {result['latitude']:.3f}°N, {result['longitude']:.3f}°E\n"
            
            response += "\n"
        
        if len(results) > 5:
            response += f"... and {len(results) - 5} more profiles\n"
        
        return response
    
    def _generate_nearest_floats_response(self, query: str, results: list, data_source: str) -> str:
        """Generate response for nearest floats queries with distance information"""
        logger.info(f"Generating nearest floats response with {len(results)} results")
        
        if not results:
            return "No ARGO floats found near the specified coordinates."
        
        # Group by float_id to get unique floats with their closest locations
        float_data = {}
        for result in results:
            float_id = result.get('float_id')
            if float_id and float_id not in float_data:
                float_data[float_id] = {
                    'float_id': float_id,
                    'latitude': result.get('latitude'),
                    'longitude': result.get('longitude'),
                    'distance_km': result.get('distance_km'),
                    'profile_date': result.get('profile_date'),
                    'status': result.get('status'),
                    'float_type': result.get('float_type'),
                    'institution': result.get('institution')
                }
        
        # Sort by distance
        sorted_floats = sorted(float_data.values(), key=lambda x: x['distance_km'])
        
        response = f"Found {len(sorted_floats)} nearest ARGO floats:\n\n"
        
        for i, float_info in enumerate(sorted_floats[:10]):  # Show top 10
            lat = float_info['latitude']
            lon = float_info['longitude']
            distance = float_info['distance_km']
            date = float_info['profile_date']
            status = float_info['status']
            
            # Format coordinates nicely
            lat_str = f"{abs(lat):.3f}°{'N' if lat >= 0 else 'S'}"
            lon_str = f"{abs(lon):.3f}°{'E' if lon >= 0 else 'W'}"
            
            response += f"**Float {float_info['float_id']}** ({distance:.1f}km away):\n"
            response += f"  - Location: {lat_str}, {lon_str}\n"
            response += f"  - Date: {date}\n"
            response += f"  - Status: {status}\n\n"
        
        return response
    
    def _generate_generic_data_response(self, query: str, results: list, data_source: str) -> str:
        """Generate generic data response"""
        if not results:
            return "No data found for the specified criteria."
        
        response = f"Found {len(results)} data records from {data_source}:\n\n"
        
        # Show summary of first few results
        for i, result in enumerate(results[:3]):
            float_id = result.get('float_id', 'Unknown')
            date = result.get('profile_date', result.get('date', 'Unknown date'))
            response += f"**Record {i+1}:** Float {float_id} - {date}\n"
        
        if len(results) > 3:
            response += f"... and {len(results) - 3} more records\n"
        
        return response
    
    def _generate_no_results_response(self, query: str, classification: Dict[str, Any]) -> str:
        """Generate response when no data is found"""
        entities = classification.get('extracted_entities', {})
        suggestions = []
        
        # Check if this is a float-specific query
        import re
        float_id_patterns = [
            r'float\s+(\d+)',
            r'argo\s+float\s+(\d+)',
            r'float\s+id\s+(\d+)',
            r'float\s+(\d{7})',
        ]
        
        float_id = None
        for pattern in float_id_patterns:
            match = re.search(pattern, query.lower())
            if match:
                float_id = match.group(1)
                break
        
        if float_id:
            # Get actual date range for this float
            try:
                from app.core.database import db_manager
                date_query = f"""
                SELECT MIN(profile_date) as min_date, MAX(profile_date) as max_date, COUNT(*) as total_profiles
                FROM argo_profiles 
                WHERE float_id = '{float_id}'
                """
                date_result = db_manager.execute_query(date_query)
                
                if date_result and date_result[0]['total_profiles'] > 0:
                    min_date = date_result[0]['min_date']
                    max_date = date_result[0]['max_date']
                    total_profiles = date_result[0]['total_profiles']
                    
                    return f"""**No Data Found for Requested Date**

Float {float_id} exists in the database but has no data for the requested date.

**Available Data for Float {float_id}:**
- Date Range: {min_date} to {max_date}
- Total Profiles: {total_profiles}

**Suggestions:**
- Try a date within the available range ({min_date} to {max_date})
- Ask for the temperature profile for a different date
- Request general information about this float's data coverage"""
                else:
                    return f"Float {float_id} does not exist in the ARGO database. Please check the float ID and try again."
            except Exception as e:
                logger.error("Error getting float date range", error=str(e))
        
        # Original logic for non-float queries
        if entities.get('parameters'):
            suggestions.append("Try searching for different oceanographic parameters")
        
        if entities.get('locations'):
            suggestions.append("Consider expanding the geographic area")
        
        if entities.get('dates'):
            suggestions.append("Try a different date range")
        
        suggestion_text = " You might want to: " + ", ".join(suggestions) if suggestions else ""
        
        return f"I couldn't find specific data matching your query about {query}.{suggestion_text} You can also try rephrasing your question or asking for general information about ARGO float data."
    
    def _is_year_comparison_query(self, query: str, retrieved_data: Dict[str, Any]) -> bool:
        """Check if this is a year comparison query that should use deterministic response"""
        query_lower = query.lower()
        sql_results = retrieved_data.get('sql_results', [])
        
        # Check for year comparison keywords (expanded list)
        year_comparison_keywords = ['compare', 'versus', 'vs', 'between', 'comparison', 'compared']
        has_comparison_keywords = any(kw in query_lower for kw in year_comparison_keywords)
        
        # Check if we have year data in SQL results
        has_year_data = any('year' in str(row) for row in sql_results)
        
        # Check if SQL generation method indicates year comparison
        generation_method = retrieved_data.get('generation_method', '')
        is_year_comparison_sql = generation_method == 'year_comparison_direct'
        
        # Debug logging
        logger.info("Year comparison detection", 
                   query=query,
                   has_comparison_keywords=has_comparison_keywords,
                   has_year_data=has_year_data,
                   generation_method=generation_method,
                   is_year_comparison_sql=is_year_comparison_sql)
        
        return has_comparison_keywords and has_year_data and is_year_comparison_sql
    
    def _generate_year_comparison_response(self, query: str, sql_results: List[Dict[str, Any]]) -> str:
        """Generate deterministic year comparison response from SQL results"""
        if not sql_results:
            return "No data available for year comparison."
        
        # Get actual counts for each year from database
        from app.core.database import db_manager
        
        # Extract years from results
        years = set()
        for row in sql_results:
            year = int(row.get('year', 0))
            if year > 0:
                years.add(year)
        
        # Get actual counts for each year
        year_counts = {}
        for year in years:
            try:
                # Check if this is an equatorial query
                is_equatorial = any(term in query.lower() for term in ['equator', 'equatorial', 'near the equator'])
                
                if is_equatorial:
                    count_query = f"""
                    SELECT COUNT(*) as count 
                    FROM argo_profiles 
                    WHERE EXTRACT(YEAR FROM profile_date) = {year}
                    AND latitude BETWEEN -5 AND 5
                    AND temperature IS NOT NULL 
                    AND salinity IS NOT NULL
                    """
                else:
                    count_query = f"""
                    SELECT COUNT(*) as count 
                    FROM argo_profiles 
                    WHERE EXTRACT(YEAR FROM profile_date) = {year}
                    AND temperature IS NOT NULL 
                    AND salinity IS NOT NULL
                    """
                
                count_results = db_manager.execute_query(count_query)
                year_counts[year] = count_results[0]['count'] if count_results else 0
            except Exception as e:
                logger.warning(f"Failed to get count for year {year}", error=str(e))
                year_counts[year] = 0
        
        # Group results by year
        year_data = {}
        for row in sql_results:
            year = int(row.get('year', 0))
            if year not in year_data:
                year_data[year] = {
                    'count': year_counts.get(year, 0),  # Use actual count from database
                    'temperatures': [],
                    'salinities': [],
                    'latitudes': [],
                    'longitudes': []
                }
            
            # Collect numeric data for analysis
            if row.get('surface_temperature') is not None:
                year_data[year]['temperatures'].append(float(row['surface_temperature']))
            if row.get('surface_salinity') is not None:
                year_data[year]['salinities'].append(float(row['surface_salinity']))
            if row.get('latitude') is not None:
                year_data[year]['latitudes'].append(float(row['latitude']))
            if row.get('longitude') is not None:
                year_data[year]['longitudes'].append(float(row['longitude']))
        
        # Generate comparison text
        response_parts = []
        response_parts.append(f"**Ocean Conditions Comparison**")
        response_parts.append("")
        
        years = sorted(year_data.keys())
        if len(years) < 2:
            return f"Found data for {years[0]} only. Need data from at least two different years for comparison."
        
        for year in years:
            data = year_data[year]
            response_parts.append(f"**{year}:**")
            response_parts.append(f"- Profiles: {data['count']}")
            
            if data['temperatures']:
                avg_temp = sum(data['temperatures']) / len(data['temperatures'])
                min_temp = min(data['temperatures'])
                max_temp = max(data['temperatures'])
                response_parts.append(f"- Surface Temperature: {avg_temp:.1f}°C (range: {min_temp:.1f}-{max_temp:.1f}°C)")
            
            if data['salinities']:
                avg_sal = sum(data['salinities']) / len(data['salinities'])
                min_sal = min(data['salinities'])
                max_sal = max(data['salinities'])
                response_parts.append(f"- Surface Salinity: {avg_sal:.1f} PSU (range: {min_sal:.1f}-{max_sal:.1f} PSU)")
            
            if data['latitudes'] and data['longitudes']:
                lat_range = f"{min(data['latitudes']):.1f} to {max(data['latitudes']):.1f}°"
                lon_range = f"{min(data['longitudes']):.1f} to {max(data['longitudes']):.1f}°"
                response_parts.append(f"- Geographic Coverage: {lat_range}N/S, {lon_range}E/W")
            
            response_parts.append("")
        
        # Add comparison summary
        if len(years) == 2:
            year1, year2 = years
            data1, data2 = year_data[year1], year_data[year2]
            
            response_parts.append("**Comparison Summary:**")
            
            if data1['temperatures'] and data2['temperatures']:
                avg1 = sum(data1['temperatures']) / len(data1['temperatures'])
                avg2 = sum(data2['temperatures']) / len(data2['temperatures'])
                temp_diff = avg2 - avg1
                response_parts.append(f"- Temperature: {year2} was {temp_diff:+.1f}°C {'warmer' if temp_diff > 0 else 'cooler'} than {year1}")
            
            if data1['salinities'] and data2['salinities']:
                avg1 = sum(data1['salinities']) / len(data1['salinities'])
                avg2 = sum(data2['salinities']) / len(data2['salinities'])
                sal_diff = avg2 - avg1
                response_parts.append(f"- Salinity: {year2} was {sal_diff:+.1f} PSU {'saltier' if sal_diff > 0 else 'fresher'} than {year1}")
            
            response_parts.append(f"- Data Coverage: {year1} had {data1['count']} profiles, {year2} had {data2['count']} profiles")
        
        return "\n".join(response_parts)
    
    def _is_float_not_found_query(self, query: str, sql_results: List[Dict[str, Any]]) -> bool:
        """Check if this is a float not found query that should use deterministic response"""
        query_lower = query.lower()
        
        # Check for float ID patterns in the query
        import re
        float_id_patterns = [
            r'float\s+(\d+)',
            r'argo\s+float\s+(\d+)',
            r'float\s+id\s+(\d+)',
            r'float\s+(\d{7})',  # 7-digit float IDs
        ]
        
        has_float_query = any(re.search(pattern, query_lower) for pattern in float_id_patterns)
        
        # Check if SQL results indicate float not found
        # This happens when we get a single result with NULL values (like {'max': None})
        is_float_not_found = (
            len(sql_results) == 1 and 
            sql_results[0] and 
            all(value is None for value in sql_results[0].values())
        )
        
        # Debug logging
        logger.info("Float not found detection", 
                   query=query,
                   has_float_query=has_float_query,
                   is_float_not_found=is_float_not_found,
                   sql_results=sql_results)
        
        return has_float_query and is_float_not_found
    
    def _generate_float_not_found_response(self, query: str, sql_results: List[Dict[str, Any]]) -> str:
        """Generate deterministic float not found response"""
        import re
        
        # Extract float ID from query
        float_id = None
        float_id_patterns = [
            r'float\s+(\d+)',
            r'argo\s+float\s+(\d+)',
            r'float\s+id\s+(\d+)',
            r'float\s+(\d{7})',
        ]
        
        for pattern in float_id_patterns:
            match = re.search(pattern, query.lower())
            if match:
                float_id = match.group(1)
                break
        
        if not float_id:
            return "I couldn't find the specific float you're asking about. Please provide a valid float ID."
        
        # Get some similar float IDs for suggestions
        try:
            from app.core.database import db_manager
            similar_query = f"SELECT DISTINCT float_id FROM argo_profiles WHERE float_id LIKE '{float_id[:4]}%' ORDER BY float_id LIMIT 5"
            similar_floats = db_manager.execute_query(similar_query)
            similar_ids = [row['float_id'] for row in similar_floats]
        except:
            similar_ids = []
        
        response_parts = []
        response_parts.append(f"**Float {float_id} Not Found**")
        response_parts.append("")
        response_parts.append(f"Float {float_id} does not exist in the ARGO database.")
        response_parts.append("")
        response_parts.append("**Database Information:**")
        response_parts.append("- Total unique floats: 1,800")
        response_parts.append("- Date range: 2019-2025")
        response_parts.append("- Total profiles: 122,215")
        
        if similar_ids:
            response_parts.append("")
            response_parts.append("**Similar Float IDs:**")
            for similar_id in similar_ids:
                response_parts.append(f"- {similar_id}")
        
        response_parts.append("")
        response_parts.append("Please check the float ID and try again, or ask about available floats in a specific region or time period.")
        
        return "\n".join(response_parts)
    
    
    def _get_data_sources_used(self, retrieved_data: Dict[str, Any]) -> List[str]:
        """Determine which data sources were used"""
        sources = []
        
        if retrieved_data.get('sql_results'):
            sources.append("PostgreSQL database")
        
        if retrieved_data.get('vector_results'):
            sources.append("Vector database (semantic search)")
        
        if retrieved_data.get('hybrid_results'):
            sources.append("Hybrid retrieval")
        
        return sources
    
    def _count_total_results(self, retrieved_data: Dict[str, Any]) -> int:
        """Count total number of results retrieved"""
        total = 0
        
        if retrieved_data.get('sql_results'):
            total += len(retrieved_data['sql_results'])
        
        if retrieved_data.get('vector_results'):
            total += len(retrieved_data['vector_results'])
        
        return total
    
    def _create_error_response(self, query: str, error: str) -> Dict[str, Any]:
        """Create error response structure"""
        return {
            "success": False,
            "query": query,
            "classification": {
                "query_type": QueryTypes.VECTOR_RETRIEVAL,
                "confidence": 0.0,
                "reasoning": "Error occurred during processing"
            },
            "retrieved_data": {
                "sql_results": [],
                "vector_results": [],
                "error": error
            },
            "response": f"I encountered an error while processing your query: {error}. Please try rephrasing your question.",
            "metadata": {
                "query_type": "error",
                "confidence": 0.0,
                "data_sources_used": [],
                "total_results": 0
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all RAG pipeline components"""
        health = {
            "database": False,
            "vector_db": False,
            "llm": False,
            "overall": False
        }
        
        try:
            # Test database connection
            health["database"] = db_manager.test_connection()
            
            # Test vector database
            vector_stats = vector_db_manager.get_collection_stats()
            health["vector_db"] = vector_stats.get('total_documents', 0) > 0
            
            # Test LLM (simple classification test)
            test_result = multi_llm_client.classify_query_type("test query")
            health["llm"] = bool(test_result.get('query_type'))
            
            # Overall health
            health["overall"] = all([health["database"], health["vector_db"], health["llm"]])
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            health["error"] = str(e)
        
        return health
    
    def _filter_by_geographic_region(self, query: str, vector_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter vector results based on geographic regions mentioned in the query"""
        query_lower = query.lower()
        
        # Define geographic regions with their coordinate bounds
        regions = {
            'bay of bengal': {
                'lat_min': 5, 'lat_max': 25,
                'lon_min': 80, 'lon_max': 100,
                'keywords': ['bay of bengal', 'bengal', 'bengal bay']
            },
            'arabian sea': {
                'lat_min': 10, 'lat_max': 30,
                'lon_min': 50, 'lon_max': 80,
                'keywords': ['arabian sea', 'arabian', 'arabia']
            },
            'indian ocean': {
                'lat_min': -60, 'lat_max': 30,
                'lon_min': 20, 'lon_max': 120,
                'keywords': ['indian ocean', 'indian']
            },
            'pacific ocean': {
                'lat_min': -60, 'lat_max': 60,
                'lon_min': 120, 'lon_max': -120,
                'keywords': ['pacific ocean', 'pacific']
            },
            'atlantic ocean': {
                'lat_min': -60, 'lat_max': 60,
                'lon_min': -80, 'lon_max': 20,
                'keywords': ['atlantic ocean', 'atlantic']
            },
            'mediterranean sea': {
                'lat_min': 30, 'lat_max': 45,
                'lon_min': -5, 'lon_max': 40,
                'keywords': ['mediterranean', 'mediterranean sea']
            }
        }
        
        # Find matching region
        matching_region = None
        for region_name, region_info in regions.items():
            if any(keyword in query_lower for keyword in region_info['keywords']):
                matching_region = region_info
                logger.info(f"Found geographic region match: {region_name}")
                break
        
        if not matching_region:
            logger.info("No specific geographic region found in query, returning all results")
            return vector_results
        
        # Filter results based on coordinates
        filtered_results = []
        for result in vector_results:
            metadata = result.get('metadata', {})
            lat = metadata.get('latitude')
            lon = metadata.get('longitude')
            
            if lat is not None and lon is not None:
                try:
                    lat_float = float(lat)
                    lon_float = float(lon)
                    
                    # Check if coordinates fall within the region bounds
                    if (matching_region['lat_min'] <= lat_float <= matching_region['lat_max'] and
                        matching_region['lon_min'] <= lon_float <= matching_region['lon_max']):
                        filtered_results.append(result)
                        logger.debug(f"Kept result at {lat_float}, {lon_float} for region")
                    else:
                        logger.debug(f"Filtered out result at {lat_float}, {lon_float} (outside region bounds)")
                except (ValueError, TypeError):
                    # If coordinates can't be parsed, keep the result
                    filtered_results.append(result)
            else:
                # If no coordinates, keep the result
                filtered_results.append(result)
        
        # If no results after filtering, try a broader search
        if len(filtered_results) == 0:
            logger.info("No results found in specific region, trying broader search")
            
            # Define broader regions for different queries
            broader_regions = {
                'bay of bengal': {
                    'lat_min': -10, 'lat_max': 30,
                    'lon_min': 60, 'lon_max': 120,
                    'name': 'broader Indian Ocean region'
                },
                'arabian sea': {
                    'lat_min': 5, 'lat_max': 35,
                    'lon_min': 45, 'lon_max': 85,
                    'name': 'broader Arabian Sea region'
                },
                'indian ocean': {
                    'lat_min': -60, 'lat_max': 30,
                    'lon_min': 20, 'lon_max': 120,
                    'name': 'broader Indian Ocean region'
                }
            }
            
            # Find matching broader region
            broader_region = None
            for region_key, region_info in broader_regions.items():
                if region_key in query_lower:
                    broader_region = region_info
                    break
            
            if broader_region:
                logger.info(f"Using {broader_region['name']} for query")
                
                for result in vector_results:
                    metadata = result.get('metadata', {})
                    lat = metadata.get('latitude')
                    lon = metadata.get('longitude')
                    
                    if lat is not None and lon is not None:
                        try:
                            lat_float = float(lat)
                            lon_float = float(lon)
                            
                            if (broader_region['lat_min'] <= lat_float <= broader_region['lat_max'] and
                                broader_region['lon_min'] <= lon_float <= broader_region['lon_max']):
                                filtered_results.append(result)
                                logger.debug(f"Kept result at {lat_float}, {lon_float} for broader region")
                        except (ValueError, TypeError):
                            filtered_results.append(result)
                
                logger.info(f"Broader geographic filtering: {len(vector_results)} -> {len(filtered_results)} results")
                
                # Add a note to the results that we're using broader filtering
                if filtered_results:
                    for result in filtered_results:
                        if 'metadata' not in result:
                            result['metadata'] = {}
                        result['metadata']['geographic_note'] = f"Using {broader_region['name']} (no specific data found in requested region)"
        
        logger.info(f"Geographic filtering: {len(vector_results)} -> {len(filtered_results)} results")
        return filtered_results


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()