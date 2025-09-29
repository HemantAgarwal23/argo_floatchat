"""
backend_adapter.py
Fixed Backend adapter for FloatChat Frontend
Handles integration with your ARGO AI backend services
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
import json
import logging
from datetime import datetime
import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendAdapter:
    """Adapter class to interface with ARGO AI backend services"""
    
    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or os.getenv("BACKEND_URL", "http://localhost:8000")
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'FloatChat-Frontend/1.0'
        })
        
        # Try to import backend services for direct integration
        self.direct_mode = self._setup_direct_mode()
        logger.info(f"Backend adapter initialized in {'direct' if self.direct_mode else 'HTTP'} mode")
    
    def _setup_direct_mode(self) -> bool:
        """Setup direct backend integration if possible"""
        try:
            # Add backend to Python path
            backend_path = Path(__file__).parent.parent / "backend"
            if backend_path.exists():
                sys.path.append(str(backend_path))
            
            # Import your actual backend services
            from app.services.rag_pipeline import rag_pipeline
            from app.core.llm_client import llm_client
            from app.core.database import db_manager
            from app.core.vector_db import vector_db_manager
            
            self.rag_pipeline = rag_pipeline
            self.llm_client = llm_client
            self.db_manager = db_manager
            self.vector_db_manager = vector_db_manager
            
            logger.info("✅ Direct backend integration successful")
            return True
            
        except ImportError as e:
            logger.info(f"ℹ️ Direct backend integration not available: {e}")
            logger.info("Will use HTTP API mode")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Error setting up direct mode: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check backend health and services"""
        try:
            if self.direct_mode:
                return self._health_check_direct()
            else:
                return self._health_check_http()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "backend_available": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "mode": "error"
            }
    
    def _health_check_direct(self) -> Dict[str, Any]:
        """Direct health check using backend services"""
        try:
            # Check if services are available
            health = self.rag_pipeline.health_check() if hasattr(self.rag_pipeline, 'health_check') else {}
            
            services = {
                "rag_pipeline": hasattr(self, 'rag_pipeline'),
                "llm_client": hasattr(self, 'llm_client'),
                "database": hasattr(self, 'db_manager'),
                "vector_store": hasattr(self, 'vector_db_manager')
            }
            
            return {
                "backend_available": True,
                "mode": "direct",
                "services": services,
                "health": health,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        except Exception as e:
            return {
                "backend_available": False,
                "mode": "direct",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _health_check_http(self) -> Dict[str, Any]:
        """HTTP health check"""
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                data["backend_available"] = True
                data["mode"] = "http"
                return data
            else:
                return {
                    "backend_available": False,
                    "mode": "http",
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "backend_available": False,
                "mode": "http",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def process_natural_language_query(self, query: str, filters: Dict = None, language: Optional[str] = None) -> Dict[str, Any]:
        """Process natural language query"""
        try:
            if self.direct_mode:
                return self._process_query_direct(query, filters)
            else:
                return self._process_query_http(query, filters, language)
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"I encountered an error processing your query: {str(e)}",
                "suggestions": [
                    "Try rephrasing your query",
                    "Check if the backend service is running",
                    "Verify your network connection"
                ]
            }
    
    def _process_query_direct(self, query: str, filters: Dict = None) -> Dict[str, Any]:
        """Process query using direct backend services"""
        try:
            # Process through your RAG pipeline
            import asyncio
            
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.rag_pipeline.process_query(query))
            finally:
                loop.close()
            
            # Build visualization from backend payload if available
            backend_vis = result.get("visualization") or {}
            viz_config = {}
            if backend_vis:
                # Prefer backend-provided coordinates payload
                coords = backend_vis.get("coordinates") or []
                if coords:
                    records = [{"latitude": lat, "longitude": lon} for lat, lon in coords]
                    viz_config = {
                        "type": "map",
                        "data": records,
                        "title": "ARGO Float Locations",
                        "color_by": None
                    }
                else:
                    # Fallback to legacy construction
                    viz_config = self._create_visualization_config(result.get("retrieved_data", {}))
            else:
                viz_config = self._create_visualization_config(result.get("retrieved_data", {}))

            # Format response for frontend
            return {
                "success": True,
                "response": result.get("response", "Query processed successfully"),
                "data": result.get("retrieved_data", {}),
                "visualization": viz_config,
                "metadata": result.get("metadata", {}),
                "query_id": f"query_{datetime.now().timestamp()}",
                "processing_time": 0.5
            }
            
        except Exception as e:
            logger.error(f"Direct query processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Query processing failed: {str(e)}"
            }
    
    def _process_query_http(self, query: str, filters: Dict = None, language: Optional[str] = None) -> Dict[str, Any]:
        """Process query using HTTP API - Fixed to handle actual backend response"""
        try:
            payload = {
                "query": query,
                "max_results": min(filters.get("max_results", 100), 100) if filters else 100,
                "include_visualizations": True
            }
            if language:
                payload["language"] = language
            
            # Use the correct endpoint
            response = self.session.post(
                f"{self.backend_url}/api/v1/query/process",
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Debug: Print raw response to see what we're getting
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Raw response text: {response.text[:500]}...")  # First 500 chars
            
            result = response.json()
            # Echo language to UI if backend didn't include it
            if language and isinstance(result, dict) and 'language' not in result:
                result['language'] = language
            
            # Debug: Print parsed JSON structure
            print(f"Parsed JSON keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            
            # Your backend already returns the correct format, so we can use it directly
            if isinstance(result, dict) and result.get("success"):
                # The backend response is already in the correct format
                return result
            else:
                # Fallback error handling
                return {
                    "success": False,
                    "error": "Invalid response format from backend",
                    "response": f"Backend returned unexpected format: {type(result)}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP query processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to connect to backend service: {str(e)}"
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "success": False,
                "error": f"JSON decode error: {str(e)}",
                "response": "Backend returned invalid JSON"
            }
        except Exception as e:
            logger.error(f"Unexpected error in HTTP query processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Unexpected error occurred: {str(e)}"
            }
    
    def _create_visualization_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualization configuration from backend data"""
        try:
            # First, check if we have the new visualization payload from backend
            backend_vis = data.get("visualization", {})
            if backend_vis and backend_vis.get("coordinates"):
                coordinates = backend_vis.get("coordinates", [])
                if coordinates:
                    # Use the coordinates from the backend visualization
                    return {
                        "type": "map",
                        "coordinates": coordinates,
                        "title": "ARGO Float Locations",
                        "geojson": backend_vis.get("geojson"),
                        "plotly_code": backend_vis.get("plotly_code"),
                        "time_series": backend_vis.get("time_series", [])
                    }
            
            # Fallback to old method using sql_results
            sql_results = data.get("sql_results", [])
            if not sql_results:
                return {}
            
            # Check if we have coordinate data
            first_record = sql_results[0] if sql_results else {}
            
            if "latitude" in first_record and "longitude" in first_record:
                return {
                    "type": "map",
                    "data": sql_results,
                    "title": "ARGO Float Locations",
                    "color_by": "temperature" if "temperature" in first_record else None
                }
            else:
                return {
                    "type": "scatter",
                    "data": sql_results,
                    "title": "ARGO Data Visualization"
                }
        except Exception as e:
            logger.error(f"Visualization config creation failed: {e}")
            return {}
    
    def get_dataset_metadata(self) -> Dict[str, Any]:
        """Get comprehensive dataset metadata"""
        try:
            if self.direct_mode:
                return self._get_metadata_direct()
            else:
                return self._get_metadata_http()
        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {}
            }
    
    def _get_metadata_direct(self) -> Dict[str, Any]:
        """Get metadata using direct backend services"""
        try:
            db_stats = self.db_manager.get_database_stats()
            vector_stats = self.vector_db_manager.get_collection_stats()
            
            metadata = {
                "database": db_stats,
                "vector_database": vector_stats,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_metadata_http(self) -> Dict[str, Any]:
        """Get metadata using HTTP API"""
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/data/metadata", timeout=10)
            response.raise_for_status()
            return {
                "success": True,
                "metadata": response.json(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def export_data(self, query: str, export_format: str = "csv") -> Optional[Dict[str, Any]]:
        """Export data using the new export API"""
        try:
            if self.direct_mode:
                return self._export_direct_new(query, export_format)
            else:
                return self._export_http_new(query, export_format)
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None

    def export_query_results(self, query_id: str, format: str = "csv") -> Optional[bytes]:
        """Export query results in specified format (legacy method)"""
        try:
            if self.direct_mode:
                return self._export_direct(query_id, format)
            else:
                return self._export_http(query_id, format)
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None
    
    def _export_direct(self, query_id: str, format: str) -> Optional[bytes]:
        """Export using direct backend services"""
        try:
            # This would need to be implemented in your backend
            logger.warning("Direct export not implemented yet")
            return None
        except Exception as e:
            logger.error(f"Direct export failed: {e}")
            return None
    
    def _export_http_new(self, query: str, export_format: str) -> Optional[Dict[str, Any]]:
        """Export using new HTTP API"""
        try:
            response = self.session.post(
                f"{self.backend_url}/api/v1/export",
                json={
                    "query": query,
                    "export_format": export_format,
                    "include_metadata": True
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HTTP export failed: {e}")
            return None

    def _export_direct_new(self, query: str, export_format: str) -> Optional[Dict[str, Any]]:
        """Export using direct backend services (new method)"""
        try:
            # This would need to be implemented in your backend
            logger.warning("Direct export not implemented yet")
            return None
        except Exception as e:
            logger.error(f"Direct export failed: {e}")
            return None

    def download_export(self, export_id: str, export_format: str) -> Optional[bytes]:
        """Download exported data file"""
        try:
            if self.direct_mode:
                return self._download_export_direct(export_id, export_format)
            else:
                return self._download_export_http(export_id, export_format)
        except Exception as e:
            logger.error(f"Download export failed: {e}")
            return None

    def _download_export_http(self, export_id: str, export_format: str) -> Optional[bytes]:
        """Download export using HTTP API"""
        try:
            response = self.session.get(
                f"{self.backend_url}/api/v1/export/{export_id}/download",
                params={"format": export_format},
                timeout=60
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"HTTP download export failed: {e}")
            return None

    def _download_export_direct(self, export_id: str, export_format: str) -> Optional[bytes]:
        """Download export using direct backend services"""
        try:
            # This would need to be implemented in your backend
            logger.warning("Direct download export not implemented yet")
            return None
        except Exception as e:
            logger.error(f"Direct download export failed: {e}")
            return None

    def _export_http(self, query_id: str, format: str) -> Optional[bytes]:
        """Export using HTTP API (legacy method)"""
        try:
            response = self.session.post(
                f"{self.backend_url}/api/v1/export",
                json={"query_id": query_id, "format": format},
                timeout=60
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"HTTP export failed: {e}")
            return None
    
    def generate_bar_chart(self, sql_results: List[Dict[str, Any]], chart_type: str = "auto", user_query: str = "") -> Dict[str, Any]:
        """Generate bar chart visualization from SQL results"""
        try:
            if self.direct_mode:
                return self._generate_bar_chart_direct(sql_results, chart_type, user_query)
            else:
                return self._generate_bar_chart_http(sql_results, chart_type, user_query)
        except Exception as e:
            logger.error(f"Bar chart generation failed: {e}")
            return {"error": f"Failed to generate bar chart: {str(e)}"}
    
    def _generate_bar_chart_direct(self, sql_results: List[Dict[str, Any]], chart_type: str, user_query: str = "") -> Dict[str, Any]:
        """Generate bar chart using direct backend services"""
        try:
            # Import visualization generator
            from app.services.visualization_generator import visualization_generator
            
            result = visualization_generator.generate_bar_chart(sql_results, chart_type, user_query)
            return result
            
        except Exception as e:
            logger.error(f"Direct bar chart generation failed: {e}")
            return {"error": f"Direct bar chart generation failed: {str(e)}"}
    
    def _generate_bar_chart_http(self, sql_results: List[Dict[str, Any]], chart_type: str, user_query: str = "") -> Dict[str, Any]:
        """Generate bar chart using HTTP API"""
        try:
            payload = {
                "sql_results": sql_results,
                "chart_type": chart_type,
                "user_query": user_query
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/v1/visualizations/bar-chart",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"HTTP bar chart generation failed: {e}")
            return {"error": f"HTTP bar chart generation failed: {str(e)}"}
    
    def generate_data_table(self, sql_results: List[Dict[str, Any]], table_type: str = "auto") -> Dict[str, Any]:
        """Generate data table visualization from SQL results"""
        try:
            if self.direct_mode:
                return self._generate_data_table_direct(sql_results, table_type)
            else:
                return self._generate_data_table_http(sql_results, table_type)
        except Exception as e:
            logger.error(f"Data table generation failed: {e}")
            return {"error": f"Failed to generate data table: {str(e)}"}
    
    def _generate_data_table_direct(self, sql_results: List[Dict[str, Any]], table_type: str) -> Dict[str, Any]:
        """Generate data table using direct backend services"""
        try:
            # Import visualization generator
            from app.services.visualization_generator import visualization_generator
            
            result = visualization_generator.generate_data_table(sql_results, table_type)
            return result
            
        except Exception as e:
            logger.error(f"Direct data table generation failed: {e}")
            return {"error": f"Direct data table generation failed: {str(e)}"}
    
    def _generate_data_table_http(self, sql_results: List[Dict[str, Any]], table_type: str) -> Dict[str, Any]:
        """Generate data table using HTTP API"""
        try:
            payload = {
                "sql_results": sql_results,
                "table_type": table_type
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/v1/visualizations/data-table",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"HTTP data table generation failed: {e}")
            return {"error": f"HTTP data table generation failed: {str(e)}"}
    