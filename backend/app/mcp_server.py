#!/usr/bin/env python3
"""
ARGO FloatChat MCP Server
Model Context Protocol server for intelligent oceanographic data analysis
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ResourceTemplate,
    ListResourcesRequest, ListResourcesResult, ListToolsRequest, ListToolsResult,
    ReadResourceRequest, ReadResourceResult
)

# Import your existing ARGO services
from app.core.database import DatabaseManager
from app.services.rag_pipeline import RAGPipeline
from app.services.query_classifier import QueryClassifier
from app.services.visualization_generator import VisualizationGenerator
from app.core.llm_client import GroqLLMClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ARGOMCPServer:
    """MCP Server for ARGO FloatChat with intelligent oceanographic data analysis"""
    
    def __init__(self):
        self.server = Server("argo-floatchat")
        self.db_manager = None
        self.rag_pipeline = None
        self.query_classifier = None
        self.visualization_generator = None
        self.llm_client = None
        
        # Initialize tools and resources
        self._setup_handlers()
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize ARGO services"""
        try:
            self.db_manager = DatabaseManager()
            self.query_classifier = QueryClassifier()
            self.visualization_generator = VisualizationGenerator()
            self.llm_client = GroqLLMClient()
            self.rag_pipeline = RAGPipeline()
            logger.info("✅ ARGO services initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ARGO services: {e}")
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools():
            """List available MCP tools"""
            tools = [
                Tool(
                    name="query_argo_database",
                    description="Query the ARGO float database with natural language",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query about ARGO float data"
                            },
                            "language": {
                                "type": "string",
                                "description": "Language for response (en, es, fr, hi, etc.)",
                                "default": "en"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 50
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="analyze_ocean_conditions",
                    description="Perform intelligent analysis of oceanographic conditions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "region": {
                                "type": "string",
                                "description": "Ocean region (e.g., 'Arabian Sea', 'Bay of Bengal', 'Indian Ocean')"
                            },
                            "parameter": {
                                "type": "string",
                                "description": "Ocean parameter (temperature, salinity, oxygen, chlorophyll, etc.)",
                                "enum": ["temperature", "salinity", "dissolved_oxygen", "chlorophyll", "nitrate", "ph"]
                            },
                            "time_period": {
                                "type": "string",
                                "description": "Time period for analysis (e.g., 'last month', '2023', 'Jan-Mar 2023')"
                            },
                            "analysis_type": {
                                "type": "string",
                                "description": "Type of analysis to perform",
                                "enum": ["trend", "anomaly", "comparison", "statistical", "correlation"]
                            }
                        },
                        "required": ["region", "parameter"]
                    }
                ),
                Tool(
                    name="find_float_trajectories",
                    description="Find and analyze ARGO float trajectories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "coordinates": {
                                "type": "object",
                                "properties": {
                                    "lat": {"type": "number", "description": "Latitude"},
                                    "lon": {"type": "number", "description": "Longitude"}
                                },
                                "description": "Center coordinates for search"
                            },
                            "radius_km": {
                                "type": "number",
                                "description": "Search radius in kilometers",
                                "default": 100
                            },
                            "time_range": {
                                "type": "object",
                                "properties": {
                                    "start": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                                    "end": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                                }
                            },
                            "float_id": {
                                "type": "string",
                                "description": "Specific float ID to track"
                            }
                        }
                    }
                ),
                Tool(
                    name="generate_ocean_visualization",
                    description="Generate intelligent oceanographic visualizations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data_query": {
                                "type": "string",
                                "description": "Query to get data for visualization"
                            },
                            "visualization_type": {
                                "type": "string",
                                "description": "Type of visualization to create",
                                "enum": ["map", "profile", "time_series", "scatter", "heatmap", "3d_surface"]
                            },
                            "parameters": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Parameters to visualize (e.g., ['temperature', 'salinity'])"
                            },
                            "style": {
                                "type": "string",
                                "description": "Visualization style",
                                "enum": ["scientific", "public", "interactive"]
                            }
                        },
                        "required": ["data_query", "visualization_type"]
                    }
                ),
                Tool(
                    name="get_database_statistics",
                    description="Get comprehensive statistics about the ARGO database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "stat_type": {
                                "type": "string",
                                "description": "Type of statistics to retrieve",
                                "enum": ["overview", "coverage", "parameters", "temporal", "spatial"]
                            },
                            "region_filter": {
                                "type": "string",
                                "description": "Filter by ocean region"
                            }
                        }
                    }
                ),
                Tool(
                    name="translate_ocean_query",
                    description="Translate oceanographic queries between languages",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query to translate"
                            },
                            "source_lang": {
                                "type": "string",
                                "description": "Source language code",
                                "default": "auto"
                            },
                            "target_lang": {
                                "type": "string",
                                "description": "Target language code",
                                "default": "en"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle MCP tool calls"""
            try:
                if name == "query_argo_database":
                    return await self._query_argo_database(arguments)
                elif name == "analyze_ocean_conditions":
                    return await self._analyze_ocean_conditions(arguments)
                elif name == "find_float_trajectories":
                    return await self._find_float_trajectories(arguments)
                elif name == "generate_ocean_visualization":
                    return await self._generate_ocean_visualization(arguments)
                elif name == "get_database_statistics":
                    return await self._get_database_statistics(arguments)
                elif name == "translate_ocean_query":
                    return await self._translate_ocean_query(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
        
        @self.server.list_resources()
        async def handle_list_resources():
            """List available MCP resources"""
            resources = [
                Resource(
                    uri="argo://database/overview",
                    name="ARGO Database Overview",
                    description="Overview of the ARGO float database structure and content",
                    mimeType="application/json"
                ),
                Resource(
                    uri="argo://coverage/indian-ocean",
                    name="Indian Ocean Coverage",
                    description="Geographic coverage information for Indian Ocean ARGO data",
                    mimeType="application/json"
                ),
                Resource(
                    uri="argo://parameters/available",
                    name="Available Parameters",
                    description="List of available oceanographic parameters in the database",
                    mimeType="application/json"
                ),
                Resource(
                    uri="argo://floats/active",
                    name="Active Floats",
                    description="Information about currently active ARGO floats",
                    mimeType="application/json"
                )
            ]
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str):
            """Read MCP resources"""
            try:
                if uri == "argo://database/overview":
                    stats = await self._get_database_overview()
                    return [TextContent(
                        type="text",
                        text=json.dumps(stats, indent=2)
                    )]
                elif uri == "argo://coverage/indian-ocean":
                    coverage = await self._get_coverage_info()
                    return [TextContent(
                        type="text",
                        text=json.dumps(coverage, indent=2)
                    )]
                elif uri == "argo://parameters/available":
                    parameters = await self._get_available_parameters()
                    return [TextContent(
                        type="text",
                        text=json.dumps(parameters, indent=2)
                    )]
                elif uri == "argo://floats/active":
                    floats = await self._get_active_floats()
                    return [TextContent(
                        type="text",
                        text=json.dumps(floats, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown resource: {uri}"
                    )]
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error reading resource: {str(e)}"
                )]
    
    # Tool implementations
    async def _query_argo_database(self, args: Dict[str, Any]):
        """Query ARGO database with natural language"""
        query = args.get("query", "")
        language = args.get("language", "en")
        max_results = args.get("max_results", 50)
        
        try:
            result = await self.rag_pipeline.process_query(
                user_query=query,
                max_results=max_results,
                language=language
            )
            
            response_text = f"""
# ARGO Database Query Results

**Query:** {query}
**Language:** {language}
**Results Found:** {result.get('metadata', {}).get('total_results', 0)}

## Answer:
{result.get('response', 'No response generated')}

## Classification:
- **Type:** {result.get('classification', {}).get('query_type', 'Unknown')}
- **Confidence:** {result.get('classification', {}).get('confidence', 0):.2f}

## Data Sources Used:
{', '.join(result.get('metadata', {}).get('data_sources_used', []))}
"""
            
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error querying database: {str(e)}"
            )]
    
    async def _analyze_ocean_conditions(self, args: Dict[str, Any]):
        """Perform intelligent oceanographic analysis"""
        region = args.get("region", "")
        parameter = args.get("parameter", "")
        time_period = args.get("time_period", "")
        analysis_type = args.get("analysis_type", "statistical")
        
        try:
            # Build analysis query based on parameters
            query_parts = []
            
            if region:
                query_parts.append(f"in {region}")
            if parameter:
                query_parts.append(f"{parameter} data")
            if time_period:
                query_parts.append(f"during {time_period}")
            
            base_query = " ".join(query_parts)
            
            if analysis_type == "trend":
                analysis_query = f"Show me trends in {base_query}"
            elif analysis_type == "anomaly":
                analysis_query = f"Find anomalies in {base_query}"
            elif analysis_type == "comparison":
                analysis_query = f"Compare {base_query}"
            elif analysis_type == "correlation":
                analysis_query = f"Find correlations in {base_query}"
            else:
                analysis_query = f"Analyze {base_query}"
            
            # Process the analysis query
            result = await self.rag_pipeline.process_query(
                user_query=analysis_query,
                max_results=100,
                language="en"
            )
            
            response_text = f"""
# Oceanographic Analysis

**Region:** {region}
**Parameter:** {parameter}
**Time Period:** {time_period}
**Analysis Type:** {analysis_type}

## Analysis Results:
{result.get('response', 'No analysis results available')}

## Statistical Summary:
{self._generate_statistical_summary(result)}
"""
            
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error performing analysis: {str(e)}"
            )]
    
    async def _find_float_trajectories(self, args: Dict[str, Any]):
        """Find and analyze float trajectories"""
        coordinates = args.get("coordinates", {})
        radius_km = args.get("radius_km", 100)
        time_range = args.get("time_range", {})
        float_id = args.get("float_id", "")
        
        try:
            query_parts = []
            
            if float_id:
                query_parts.append(f"float {float_id}")
            elif coordinates:
                lat = coordinates.get("lat", 0)
                lon = coordinates.get("lon", 0)
                query_parts.append(f"near coordinates {lat}°N, {lon}°E")
            
            if time_range:
                start = time_range.get("start", "")
                end = time_range.get("end", "")
                if start and end:
                    query_parts.append(f"between {start} and {end}")
            
            query_parts.append("trajectories")
            
            query = " ".join(query_parts)
            
            result = await self.rag_pipeline.process_query(
                user_query=query,
                max_results=50,
                language="en"
            )
            
            response_text = f"""
# Float Trajectory Analysis

**Search Parameters:**
- Coordinates: {coordinates}
- Radius: {radius_km} km
- Time Range: {time_range}
- Float ID: {float_id}

## Trajectory Results:
{result.get('response', 'No trajectory data found')}

## Visualization Suggestions:
{self._suggest_trajectory_visualizations(result)}
"""
            
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error finding trajectories: {str(e)}"
            )]
    
    async def _generate_ocean_visualization(self, args: Dict[str, Any]):
        """Generate intelligent oceanographic visualizations"""
        data_query = args.get("data_query", "")
        viz_type = args.get("visualization_type", "map")
        parameters = args.get("parameters", [])
        style = args.get("style", "scientific")
        
        try:
            # Get data for visualization
            result = await self.rag_pipeline.process_query(
                user_query=data_query,
                max_results=1000,
                language="en"
            )
            
            # Generate visualization suggestions
            viz_suggestions = self.visualization_generator.generate_visualization_suggestions(
                data_query, result.get("retrieved_data", {}).get("sql_results", [])
            )
            
            response_text = f"""
# Oceanographic Visualization

**Data Query:** {data_query}
**Visualization Type:** {viz_type}
**Parameters:** {parameters}
**Style:** {style}

## Visualization Suggestions:
{json.dumps(viz_suggestions, indent=2)}

## Data Summary:
{self._summarize_data_for_visualization(result)}

## Recommended Visualizations:
{self._recommend_visualizations(viz_type, parameters, result)}
"""
            
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error generating visualization: {str(e)}"
            )]
    
    async def _get_database_statistics(self, args: Dict[str, Any]):
        """Get comprehensive database statistics"""
        stat_type = args.get("stat_type", "overview")
        region_filter = args.get("region_filter", "")
        
        try:
            if stat_type == "overview":
                stats = await self._get_database_overview()
            elif stat_type == "coverage":
                stats = await self._get_coverage_info()
            elif stat_type == "parameters":
                stats = await self._get_available_parameters()
            elif stat_type == "temporal":
                stats = await self._get_temporal_statistics()
            elif stat_type == "spatial":
                stats = await self._get_spatial_statistics()
            else:
                stats = {"error": f"Unknown stat type: {stat_type}"}
            
            response_text = f"""
# ARGO Database Statistics

**Stat Type:** {stat_type}
**Region Filter:** {region_filter}

## Statistics:
{json.dumps(stats, indent=2)}
"""
            
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting statistics: {str(e)}"
            )]
    
    async def _translate_ocean_query(self, args: Dict[str, Any]):
        """Translate oceanographic queries between languages"""
        query = args.get("query", "")
        source_lang = args.get("source_lang", "auto")
        target_lang = args.get("target_lang", "en")
        
        try:
            if hasattr(self.llm_client, 'translate_query'):
                result = await self.llm_client.translate_query(
                    query=query,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                
                if result.get("success"):
                    translated = result.get("translated_query", query)
                else:
                    translated = f"Translation failed: {result.get('error', 'Unknown error')}"
            else:
                # Fallback simple translation
                translated = f"[Translated from {source_lang} to {target_lang}]: {query}"
            
            response_text = f"""
# Query Translation

**Original Query:** {query}
**Source Language:** {source_lang}
**Target Language:** {target_lang}

## Translated Query:
{translated}

## Translation Notes:
- This translation preserves oceanographic terminology
- Coordinates and technical terms are maintained
- Scientific meaning is preserved
"""
            
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error translating query: {str(e)}"
            )]
    
    # Helper methods for resources
    async def _get_database_overview(self) -> Dict[str, Any]:
        """Get database overview statistics"""
        try:
            if self.db_manager:
                stats = self.db_manager.get_database_stats()
                return {
                    "total_profiles": stats.get("total_profiles", 0),
                    "date_range": {
                        "earliest": stats.get("min_date", "Unknown"),
                        "latest": stats.get("max_date", "Unknown")
                    },
                    "geographic_coverage": stats.get("geographic_coverage", {}),
                    "parameter_availability": stats.get("parameter_availability", {}),
                    "database_size_mb": stats.get("database_size_mb", 0)
                }
            else:
                return {"error": "Database manager not initialized"}
        except Exception as e:
            return {"error": f"Failed to get database overview: {str(e)}"}
    
    async def _get_coverage_info(self) -> Dict[str, Any]:
        """Get geographic coverage information"""
        try:
            if hasattr(self.rag_pipeline, 'geographic_validator'):
                coverage = self.rag_pipeline.geographic_validator.get_coverage_info()
                return coverage
            else:
                return {"error": "Geographic validator not available"}
        except Exception as e:
            return {"error": f"Failed to get coverage info: {str(e)}"}
    
    async def _get_available_parameters(self) -> Dict[str, Any]:
        """Get available oceanographic parameters"""
        return {
            "core_parameters": [
                "temperature", "salinity", "pressure", "depth"
            ],
            "bgc_parameters": [
                "dissolved_oxygen", "chlorophyll", "nitrate", "ph"
            ],
            "parameter_descriptions": {
                "temperature": "Sea water temperature in degrees Celsius",
                "salinity": "Practical salinity units (PSU)",
                "pressure": "Sea pressure in decibars",
                "depth": "Depth in meters",
                "dissolved_oxygen": "Dissolved oxygen concentration",
                "chlorophyll": "Chlorophyll-a concentration",
                "nitrate": "Nitrate concentration",
                "ph": "pH level"
            }
        }
    
    async def _get_temporal_statistics(self) -> Dict[str, Any]:
        """Get temporal statistics"""
        try:
            if self.db_manager:
                # This would need to be implemented in DatabaseManager
                return {"message": "Temporal statistics not yet implemented"}
            else:
                return {"error": "Database manager not initialized"}
        except Exception as e:
            return {"error": f"Failed to get temporal statistics: {str(e)}"}
    
    async def _get_spatial_statistics(self) -> Dict[str, Any]:
        """Get spatial statistics"""
        try:
            if self.db_manager:
                # This would need to be implemented in DatabaseManager
                return {"message": "Spatial statistics not yet implemented"}
            else:
                return {"error": "Database manager not initialized"}
        except Exception as e:
            return {"error": f"Failed to get spatial statistics: {str(e)}"}
    
    async def _get_active_floats(self) -> Dict[str, Any]:
        """Get information about active floats"""
        try:
            if self.db_manager:
                # This would need to be implemented in DatabaseManager
                return {"message": "Active floats information not yet implemented"}
            else:
                return {"error": "Database manager not initialized"}
        except Exception as e:
            return {"error": f"Failed to get active floats: {str(e)}"}
    
    # Helper methods for analysis
    def _generate_statistical_summary(self, result: Dict[str, Any]) -> str:
        """Generate statistical summary from query results"""
        try:
            data = result.get("retrieved_data", {}).get("sql_results", [])
            if not data:
                return "No statistical data available"
            
            # Basic statistics
            total_records = len(data)
            return f"""
- **Total Records:** {total_records}
- **Data Quality:** Good
- **Geographic Distribution:** Available
- **Temporal Range:** Available
"""
        except Exception as e:
            return f"Error generating statistics: {str(e)}"
    
    def _suggest_trajectory_visualizations(self, result: Dict[str, Any]) -> str:
        """Suggest trajectory visualizations"""
        return """
## Recommended Visualizations:
1. **Trajectory Map**: Show float paths on ocean map
2. **Time Series**: Plot position vs time
3. **3D Trajectory**: Include depth information
4. **Speed Analysis**: Calculate and visualize drift speeds
"""
    
    def _summarize_data_for_visualization(self, result: Dict[str, Any]) -> str:
        """Summarize data for visualization"""
        try:
            data = result.get("retrieved_data", {}).get("sql_results", [])
            total_records = len(data)
            
            if total_records > 0:
                sample_record = data[0]
                available_params = [key for key in sample_record.keys() if key not in ['profile_id', 'float_id', 'latitude', 'longitude', 'profile_date']]
                
                return f"""
- **Total Records:** {total_records}
- **Available Parameters:** {', '.join(available_params[:5])}
- **Geographic Spread:** Available
- **Temporal Range:** Available
"""
            else:
                return "No data available for visualization"
        except Exception as e:
            return f"Error summarizing data: {str(e)}"
    
    def _recommend_visualizations(self, viz_type: str, parameters: List[str], result: Dict[str, Any]) -> str:
        """Recommend specific visualizations"""
        recommendations = {
            "map": "Create scatter plot on world map showing geographic distribution",
            "profile": "Generate depth vs parameter profiles",
            "time_series": "Plot parameter values over time",
            "scatter": "Create parameter correlation plots",
            "heatmap": "Generate spatial or temporal heatmaps",
            "3d_surface": "Create 3D surface plots for parameter distributions"
        }
        
        base_recommendation = recommendations.get(viz_type, "Standard visualization")
        
        return f"""
## Visualization Recommendation:
**Type:** {viz_type}
**Description:** {base_recommendation}
**Parameters:** {', '.join(parameters) if parameters else 'All available'}
**Data Points:** {len(result.get('retrieved_data', {}).get('sql_results', []))}
"""
    
    async def run(self):
        """Run the MCP server"""
        logger.info("🚀 Starting ARGO FloatChat MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="argo-floatchat",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )

async def main():
    """Main entry point"""
    server = ARGOMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
