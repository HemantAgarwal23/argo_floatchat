"""
rag_pipeline.py
Complete RAG (Retrieval-Augmented Generation) pipeline for ARGO queries
"""
from typing import Dict, Any, List, Optional
import asyncio
import structlog
from app.core.database import db_manager
from app.core.vector_db import vector_db_manager
from app.core.multi_llm_client import multi_llm_client
from app.services.query_classifier import query_classifier
from app.config import settings, QueryTypes
from app.services.visualization_generator import visualization_generator

logger = structlog.get_logger()


class RAGPipeline:
    """Complete RAG pipeline for ARGO oceanographic data queries"""
    
    def __init__(self):
        self.max_sql_results = settings.MAX_SEARCH_RESULTS
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
    
    async def process_query(self, user_query: str, max_results: int = None) -> Dict[str, Any]:
        """Main RAG pipeline processing method"""
        try:
            max_results = max_results or self.max_sql_results
            
            logger.info("Starting RAG pipeline", query=user_query)
            
            # Step 1: Classify the query
            classification = query_classifier.classify_query(user_query)
            
            # Force vector retrieval for map/trajectory queries to ensure we get the data
            if any(k in user_query.lower() for k in ["map", "trajectory", "trajectories", "location", "coordinates"]):
                logger.info("Forcing vector retrieval for map/trajectory query")
                classification['query_type'] = QueryTypes.VECTOR_RETRIEVAL
                classification['confidence'] = 1.0
                classification['reasoning'] = "Forced vector retrieval for map/trajectory query"
            
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
                sql_generation_result.get('generation_method') != 'geographic_direct'):
                sql_query += f" LIMIT {max_results}"
            
            # Execute SQL query
            logger.info("Executing intelligent SQL query", query=sql_query)
            sql_results = db_manager.execute_query(sql_query)
            
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
            
            

            # For map/trajectory queries, always use data-based response to avoid LLM hallucinations
            if any(k in query.lower() for k in ["map", "trajectory", "trajectories", "location", "coordinates"]):
                logger.info("Using data-based response for map/trajectory query to avoid hallucinations")
                try:
                    response = self._generate_data_response(query, retrieved_data, query_type)
                    logger.info(f"Data response generated successfully: {len(response)} characters")
                    return response
                except Exception as e:
                    logger.error(f"Error in data response generation: {e}")
                    import traceback
                    traceback.print_exc()
                    return f"Error generating data response: {str(e)}"
            
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
        """Generate response based on actual data when LLM fails"""
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
            return "No data found for your query."
        
        if not results:
            logger.warning("Results list is empty")
            return "No data found for your query."
        
        # Generate response based on query type
        if any(k in query.lower() for k in ["map", "trajectory", "trajectories", "location", "coordinates"]):
            return self._generate_trajectory_response(query, results, data_source)
        elif "temperature" in query.lower() or "salinity" in query.lower():
            return self._generate_parameter_response(query, results, data_source)
        else:
            return self._generate_generic_data_response(query, results, data_source)
    
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
        
        # Group results by year
        year_data = {}
        for row in sql_results:
            year = int(row.get('year', 0))
            if year not in year_data:
                year_data[year] = {
                    'count': 0,
                    'temperatures': [],
                    'salinities': [],
                    'latitudes': [],
                    'longitudes': []
                }
            
            year_data[year]['count'] += 1
            
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