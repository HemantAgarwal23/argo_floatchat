#frontend_config.py
import os
from typing import Dict, Any, List

class FrontendConfig:
    """Configuration class for frontend application"""
    
    # Backend connection
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    BACKEND_TIMEOUT = int(os.getenv("BACKEND_TIMEOUT", "30"))
    
    # UI Configuration
    PAGE_TITLE = "FloatChat - ARGO Ocean Data Explorer"
    PAGE_ICON = "🌊"
    LAYOUT = "wide"
    
    # Chat configuration
    MAX_MESSAGE_LENGTH = 2000
    MAX_CHAT_HISTORY = 100
    
    # Visualization defaults
    DEFAULT_MAP_ZOOM = 3
    DEFAULT_PLOT_HEIGHT = 500
    COLOR_PALETTE = [
        "#06b6d4", "#3b82f6", "#8b5cf6", "#f59e0b", 
        "#ef4444", "#10b981", "#f97316", "#84cc16"
    ]
    
    # Export settings
    EXPORT_FORMATS = ["csv", "json", "netcdf", "xlsx"]
    MAX_EXPORT_RECORDS = 50000
    
    # Quick queries
    QUICK_QUERIES = [
        "Show me temperature profiles in the Indian Ocean for the last month",
        "Compare salinity data near the equator between 2022 and 2023",
        "Find the nearest ARGO floats to coordinates 20°N, 70°E",
        "Display BGC oxygen levels in the Arabian Sea",
        "Show float trajectories in the Bay of Bengal",
        "What's the temperature anomaly in the equatorial Pacific?",
        "Compare chlorophyll levels in different ocean regions",
        "Show deep water temperature trends over the last year"
    ]
    
    # Geographic regions for quick access
    REGIONS = {
        "Indian Ocean": {"lat": [-40, 30], "lon": [20, 120]},
        "Arabian Sea": {"lat": [0, 30], "lon": [50, 80]},
        "Bay of Bengal": {"lat": [5, 25], "lon": [80, 100]},
        "Equatorial Pacific": {"lat": [-10, 10], "lon": [120, -80]},
        "North Atlantic": {"lat": [20, 70], "lon": [-80, 0]},
        "Southern Ocean": {"lat": [-70, -40], "lon": [-180, 180]}
    }
    
    # Parameter configurations
    PARAMETER_CONFIG = {
        'temperature': {
            'color': '#ff6b6b',
            'unit': '°C',
            'title': 'Temperature',
            'range': [-2, 35],
            'colorscale': 'RdYlBu_r'
        },
        'salinity': {
            'color': '#4ecdc4',
            'unit': 'PSU',
            'title': 'Salinity',
            'range': [30, 37],
            'colorscale': 'Viridis'
        },
        'pressure': {
            'color': '#45b7d1',
            'unit': 'dbar',
            'title': 'Pressure',
            'range': [0, 2000],
            'colorscale': 'Blues'
        },
        'oxygen': {
            'color': '#f9ca24',
            'unit': 'μmol/kg',
            'title': 'Dissolved Oxygen',
            'range': [0, 400],
            'colorscale': 'Plasma'
        },
        'chlorophyll': {
            'color': '#6c5ce7',
            'unit': 'mg/m³',
            'title': 'Chlorophyll-a',
            'range': [0, 10],
            'colorscale': 'Greens'
        },
        'nitrate': {
            'color': '#fd79a8',
            'unit': 'μmol/kg',
            'title': 'Nitrate',
            'range': [0, 50],
            'colorscale': 'Reds'
        },
        'ph': {
            'color': '#00b894',
            'unit': 'pH units',
            'title': 'pH',
            'range': [7.5, 8.5],
            'colorscale': 'RdYlGn'
        }
    }
    
    @classmethod
    def get_api_endpoints(cls) -> Dict[str, str]:
        """Get all API endpoints"""
        return {
            "health": f"{cls.BACKEND_URL}/health",
            "query": f"{cls.BACKEND_URL}/api/v1/query",
            "data": f"{cls.BACKEND_URL}/api/v1/data",
            "visualization": f"{cls.BACKEND_URL}/api/v1/visualization",
            "metadata": f"{cls.BACKEND_URL}/api/v1/metadata",
            "export": f"{cls.BACKEND_URL}/api/v1/export",
            "upload": f"{cls.BACKEND_URL}/api/v1/upload",
            "status": f"{cls.BACKEND_URL}/api/v1/status"
        }
    
    @classmethod
    def get_parameter_info(cls, parameter: str) -> Dict[str, Any]:
        """Get parameter configuration"""
        return cls.PARAMETER_CONFIG.get(parameter, {
            'color': '#06b6d4',
            'unit': '',
            'title': parameter.title(),
            'range': [0, 100],
            'colorscale': 'Viridis'
        })