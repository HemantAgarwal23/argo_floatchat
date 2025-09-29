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
# Import intelligent analysis with error handling
try:
    from app.services.intelligent_analysis import intelligent_analysis_service
    INTELLIGENT_ANALYSIS_AVAILABLE = True
except ImportError:
    intelligent_analysis_service = None
    INTELLIGENT_ANALYSIS_AVAILABLE = False

logger = structlog.get_logger()


class RAGPipeline:
    """Complete RAG pipeline for ARGO oceanographic data queries"""
    
    def __init__(self):
        self.max_sql_results = settings.MAX_SEARCH_RESULTS
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.geographic_validator = GeographicValidator()
    
    async def process_query(self, user_query: str, max_results: int = None, language: str = "en") -> Dict[str, Any]:
        """Main RAG pipeline processing method"""
        try:
            max_results = max_results or self.max_sql_results
            
            logger.info("Starting RAG pipeline", query=user_query, language=language)
            
            # =============================================================================
            # CONVERSATIONAL FEATURES - Capability Questions (No Database Query)
            # =============================================================================
            
            # Handle capability and help questions (no database query needed)
            query_lower = user_query.lower().strip()
            
            if any(phrase in query_lower for phrase in [
                "what can you do", "what are your capabilities", "help", "what features", 
                "what do you support", "what can you help with", "capabilities", "features"
            ]):
                capability_response = """I'm your ARGO ocean data assistant! Here's what I can help you with:

🌊 **Ocean Data Analysis:**
• Temperature profiles and trends
• Salinity patterns and variations  
• Oceanographic parameter analysis
• Depth-based data exploration

🗺️ **Geographic Queries:**
• Find ARGO floats by location
• Regional ocean analysis (Indian Ocean, Pacific, Atlantic, etc.)
• Coordinate-based searches
• Float trajectory mapping

📊 **Data Visualization:**
• Interactive maps with float locations
• Bar charts comparing parameters
• Data tables with detailed statistics
• Time-series analysis

🔍 **Smart Search:**
• Natural language queries
• Multi-parameter analysis
• Trend detection and patterns
• Comparative studies

💾 **Data Export:**
• CSV, JSON, Excel formats
• Custom data filtering
• Report generation

Just ask me anything about ocean data! For example:
• "Show me temperature in the Indian Ocean"
• "Compare salinity near the equator"
• "Find floats near coordinates 20°N, 70°E"
• "Create a bar chart of ocean parameters" """
                
                return {
                    "success": True,
                    "response": capability_response,
                    "query_type": "capability",
                    "sql_results": [],
                    "vector_results": [],
                    "visualization_suggestions": None
                }
            
            # Handle "who are you" type questions
            if any(phrase in query_lower for phrase in [
                "who are you", "what are you", "introduce yourself", "tell me about yourself"
            ]):
                intro_response = """I'm ARGO FloatChat, your AI-powered ocean data assistant! 

I specialize in helping you explore and understand oceanographic data from ARGO floats - autonomous instruments that drift through the world's oceans collecting vital measurements.

My expertise includes:
• Analyzing temperature, salinity, and other ocean parameters
• Creating interactive visualizations and maps
• Finding specific float locations and trajectories
• Detecting patterns and trends in ocean data
• Answering complex oceanographic questions

I'm designed to make ocean data accessible and understandable, whether you're a researcher, student, or just curious about our oceans. I can process natural language queries and provide both raw data and intelligent insights.

What would you like to explore about our oceans today?"""
                
                return {
                    "success": True,
                    "response": intro_response,
                    "query_type": "introduction",
                    "sql_results": [],
                    "vector_results": [],
                    "visualization_suggestions": None
                }
            
            # Handle "what is argo" or "explain argo" questions
            if any(phrase in query_lower for phrase in [
                "what is argo", "explain argo", "tell me about argo", "what are argo floats"
            ]):
                argo_response = """ARGO is a global ocean observation system that uses autonomous floats to monitor the world's oceans!

🌊 **What are ARGO floats?**
ARGO floats are robotic instruments that drift through the ocean, automatically collecting measurements of temperature, salinity, and other oceanographic parameters.

📊 **What data do they collect?**
• Temperature profiles from surface to 2000m depth
• Salinity measurements throughout the water column
• Pressure and depth information
• Biogeochemical data (oxygen, nutrients, chlorophyll)
• Float position and trajectory data

🌍 **Global Coverage:**
• Over 4,000 active floats worldwide
• Data from all major ocean basins
• Continuous monitoring since 2000
• Real-time data transmission via satellite

🔬 **Why is this important?**
ARGO data helps us understand:
• Climate change impacts on oceans
• Ocean circulation patterns
• Marine ecosystem health
• Weather and climate prediction
• Sea level rise monitoring

I can help you explore this amazing dataset! Try asking me about temperature patterns, salinity variations, or float locations in specific regions."""
                
                return {
                    "success": True,
                    "response": argo_response,
                    "query_type": "argo_explanation",
                    "sql_results": [],
                    "vector_results": [],
                    "visualization_suggestions": None
                }
            
            # Step 0: Translate non-English queries to English for processing
            processed_query = user_query
            if language != "en":
                try:
                    translation_result = await multi_llm_client.translate_query(user_query, source_lang=language, target_lang="en")
                    if translation_result and translation_result.get("success"):
                        processed_query = translation_result["translated_query"]
                        logger.info("Query translated", original=user_query, translated=processed_query)
                    else:
                        logger.warning("Translation failed, using original query", query=user_query)
                except Exception as e:
                    logger.error("Translation error", error=str(e), query=user_query)
            
            # Step 1: Classify the query (using translated version)
            classification = query_classifier.classify_query(processed_query)
            
            # Step 1.5: Check if user is asking about data coverage (using processed query)
            if any(phrase in processed_query.lower() for phrase in ["what data", "data coverage", "ocean regions", "available data", "what oceans"]):
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
            
            # Step 1.6: Validate geographic coverage to prevent hallucination (using processed query)
            geographic_validation = self.geographic_validator.validate_geographic_coverage(processed_query)
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
            
            # Force SQL retrieval for specific data queries to prevent hallucination
            # Only use vector search for pure informational questions, not data requests (using processed query)
            # Exclude vector keywords from force SQL rule
            vector_keywords = ['describe', 'explain', 'patterns', 'trends', 'characteristics', 'general', 'typical', 'average', 'variations', 'changes', 'insights', 'understand']
            is_vector_query = any(k in processed_query.lower() for k in vector_keywords)
            
            if not is_vector_query and any(k in processed_query.lower() for k in ["show", "find", "get", "list", "display", "float", "profile", "temperature", "salinity", "trajectory", "trajectories", "location", "coordinates", "map", "bay", "ocean", "sea", "equator", "near"]):
                logger.info("Forcing SQL retrieval for data query to prevent hallucination")
                classification['query_type'] = QueryTypes.SQL_RETRIEVAL
                classification['confidence'] = 1.0
                classification['reasoning'] = "Forced SQL retrieval for data query to prevent hallucination"
            
            # Step 2: Retrieve relevant data based on classification (using processed query)
            retrieved_data = await self._retrieve_data(processed_query, classification, max_results)
            
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
            
            # Generate visualization suggestions for bar chart and data table queries
            if any(k in user_query.lower() for k in ["bar chart", "bar graph", "chart", "graph", "compare", "vs", "versus", "data table", "table", "tabular", "summary", "summarize", "overview", "statistics", "stats"]):
                try:
                    sql_results = retrieved_data.get('sql_results', [])
                    logger.info(f"Generating visualization suggestions for query with {len(sql_results)} SQL results")
                    if sql_results:
                        viz_suggestions = visualization_generator.generate_visualization_suggestions(user_query, sql_results)
                        result["visualization_suggestions"] = viz_suggestions
                        logger.info(f"Generated {len(viz_suggestions.get('suggestions', []))} visualization suggestions")
                        logger.info(f"Visualization suggestions: {viz_suggestions}")
                    else:
                        logger.warning("No SQL results available for visualization suggestions")
                except Exception as e:
                    logger.error("Failed to generate visualization suggestions", error=str(e))
                    import traceback
                    traceback.print_exc()
            
            logger.info("RAG pipeline completed successfully", 
                       query_type=classification['query_type'],
                       total_results=result['metadata']['total_results'])
            
            # If visualization-related query OR year comparison OR bar chart, attach visualization payload
            # Only generate visualizations when explicitly requested
            should_generate_visualization = (
                any(k in user_query.lower() for k in ["bar chart", "bar graph", "data table", "table", "chart", "graph", "visualization", "plot"]) or
                any(k in user_query.lower() for k in ["map", "coordinates", "geojson", "trajectory", "trajectories"])
            )
            
            if should_generate_visualization:
                try:
                    logger.info("Generating visualization...")
                    
                    # Generate appropriate visualization based on request
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
                    result["visualization"] = visualization_generator.build_visualization_payload(results_for_visualization, user_query)
                    
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
            
            

            # For data queries (not vector queries), use data-based response to avoid LLM hallucinations
            # Exclude vector queries from this condition
            vector_keywords = ['describe', 'explain', 'patterns', 'trends', 'characteristics', 'general', 'typical', 'average', 'variations', 'changes', 'insights', 'understand']
            is_vector_query = any(k in query.lower() for k in vector_keywords)
            
            if not is_vector_query and any(k in query.lower() for k in ["show", "find", "get", "list", "display", "float", "data", "profile", "temperature", "salinity", "trajectory", "trajectories", "location", "coordinates", "map", "bay", "ocean", "sea"]):
                logger.info("Using data-based response for data query")
                try:
                    # Temporarily disable intelligent analysis to prevent hanging
                    # TODO: Fix intelligent analysis timeout issues
                    logger.info("Using standard data response (intelligent analysis temporarily disabled)")
                    response = self._generate_data_response(query, retrieved_data, query_type)
                    return response
                except asyncio.TimeoutError:
                    logger.warning("Intelligent analysis timeout, using standard response")
                    response = self._generate_data_response(query, retrieved_data, query_type)
                    return response
                except Exception as e:
                    logger.error(f"Error in data response generation: {e}")
                    # Fallback to regular data response
                    try:
                        response = self._generate_data_response(query, retrieved_data, query_type)
                        return response
                    except Exception as e2:
                        logger.error(f"Error in fallback data response generation: {e2}")
                        return "No data available for your query."
            
            # Generate response using multi-provider LLM for other queries
            try:
                response = multi_llm_client.generate_final_response(query, retrieved_data, query_type)
                logger.info(f"LLM response length: {len(response) if response else 0}")
                logger.info(f"LLM response preview: {response[:200] if response else 'None'}...")
                
                # Check if LLM returned a meaningful response or just generic messages
                is_valid = (response and response.strip() and 
                    "query processed successfully" not in response.lower() and
                    "no data found" not in response.lower() and
                    "no data available" not in response.lower() and
                    len(response) > 50)  # Ensure it's a substantial response
                
                logger.info(f"LLM response validation: {is_valid}")
                
                if is_valid:
                    logger.info("Using LLM response")
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
    
    async def _generate_intelligent_data_response(self, query: str, retrieved_data: Dict[str, Any], 
                                                query_type: str, classification: Dict[str, Any]) -> str:
        """Generate intelligent response with analysis and insights"""
        try:
            logger.info("Generating intelligent data response with analysis")
            
            # Get basic data response first
            basic_response = self._generate_data_response(query, retrieved_data, query_type)
            
            # Extract parameters and regions from query for intelligent analysis
            analysis_params = self._extract_analysis_parameters(query, classification)
            
            # Generate intelligent insights if we have enough data
            sql_results = retrieved_data.get('sql_results', [])
            if len(sql_results) >= 10:  # Only analyze if we have sufficient data
                insights = await self._generate_intelligent_insights(query, retrieved_data, analysis_params)
                
                # Combine basic response with intelligent insights
                intelligent_response = f"{basic_response}\n\n## 🔍 **Intelligent Analysis**\n\n"
                
                if insights.get("anomalies_found", 0) > 0:
                    intelligent_response += f"**Anomalies Detected:** {insights['anomalies_found']} unusual values found\n"
                
                if insights.get("trends"):
                    trend_info = insights["trends"]
                    intelligent_response += f"**Trend Analysis:** {trend_info.get('trend_direction', 'stable')} trend detected\n"
                
                if insights.get("insights"):
                    intelligent_response += "**Key Insights:**\n"
                    for insight in insights["insights"][:3]:  # Show top 3 insights
                        intelligent_response += f"• {insight}\n"
                
                if insights.get("suggestions"):
                    intelligent_response += "\n**💡 Smart Suggestions:**\n"
                    for suggestion in insights["suggestions"][:3]:  # Show top 3 suggestions
                        intelligent_response += f"• {suggestion}\n"
                
                return intelligent_response
            else:
                # Not enough data for intelligent analysis, return basic response with suggestion
                return f"{basic_response}\n\n💡 **Tip:** For more detailed analysis, try queries that return more data points."
                
        except Exception as e:
            logger.error("Error in intelligent data response generation", error=str(e))
            # Fallback to basic response
            return self._generate_data_response(query, retrieved_data, query_type)
    
    def _extract_analysis_parameters(self, query: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for intelligent analysis from query and classification"""
        try:
            params = {
                "region": "Indian Ocean",  # Default region
                "parameter": "temperature",  # Default parameter
                "analysis_type": "statistical"
            }
            
            # Extract region from query
            query_lower = query.lower()
            if "arabian sea" in query_lower:
                params["region"] = "Arabian Sea"
            elif "bay of bengal" in query_lower:
                params["region"] = "Bay of Bengal"
            elif "indian ocean" in query_lower:
                params["region"] = "Indian Ocean"
            
            # Extract parameter from query
            if "temperature" in query_lower or "temp" in query_lower:
                params["parameter"] = "temperature"
            elif "salinity" in query_lower:
                params["parameter"] = "salinity"
            elif "oxygen" in query_lower:
                params["parameter"] = "dissolved_oxygen"
            elif "chlorophyll" in query_lower:
                params["parameter"] = "chlorophyll"
            elif "nitrate" in query_lower:
                params["parameter"] = "nitrate"
            
            # Extract analysis type from query
            if any(word in query_lower for word in ["trend", "trends", "change", "over time"]):
                params["analysis_type"] = "trend"
            elif any(word in query_lower for word in ["anomaly", "anomalies", "unusual", "outlier"]):
                params["analysis_type"] = "anomaly"
            elif any(word in query_lower for word in ["compare", "comparison", "vs", "versus"]):
                params["analysis_type"] = "comparison"
            elif any(word in query_lower for word in ["correlation", "relationship", "related"]):
                params["analysis_type"] = "correlation"
            
            return params
            
        except Exception as e:
            logger.error("Error extracting analysis parameters", error=str(e))
            return {"region": "Indian Ocean", "parameter": "temperature", "analysis_type": "statistical"}
    
    async def _generate_intelligent_insights(self, query: str, retrieved_data: Dict[str, Any], 
                                           analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent insights using the analysis service"""
        try:
            insights = {}
            
            # Try anomaly detection
            try:
                anomaly_result = await intelligent_analysis_service.detect_anomalies(
                    query=query, threshold=2.0
                )
                if anomaly_result.get("success"):
                    insights.update({
                        "anomalies_found": anomaly_result["result"].get("anomalies_found", 0),
                        "anomaly_insights": anomaly_result["result"].get("insights", [])
                    })
            except Exception as e:
                logger.warning("Anomaly detection failed", error=str(e))
            
            # Try trend analysis
            try:
                trend_result = await intelligent_analysis_service.analyze_trends(
                    parameter=analysis_params["parameter"],
                    region=analysis_params["region"]
                )
                if trend_result.get("success"):
                    insights["trends"] = trend_result["result"].get("trends", {})
                    insights["trend_insights"] = trend_result["result"].get("insights", [])
            except Exception as e:
                logger.warning("Trend analysis failed", error=str(e))
            
            # Generate smart suggestions
            try:
                suggestions_result = await intelligent_analysis_service.generate_smart_suggestions(
                    current_query=query
                )
                if suggestions_result.get("success"):
                    insights["suggestions"] = suggestions_result["result"].get("suggestions", [])
                    insights["follow_ups"] = suggestions_result["result"].get("follow_up_questions", [])
            except Exception as e:
                logger.warning("Smart suggestions failed", error=str(e))
            
            # Combine insights
            all_insights = []
            if insights.get("anomaly_insights"):
                all_insights.extend(insights["anomaly_insights"][:2])  # Top 2 anomaly insights
            if insights.get("trend_insights"):
                all_insights.extend(insights["trend_insights"][:2])  # Top 2 trend insights
            
            insights["insights"] = all_insights[:4]  # Limit to 4 total insights
            
            return insights
            
        except Exception as e:
            logger.error("Error generating intelligent insights", error=str(e))
            return {"insights": ["Analysis completed successfully"]}
    
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
        
        # Check if this is a data table request - provide better response
        if any(keyword in query.lower() for keyword in ["data table", "table", "tabular", "statistics", "summary"]):
            total_count = getattr(self, '_current_total_count', len(results))
            return f"**Data Analysis Complete** ({total_count:,} records found):\n\nI've generated comprehensive data tables and visualizations for your query. The interactive tables below show detailed statistics and analysis of the oceanographic data.\n\n**Available Data:**\n- **Records Found:** {total_count:,}\n- **Data Source:** {data_source}\n- **Analysis Type:** Statistical Summary\n\nPlease review the data tables and charts below for detailed insights."
        
        # Only generate bar chart responses when explicitly requested
        if any(keyword in query.lower() for keyword in ["bar chart", "bar graph", "chart", "graph"]):
            total_count = getattr(self, '_current_total_count', len(results))
            return f"**Data Analysis Complete** ({total_count:,} records found):\n\nI've generated comprehensive bar charts and visualizations for your query. The interactive charts below show detailed comparisons and analysis of the oceanographic data.\n\n**Available Data:**\n- **Records Found:** {total_count:,}\n- **Data Source:** {data_source}\n- **Analysis Type:** Comparative Visualization\n\nPlease review the charts and visualizations below for detailed insights."
        
        # Present raw data without interpretation for other queries
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
                
                # Extract temperature and salinity data from arrays if present
                if 'temperature' in result and result['temperature']:
                    temp_array = result['temperature']
                    if isinstance(temp_array, list) and len(temp_array) > 0:
                        # Get surface temperature (first value) and deep temperature (last non-null value)
                        surface_temp = temp_array[0] if temp_array[0] is not None else None
                        deep_temp = None
                        for temp_val in reversed(temp_array):
                            if temp_val is not None:
                                deep_temp = temp_val
                                break
                        flattened_result['surface_temperature'] = surface_temp
                        flattened_result['deep_temperature'] = deep_temp
                        flattened_result['temperature_range'] = f"{surface_temp:.2f}°C to {deep_temp:.2f}°C" if surface_temp and deep_temp else "Temperature data available"
                
                if 'salinity' in result and result['salinity']:
                    sal_array = result['salinity']
                    if isinstance(sal_array, list) and len(sal_array) > 0:
                        # Get surface salinity (first value) and deep salinity (last non-null value)
                        surface_sal = sal_array[0] if sal_array[0] is not None else None
                        deep_sal = None
                        for sal_val in reversed(sal_array):
                            if sal_val is not None:
                                deep_sal = sal_val
                                break
                        flattened_result['surface_salinity'] = surface_sal
                        flattened_result['deep_salinity'] = deep_sal
                        flattened_result['salinity_range'] = f"{surface_sal:.2f} to {deep_sal:.2f} PSU" if surface_sal and deep_sal else "Salinity data available"
            
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
                    
                    # Add temperature and salinity information if available
                    temp_info = ""
                    sal_info = ""
                    
                    if 'surface_temperature' in record and record['surface_temperature'] is not None:
                        temp_info = f" - Temp: {record['surface_temperature']:.2f}°C"
                        if 'deep_temperature' in record and record['deep_temperature'] is not None:
                            temp_info += f" to {record['deep_temperature']:.2f}°C"
                    
                    if 'surface_salinity' in record and record['surface_salinity'] is not None:
                        sal_info = f" - Sal: {record['surface_salinity']:.2f} PSU"
                        if 'deep_salinity' in record and record['deep_salinity'] is not None:
                            sal_info += f" to {record['deep_salinity']:.2f} PSU"
                    
                    response += f"  {i+1}. {profile_id}: {lat_str}, {lon_str} ({date}){depth_info}{temp_info}{sal_info}\n"
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
        
        # Sanitize any HTML tags that might have been introduced
        import re
        response = re.sub(r'<[^>]+>', '', response)  # Remove all HTML tags
        
        # Additional sanitization - remove any remaining HTML entities
        response = response.replace('&lt;', '<').replace('&gt;', '>')
        response = re.sub(r'<[^>]+>', '', response)  # Remove any remaining HTML tags
        
        return response
    
    def _get_count_query(self, sql_query: str) -> str:
        """Generate a COUNT query from a SELECT query"""
        try:
            # Remove LIMIT clause if present
            count_query = re.sub(r'\s+LIMIT\s+\d+', '', sql_query, flags=re.IGNORECASE)
            
            # Remove ORDER BY clause if present (not needed for count)
            count_query = re.sub(r'\s+ORDER\s+BY\s+.*$', '', count_query, flags=re.IGNORECASE | re.DOTALL)
            
            # For complex distance calculation queries with JOINs, use a simpler approach
            if 'LEFT JOIN' in count_query.upper() or 'JOIN' in count_query.upper():
                # Extract the main table and WHERE clause
                from_match = re.search(r'FROM\s+(\w+)\s+(\w+)', count_query, re.IGNORECASE)
                if from_match:
                    table_name = from_match.group(1)
                    table_alias = from_match.group(2)
                    # Get the WHERE clause if present
                    where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|$)', count_query, re.IGNORECASE | re.DOTALL)
                    if where_match:
                        where_clause = where_match.group(1).strip()
                        # Replace table alias with actual table name in WHERE clause
                        where_clause = where_clause.replace(f'{table_alias}.', f'{table_name}.')
                        return f"SELECT COUNT(*) as count FROM {table_name} WHERE {where_clause}"
                    else:
                        return f"SELECT COUNT(*) as count FROM {table_name}"
            
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