"""
Geographic Coverage Validator
Validates queries against available data coverage to prevent hallucination
"""
import logging
from typing import Dict, List, Tuple, Optional
import re

logger = logging.getLogger(__name__)


class GeographicValidator:
    """Validates geographic queries against available data coverage"""
    
    def __init__(self):
        # Define ocean regions and their longitude ranges
        self.ocean_regions = {
            'atlantic': {
                'longitude_range': (-80, 20),
                'description': 'Atlantic Ocean (-80°W to 20°E)',
                'has_data': False  # Based on our database analysis
            },
            'pacific': {
                'longitude_range': (160, -120),  # 160°E to 120°W (crosses dateline)
                'description': 'Pacific Ocean (160°E to 120°W)',
                'has_data': False
            },
            'indian': {
                'longitude_range': (20, 160),
                'description': 'Indian Ocean (20°E to 160°E)',
                'has_data': True  # Based on our database analysis
            },
            'arctic': {
                'longitude_range': (-180, 180),
                'description': 'Arctic Ocean (all longitudes, high latitudes)',
                'has_data': False
            },
            'mediterranean': {
                'longitude_range': (-10, 40),
                'description': 'Mediterranean Sea (-10°W to 40°E)',
                'has_data': False
            }
        }
        
        # Available data coverage from our database
        self.available_coverage = {
            'longitude_range': (20.003, 144.99976),
            'latitude_range': (-59.99932, 26.852016),
            'total_profiles': 122215,
            'ocean_regions': ['indian']
        }
    
    def extract_ocean_region_from_query(self, query: str) -> List[str]:
        """Extract mentioned ocean regions from query"""
        query_lower = query.lower()
        mentioned_regions = []
        
        # Check for ocean region keywords
        ocean_keywords = {
            'atlantic': ['atlantic', 'atlantic ocean'],
            'pacific': ['pacific', 'pacific ocean'],
            'indian': ['indian', 'indian ocean'],
            'arctic': ['arctic', 'arctic ocean'],
            'mediterranean': ['mediterranean', 'mediterranean sea']
        }
        
        for region, keywords in ocean_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                mentioned_regions.append(region)
        
        return mentioned_regions
    
    def validate_geographic_coverage(self, query: str) -> Dict[str, any]:
        """Validate if query requests data from available regions"""
        mentioned_regions = self.extract_ocean_region_from_query(query)
        
        if not mentioned_regions:
            # No specific ocean mentioned, assume general query is OK
            return {
                'is_valid': True,
                'message': None,
                'available_regions': ['indian'],
                'unavailable_regions': []
            }
        
        unavailable_regions = []
        available_regions = []
        
        for region in mentioned_regions:
            if region in self.ocean_regions:
                if self.ocean_regions[region]['has_data']:
                    available_regions.append(region)
                else:
                    unavailable_regions.append(region)
        
        if unavailable_regions:
            unavailable_descriptions = [
                self.ocean_regions[region]['description'] 
                for region in unavailable_regions
            ]
            available_descriptions = [
                self.ocean_regions[region]['description'] 
                for region in available_regions
            ]
            
            message = f"I don't have data for {', '.join(unavailable_descriptions)}. "
            if available_descriptions:
                message += f"Our database only contains data from {', '.join(available_descriptions)}. "
                message += "Would you like to explore data from these regions instead?"
            else:
                message += "Our database only contains data from the Indian Ocean region (20°E to 160°E longitude)."
            
            return {
                'is_valid': False,
                'message': message,
                'available_regions': available_regions,
                'unavailable_regions': unavailable_regions
            }
        
        return {
            'is_valid': True,
            'message': None,
            'available_regions': available_regions,
            'unavailable_regions': []
        }
    
    def get_coverage_info(self) -> Dict[str, any]:
        """Get information about available data coverage"""
        return {
            'total_profiles': self.available_coverage['total_profiles'],
            'longitude_range': self.available_coverage['longitude_range'],
            'latitude_range': self.available_coverage['latitude_range'],
            'ocean_regions': self.available_coverage['ocean_regions'],
            'description': 'Indian Ocean region (20°E to 160°E longitude, -60°S to 27°N latitude)'
        }
