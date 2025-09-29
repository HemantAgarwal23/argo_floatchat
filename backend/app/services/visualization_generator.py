"""
visualization_generator.py
Generate coordinate arrays, Plotly code, GeoJSON, time series, bar charts, and tables for trajectories.
Uses Hugging Face for code generation when beneficial, with robust local fallbacks.
Enhanced with intelligent data aggregation and statistical analysis.
"""
from typing import Dict, Any, List, Tuple, Optional
import json
import structlog
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.core.multi_llm_client import multi_llm_client


logger = structlog.get_logger()


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


class VisualizationGenerator:
    def extract_coordinates(self, sql_results: List[Dict[str, Any]]) -> List[List[float]]:
        """Extract [[lat, lon], ...] from SQL rows, ordered by date if present."""
        if not sql_results:
            return []
        def sort_key(row: Dict[str, Any]):
            return row.get('profile_date') or row.get('profile_time') or 0
        rows = sorted(sql_results, key=sort_key)
        coords: List[List[float]] = []
        for r in rows:
            lat = r.get('latitude')
            lon = r.get('longitude')
            if lat is not None and lon is not None:
                coords.append([float(lat), float(lon)])
        return coords

    def extract_time_series(self, sql_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return [{timestamp, latitude, longitude, profile_id, float_id}]"""
        series: List[Dict[str, Any]] = []
        for r in sql_results:
            # Ensure all values are JSON serializable
            profile_date = r.get('profile_date')
            series.append({
                "timestamp": str(profile_date) if profile_date is not None else "Unknown",
                "latitude": r.get('latitude'),
                "longitude": r.get('longitude'),
                "profile_id": r.get('profile_id'),
                "float_id": r.get('float_id'),
            })
        return series

    def build_geojson(self, coordinates: List[List[float]]) -> Dict[str, Any]:
        """Generate a simple LineString GeoJSON from coordinates."""
        geo_coords = [[lon, lat] for lat, lon in coordinates]
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": geo_coords
                    },
                    "properties": {
                        "name": "ARGO Trajectory"
                    }
                }
            ]
        }

    def generate_plotly_code(self, coordinates: List[List[float]]) -> str:
        """Use HF code model to generate Plotly code. Fallback to deterministic template."""
        # Minimal data sample to keep prompt size reasonable
        sample = coordinates[:100]
        prompt = (
            "You are a Python visualization assistant. Generate standalone Plotly code that creates an interactive map "
            "with a trajectory polyline from given latitude/longitude pairs. Use scattergeo with mode='lines+markers', "
            "center view to the mean coordinate, and add coastline. Input coordinates are a Python list of [lat, lon].\n\n"
            f"Coordinates (list of [lat, lon]): {json.dumps(sample)}\n\n"
            "Return ONLY Python code that can be executed as-is (imports included)."
        )
        messages = [
            {"role": "system", "content": "Generate high-quality Python Plotly code for geographic trajectories."},
            {"role": "user", "content": prompt}
        ]
        try:
            code = multi_llm_client.generate_response(messages, user_query="plotly trajectory map", use_code_model=True, temperature=0.1, max_tokens=800)
            return code
        except Exception as e:
            logger.warning("HF code generation failed; using fallback template", error=str(e))
            # Deterministic fallback
            return (
                "import plotly.graph_objects as go\n"
                "coordinates = " + json.dumps(sample) + "\n"
                "lats = [c[0] for c in coordinates]\n"
                "lons = [c[1] for c in coordinates]\n"
                "fig = go.Figure(go.Scattergeo(lat=lats, lon=lons, mode='lines+markers'))\n"
                "fig.update_layout(geo=dict(showcoastlines=True, showcountries=True))\n"
                "fig.show()\n"
            )

    def generate_leaflet_code(self, coordinates: List[List[float]], float_data: List[Dict[str, Any]] = None) -> str:
        """Generate Leaflet.js code for interactive map with ARGO float trajectories."""
        if not coordinates:
            return ""
        
        # Calculate map center and bounds
        lats = [c[0] for c in coordinates]
        lons = [c[1] for c in coordinates]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Create coordinate pairs for the polyline
        coord_pairs = [[c[1], c[0]] for c in coordinates]  # Leaflet uses [lon, lat]
        
        # Generate marker data if available
        markers_data = []
        if float_data:
            for i, data in enumerate(float_data[:50]):  # Limit to 50 markers for performance
                if i < len(coordinates):
                    lat, lon = coordinates[i]
                    float_id = data.get('float_id', f'Float {i+1}')
                    date = data.get('profile_date', 'Unknown date')
                    markers_data.append({
                        'lat': lat,
                        'lon': lon,
                        'float_id': float_id,
                        'date': str(date)  # Convert date to string for JSON serialization
                    })
        
        leaflet_code = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ARGO Float Trajectories</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ height: 100vh; width: 100%; }}
        .float-popup {{ font-family: Arial, sans-serif; }}
        .float-popup h3 {{ margin: 0 0 5px 0; color: #2c3e50; }}
        .float-popup p {{ margin: 2px 0; color: #7f8c8d; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Initialize map
        const map = L.map('map').setView([{center_lat}, {center_lon}], 6);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        // Create trajectory polyline
        const trajectory = L.polyline({json.dumps(coord_pairs)}, {{
            color: '#e74c3c',
            weight: 3,
            opacity: 0.8
        }}).addTo(map);
        
        // Add markers for each float position
        const markers = {json.dumps(markers_data)};
        markers.forEach(marker => {{
            const popup = `
                <div class="float-popup">
                    <h3>${{marker.float_id}}</h3>
                    <p><strong>Date:</strong> ${{marker.date}}</p>
                    <p><strong>Position:</strong> ${{marker.lat.toFixed(3)}}°N, ${{marker.lon.toFixed(3)}}°E</p>
                </div>
            `;
            
            L.marker([marker.lat, marker.lon])
                .addTo(map)
                .bindPopup(popup);
        }});
        
        // Fit map to show all data
        if (trajectory.getLatLngs().length > 0) {{
            map.fitBounds(trajectory.getBounds());
        }}
        
        // Add legend
        const legend = L.control({{position: 'bottomright'}});
        legend.onAdd = function(map) {{
            const div = L.DomUtil.create('div', 'info legend');
            div.innerHTML = `
                <div style="background: white; padding: 10px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2);">
                    <h4 style="margin: 0 0 5px 0;">ARGO Float Trajectories</h4>
                    <p style="margin: 2px 0;"><span style="color: #e74c3c; font-weight: bold;">━</span> Trajectory Path</p>
                    <p style="margin: 2px 0;"><span style="color: #2c3e50;">●</span> Float Positions</p>
                    <p style="margin: 2px 0; font-size: 12px; color: #7f8c8d;">Total Points: {len(coordinates)}</p>
                </div>
            `;
            return div;
        }};
        legend.addTo(map);
    </script>
</body>
</html>
"""
        return leaflet_code.strip()

    def generate_bar_chart(self, sql_results: List[Dict[str, Any]], chart_type: str = "auto", user_query: str = "") -> Dict[str, Any]:
        """Generate intelligent bar charts from SQL results"""
        if not sql_results:
            return {"error": "No data available for bar chart"}
        
        try:
            df = pd.DataFrame(sql_results)
            
            # Auto-detect chart type if not specified
            if chart_type == "auto":
                chart_type = self._detect_bar_chart_type(df, sql_results, user_query)
            
            if chart_type == "year_comparison":
                result = self._create_year_comparison_chart(df, user_query)
            elif chart_type == "parameter_comparison":
                result = self._create_parameter_comparison_chart(df)
            elif chart_type == "temporal_distribution":
                result = self._create_temporal_distribution_chart(df)
            elif chart_type == "regional_comparison":
                result = self._create_regional_comparison_chart(df)
            elif chart_type == "depth_analysis":
                result = self._create_depth_analysis_chart(df)
            elif chart_type == "float_statistics":
                result = self._create_float_statistics_chart(df)
            elif chart_type == "float_specific":
                result = self._create_float_specific_chart(df)
            else:
                result = self._create_generic_bar_chart(df)
            
            # Convert numpy types to Python native types for JSON serialization
            return convert_numpy_types(result)
                
        except Exception as e:
            logger.error("Error generating bar chart", error=str(e))
            return {"error": f"Failed to generate bar chart: {str(e)}"}

    def generate_data_table(self, sql_results: List[Dict[str, Any]], table_type: str = "auto") -> Dict[str, Any]:
        """Generate intelligent data tables from SQL results"""
        if not sql_results:
            return {"error": "No data available for table"}
        
        try:
            df = pd.DataFrame(sql_results)
            
            # Auto-detect table type if not specified
            if table_type == "auto":
                table_type = self._detect_table_type(df, sql_results)
            
            if table_type == "summary_statistics":
                result = self._create_summary_statistics_table(df)
            elif table_type == "detailed_records":
                result = self._create_detailed_records_table(df)
            elif table_type == "comparison_table":
                result = self._create_comparison_table(df)
            elif table_type == "aggregated_data":
                result = self._create_aggregated_data_table(df)
            else:
                result = self._create_generic_table(df)
            
            # Convert numpy types to Python native types for JSON serialization
            return convert_numpy_types(result)
                
        except Exception as e:
            logger.error("Error generating data table", error=str(e))
            return {"error": f"Failed to generate table: {str(e)}"}

    def _detect_bar_chart_type(self, df: pd.DataFrame, sql_results: List[Dict[str, Any]], user_query: str = "") -> str:
        """Intelligently detect the best bar chart type for the data"""
        try:
            query_lower = user_query.lower()
            
            # Check for year comparison queries first (highest priority)
            year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', user_query)
            unique_years = sorted(list({int(y) for y in year_matches}))
            is_year_comparison = len(unique_years) >= 2 and any(w in query_lower for w in ["compare", "versus", "vs", "compare between", "between"])
            
            if is_year_comparison:
                # Check if this is a parameter comparison across years
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                oceanographic_params = ['temperature', 'salinity', 'dissolved_oxygen', 'pressure', 'ph', 'nitrate', 'chlorophyll', 'temp', 'sal']
                param_cols = [col for col in numeric_cols if any(param in col.lower() for param in oceanographic_params)]
                
                if len(param_cols) >= 1:  # At least one oceanographic parameter
                    return "year_comparison"
            
            # Check for parameter comparison queries (high priority)
            parameter_comparison_keywords = ['compare', 'comparison', 'vs', 'versus', 'temperature', 'salinity', 'parameters']
            is_parameter_comparison_query = any(keyword in query_lower for keyword in parameter_comparison_keywords)
            
            # Check if query explicitly mentions both temperature and salinity
            has_both_temp_sal = 'temperature' in query_lower and 'salinity' in query_lower
            
            if is_parameter_comparison_query or has_both_temp_sal:
                # Check for oceanographic parameters in data
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                oceanographic_params = ['temperature', 'salinity', 'dissolved_oxygen', 'pressure', 'ph', 'nitrate', 'chlorophyll', 'temp', 'sal']
                param_cols = [col for col in numeric_cols if any(param in col.lower() for param in oceanographic_params)]
                
                if len(param_cols) >= 1:  # At least one oceanographic parameter
                    return "parameter_comparison"
            
            # Check for multiple parameters (comparison) - general case
            if len(param_cols) >= 2:
                return "parameter_comparison"
            
            # Check for temporal data (only if not year comparison)
            if 'profile_date' in df.columns or 'date' in df.columns:
                return "temporal_distribution"
            
            # Check for regional data
            if 'latitude' in df.columns and 'longitude' in df.columns:
                return "regional_comparison"
            
            # Check for depth data
            if 'pressure' in df.columns or 'depth' in df.columns:
                return "depth_analysis"
            
            # Check for single float with surface/deep data
            surface_deep_cols = [col for col in df.columns if any(x in col.lower() for x in ['surface_temp', 'deep_temp', 'surface_sal', 'deep_sal'])]
            if ('float_id' in df.columns and df['float_id'].nunique() == 1 and surface_deep_cols):
                return "float_specific"
            
            # Check for multiple floats
            if 'float_id' in df.columns and df['float_id'].nunique() > 1:
                return "float_statistics"
            
            return "generic"
            
        except Exception as e:
            logger.warning("Error detecting bar chart type", error=str(e))
            return "generic"

    def _detect_table_type(self, df: pd.DataFrame, sql_results: List[Dict[str, Any]]) -> str:
        """Intelligently detect the best table type for the data"""
        try:
            # If we have many records, create summary
            if len(df) > 50:
                return "summary_statistics"
            
            # If we have detailed oceanographic data
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 3:
                return "detailed_records"
            
            # If we have comparison data
            if 'float_id' in df.columns and df['float_id'].nunique() > 1:
                return "comparison_table"
            
            # If we have aggregated data
            if any(col in df.columns for col in ['count', 'avg', 'mean', 'sum', 'total']):
                return "aggregated_data"
            
            return "generic"
            
        except Exception as e:
            logger.warning("Error detecting table type", error=str(e))
            return "generic"

    def _create_parameter_comparison_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create bar chart comparing different oceanographic parameters"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            oceanographic_params = ['temperature', 'salinity', 'dissolved_oxygen', 'pressure', 'ph', 'nitrate', 'chlorophyll', 'temp', 'sal']
            param_cols = [col for col in numeric_cols if any(param in col.lower() for param in oceanographic_params)]
            
            if not param_cols:
                return {"error": "No oceanographic parameters found for comparison"}
            
            # Calculate statistics for each parameter
            stats_data = []
            for param in param_cols[:6]:  # Limit to 6 parameters
                values = df[param].dropna()
                if len(values) > 0:
                    stats_data.append({
                        'parameter': param.replace('_', ' ').title(),
                        'mean': values.mean(),
                        'std': values.std(),
                        'min': values.min(),
                        'max': values.max(),
                        'count': len(values)
                    })
            
            # Create bar chart
            fig = go.Figure()
            
            # Add mean values
            fig.add_trace(go.Bar(
                name='Mean Value',
                x=[item['parameter'] for item in stats_data],
                y=[item['mean'] for item in stats_data],
                error_y=dict(type='data', array=[item['std'] for item in stats_data]),
                marker_color='#3498db',
                text=[f"{item['mean']:.2f}" for item in stats_data],
                textposition='auto'
            ))
            
            fig.update_layout(
                title='Oceanographic Parameter Comparison',
                xaxis_title='Parameters',
                yaxis_title='Values',
                barmode='group',
                height=500,
                showlegend=True,
                plot_bgcolor='white'
            )
            
            return {
                "type": "bar_chart",
                "chart": fig.to_dict(),
                "data_summary": stats_data,
                "description": f"Comparison of {len(stats_data)} oceanographic parameters across {len(df)} data points"
            }
            
        except Exception as e:
            logger.error("Error creating parameter comparison chart", error=str(e))
            return {"error": f"Failed to create parameter comparison chart: {str(e)}"}

    def _create_temporal_distribution_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create bar chart showing temporal distribution of data"""
        try:
            date_col = 'profile_date' if 'profile_date' in df.columns else 'date'
            if date_col not in df.columns:
                return {"error": "No date column found for temporal analysis"}
            
            # Convert dates and extract year-month
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            
            if len(df) == 0:
                return {"error": "No valid dates found"}
            
            # Group by month-year
            df['year_month'] = df[date_col].dt.to_period('M')
            monthly_counts = df['year_month'].value_counts().sort_index()
            
            # Create bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[str(period) for period in monthly_counts.index],
                y=monthly_counts.values,
                marker_color='#e74c3c',
                text=monthly_counts.values,
                textposition='auto'
            ))
            
            fig.update_layout(
                title='Data Distribution Over Time',
                xaxis_title='Month-Year',
                yaxis_title='Number of Records',
                height=500,
                plot_bgcolor='white'
            )
            
            return {
                "type": "bar_chart",
                "chart": fig.to_dict(),
                "data_summary": {
                    "total_records": len(df),
                    "date_range": f"{monthly_counts.index.min()} to {monthly_counts.index.max()}",
                    "peak_month": str(monthly_counts.idxmax()),
                    "peak_count": monthly_counts.max()
                },
                "description": f"Temporal distribution of {len(df)} records across {len(monthly_counts)} months"
            }
            
        except Exception as e:
            logger.error("Error creating temporal distribution chart", error=str(e))
            return {"error": f"Failed to create temporal distribution chart: {str(e)}"}

    def _create_regional_comparison_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create bar chart comparing different ocean regions"""
        try:
            if 'latitude' not in df.columns or 'longitude' not in df.columns:
                return {"error": "Latitude and longitude required for regional comparison"}
            
            # Define ocean regions based on coordinates
            def get_region(lat, lon):
                if 5 <= lat <= 25 and 65 <= lon <= 85:
                    return "Arabian Sea"
                elif 5 <= lat <= 25 and 85 <= lon <= 95:
                    return "Bay of Bengal"
                elif -20 <= lat <= 25 and 40 <= lon <= 120:
                    return "Indian Ocean"
                else:
                    return "Other Region"
            
            df['region'] = df.apply(lambda row: get_region(row['latitude'], row['longitude']), axis=1)
            regional_counts = df['region'].value_counts()
            
            # Create bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=regional_counts.index,
                y=regional_counts.values,
                marker_color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12'],
                text=regional_counts.values,
                textposition='auto'
            ))
            
            fig.update_layout(
                title='Data Distribution by Ocean Region',
                xaxis_title='Ocean Region',
                yaxis_title='Number of Records',
                height=500,
                plot_bgcolor='white'
            )
            
            return {
                "type": "bar_chart",
                "chart": fig.to_dict(),
                "data_summary": {
                    "total_records": len(df),
                    "regions_covered": len(regional_counts),
                    "dominant_region": regional_counts.idxmax(),
                    "dominant_count": regional_counts.max()
                },
                "description": f"Regional distribution across {len(regional_counts)} ocean regions"
            }
            
        except Exception as e:
            logger.error("Error creating regional comparison chart", error=str(e))
            return {"error": f"Failed to create regional comparison chart: {str(e)}"}

    def _create_depth_analysis_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create bar chart analyzing data by depth/pressure"""
        try:
            depth_col = 'pressure' if 'pressure' in df.columns else 'depth'
            if depth_col not in df.columns:
                return {"error": "No depth/pressure column found for depth analysis"}
            
            # Create depth bins
            df = df.dropna(subset=[depth_col])
            if len(df) == 0:
                return {"error": "No valid depth data found"}
            
            # Create depth bins (surface, shallow, intermediate, deep)
            df['depth_bin'] = pd.cut(df[depth_col], 
                                   bins=[0, 50, 200, 1000, df[depth_col].max()], 
                                   labels=['Surface (0-50m)', 'Shallow (50-200m)', 
                                          'Intermediate (200-1000m)', 'Deep (>1000m)'])
            
            depth_counts = df['depth_bin'].value_counts()
            
            # Create bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=depth_counts.index,
                y=depth_counts.values,
                marker_color='#9b59b6',
                text=depth_counts.values,
                textposition='auto'
            ))
            
            fig.update_layout(
                title='Data Distribution by Depth',
                xaxis_title='Depth Range',
                yaxis_title='Number of Records',
                height=500,
                plot_bgcolor='white'
            )
            
            return {
                "type": "bar_chart",
                "chart": fig.to_dict(),
                "data_summary": {
                    "total_records": len(df),
                    "depth_range": f"{df[depth_col].min():.1f}m to {df[depth_col].max():.1f}m",
                    "dominant_depth": depth_counts.idxmax(),
                    "dominant_count": depth_counts.max()
                },
                "description": f"Depth distribution across {len(depth_counts)} depth ranges"
            }
            
        except Exception as e:
            logger.error("Error creating depth analysis chart", error=str(e))
            return {"error": f"Failed to create depth analysis chart: {str(e)}"}

    def _create_float_statistics_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create bar chart showing statistics by float"""
        try:
            if 'float_id' not in df.columns:
                return {"error": "No float_id column found for float statistics"}
            
            # Calculate statistics per float
            float_stats = df.groupby('float_id').agg({
                'profile_id': 'count',
                'latitude': ['mean', 'std'],
                'longitude': ['mean', 'std']
            }).round(2)
            
            float_stats.columns = ['profile_count', 'lat_mean', 'lat_std', 'lon_mean', 'lon_std']
            float_stats = float_stats.sort_values('profile_count', ascending=False).head(10)  # Top 10 floats
            
            # Create bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[f"Float {float_id}" for float_id in float_stats.index],
                y=float_stats['profile_count'],
                marker_color='#16a085',
                text=float_stats['profile_count'],
                textposition='auto'
            ))
            
            fig.update_layout(
                title='Profile Count by Float (Top 10)',
                xaxis_title='Float ID',
                yaxis_title='Number of Profiles',
                height=500,
                plot_bgcolor='white'
            )
            
            return {
                "type": "bar_chart",
                "chart": fig.to_dict(),
                "data_summary": {
                    "total_floats": df['float_id'].nunique(),
                    "total_profiles": len(df),
                    "most_active_float": float_stats.index[0],
                    "most_active_count": float_stats.iloc[0]['profile_count']
                },
                "description": f"Statistics for {df['float_id'].nunique()} floats with {len(df)} total profiles"
            }
            
        except Exception as e:
            logger.error("Error creating float statistics chart", error=str(e))
            return {"error": f"Failed to create float statistics chart: {str(e)}"}

    def _create_float_specific_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create bar chart showing actual values for a specific float"""
        try:
            # Get the float ID from the data
            float_id = df['float_id'].iloc[0] if 'float_id' in df.columns else 'Unknown'
            
            # Extract surface and deep values - check multiple possible column names
            surface_temp = None
            deep_temp = None
            surface_sal = None
            deep_sal = None
            
            # Try different column name variations
            for col in df.columns:
                if 'surface_temp' in col.lower() and not col.endswith('_range'):
                    surface_temp = df[col].iloc[0] if not df[col].isna().iloc[0] else None
                elif 'deep_temp' in col.lower() and not col.endswith('_range'):
                    deep_temp = df[col].iloc[0] if not df[col].isna().iloc[0] else None
                elif 'surface_sal' in col.lower() and not col.endswith('_range'):
                    surface_sal = df[col].iloc[0] if not df[col].isna().iloc[0] else None
                elif 'deep_sal' in col.lower() and not col.endswith('_range'):
                    deep_sal = df[col].iloc[0] if not df[col].isna().iloc[0] else None
            
            # Prepare data for plotting
            parameters = []
            values = []
            colors = []
            
            if surface_temp is not None:
                parameters.append('Surface Temperature')
                values.append(surface_temp)
                colors.append('lightcoral')
            
            if deep_temp is not None:
                parameters.append('Deep Temperature')
                values.append(deep_temp)
                colors.append('darkblue')
            
            if surface_sal is not None:
                parameters.append('Surface Salinity')
                values.append(surface_sal)
                colors.append('lightgreen')
            
            if deep_sal is not None:
                parameters.append('Deep Salinity')
                values.append(deep_sal)
                colors.append('darkgreen')
            
            if not parameters:
                return {"error": "No temperature or salinity data available for this float"}
            
            # Create bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name=f'Float {float_id} Values',
                x=parameters,
                y=values,
                marker_color=colors,
                text=[f'{v:.2f}' for v in values],
                textposition='auto'
            ))
            
            fig.update_layout(
                title=f"Float {float_id} - Temperature and Salinity Data",
                xaxis_title="Parameters",
                yaxis_title="Values",
                barmode='group',
                template="plotly_dark",
                showlegend=False
            )
            
            return {
                "type": "bar_chart",
                "plotly_json": fig.to_json(),
                "title": f"Float {float_id} Analysis",
                "description": f"Temperature and salinity data for float {float_id}"
            }
            
        except Exception as e:
            logger.error("Error creating float-specific bar chart", error=str(e))
            return {"error": f"Failed to create float-specific bar chart: {str(e)}"}

    def _create_generic_bar_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a generic bar chart when specific type cannot be determined"""
        try:
            # Find the most suitable categorical column
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) == 0:
                return {"error": "No suitable data for bar chart"}
            
            # Use the column with most reasonable number of categories
            best_col = None
            best_count = 0
            for col in categorical_cols:
                unique_count = df[col].nunique()
                if 2 <= unique_count <= 20 and unique_count > best_count:
                    best_col = col
                    best_count = unique_count
            
            if best_col is None:
                return {"error": "No suitable categorical column found"}
            
            value_counts = df[best_col].value_counts().head(10)
            
            # Create bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=value_counts.index,
                y=value_counts.values,
                marker_color='#34495e',
                text=value_counts.values,
                textposition='auto'
            ))
            
            fig.update_layout(
                title=f'Distribution by {best_col.replace("_", " ").title()}',
                xaxis_title=best_col.replace("_", " ").title(),
                yaxis_title='Count',
                height=500,
                plot_bgcolor='white'
            )
            
            return {
                "type": "bar_chart",
                "chart": fig.to_dict(),
                "data_summary": {
                    "total_records": len(df),
                    "categories": len(value_counts),
                    "column_analyzed": best_col
                },
                "description": f"Distribution analysis of {len(df)} records by {best_col}"
            }
            
        except Exception as e:
            logger.error("Error creating generic bar chart", error=str(e))
            return {"error": f"Failed to create generic bar chart: {str(e)}"}

    def _create_summary_statistics_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a summary statistics table"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) == 0:
                return {"error": "No numeric columns found for summary statistics"}
            
            # Calculate summary statistics
            summary_stats = df[numeric_cols].describe()
            
            # Add additional statistics
            additional_stats = pd.DataFrame({
                'Count': df[numeric_cols].count(),
                'Unique': df[numeric_cols].nunique(),
                'Skewness': df[numeric_cols].skew(),
                'Kurtosis': df[numeric_cols].kurtosis()
            }).T
            
            # Combine statistics
            full_stats = pd.concat([summary_stats, additional_stats])
            
            # Create table
            fig = go.Figure(data=[go.Table(
                header=dict(values=['Statistic'] + list(full_stats.columns),
                           fill_color='#34495e',
                           font=dict(color='white', size=12),
                           align='left'),
                cells=dict(values=[full_stats.index] + [full_stats[col].round(3) for col in full_stats.columns],
                          fill_color='#ecf0f1',
                          align='left',
                          font=dict(size=11))
            )])
            
            fig.update_layout(
                title='Summary Statistics',
                height=400,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            
            return {
                "type": "data_table",
                "table": fig.to_dict(),
                "data_summary": {
                    "total_records": len(df),
                    "numeric_columns": len(numeric_cols),
                    "columns_analyzed": list(numeric_cols)
                },
                "description": f"Statistical summary of {len(numeric_cols)} numeric columns from {len(df)} records"
            }
            
        except Exception as e:
            logger.error("Error creating summary statistics table", error=str(e))
            return {"error": f"Failed to create summary statistics table: {str(e)}"}

    def _create_detailed_records_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a detailed records table with key columns"""
        try:
            # Select most important columns
            important_cols = []
            for col in ['profile_id', 'float_id', 'profile_date', 'latitude', 'longitude', 
                       'temperature', 'salinity', 'pressure', 'dissolved_oxygen']:
                if col in df.columns:
                    important_cols.append(col)
            
            if not important_cols:
                important_cols = df.columns[:8].tolist()  # Take first 8 columns
            
            # Limit to first 50 records for performance
            display_df = df[important_cols].head(50)
            
            # Create table
            fig = go.Figure(data=[go.Table(
                header=dict(values=[col.replace('_', ' ').title() for col in important_cols],
                           fill_color='#3498db',
                           font=dict(color='white', size=12),
                           align='left'),
                cells=dict(values=[display_df[col].astype(str) for col in important_cols],
                          fill_color='#ecf0f1',
                          align='left',
                          font=dict(size=10))
            )])
            
            fig.update_layout(
                title=f'Detailed Records (Showing {len(display_df)} of {len(df)} records)',
                height=600,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            
            return {
                "type": "data_table",
                "table": fig.to_dict(),
                "data_summary": {
                    "total_records": len(df),
                    "displayed_records": len(display_df),
                    "columns_displayed": len(important_cols)
                },
                "description": f"Detailed view of {len(display_df)} records with {len(important_cols)} key columns"
            }
            
        except Exception as e:
            logger.error("Error creating detailed records table", error=str(e))
            return {"error": f"Failed to create detailed records table: {str(e)}"}

    def _create_comparison_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a comparison table for different categories"""
        try:
            if 'float_id' not in df.columns:
                return {"error": "No float_id column found for comparison"}
            
            # Group by float and calculate statistics
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            oceanographic_params = [col for col in numeric_cols if any(param in col.lower() 
                             for param in ['temperature', 'salinity', 'pressure', 'dissolved_oxygen'])]
            
            if not oceanographic_params:
                return {"error": "No oceanographic parameters found for comparison"}
            
            comparison_data = []
            for float_id in df['float_id'].unique()[:10]:  # Top 10 floats
                float_data = df[df['float_id'] == float_id]
                row_data = {'Float ID': f"Float {float_id}"}
                
                for param in oceanographic_params[:4]:  # Top 4 parameters
                    values = float_data[param].dropna()
                    if len(values) > 0:
                        row_data[f"{param.replace('_', ' ').title()} (Mean)"] = f"{values.mean():.2f}"
                        row_data[f"{param.replace('_', ' ').title()} (Count)"] = len(values)
                
                comparison_data.append(row_data)
            
            # Create table
            if comparison_data:
                all_columns = list(comparison_data[0].keys())
                fig = go.Figure(data=[go.Table(
                    header=dict(values=all_columns,
                               fill_color='#e74c3c',
                               font=dict(color='white', size=12),
                               align='left'),
                    cells=dict(values=[[row.get(col, '') for row in comparison_data] for col in all_columns],
                              fill_color='#ecf0f1',
                              align='left',
                              font=dict(size=10))
                )])
                
                fig.update_layout(
                    title='Float Comparison Table',
                    height=500,
                    margin=dict(l=10, r=10, t=50, b=10)
                )
                
                return {
                    "type": "data_table",
                    "table": fig.to_dict(),
                    "data_summary": {
                        "floats_compared": len(comparison_data),
                        "parameters_compared": len(oceanographic_params),
                        "total_records": len(df)
                    },
                    "description": f"Comparison of {len(comparison_data)} floats across {len(oceanographic_params)} parameters"
                }
            
            return {"error": "No comparison data generated"}
            
        except Exception as e:
            logger.error("Error creating comparison table", error=str(e))
            return {"error": f"Failed to create comparison table: {str(e)}"}

    def _create_aggregated_data_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create an aggregated data table"""
        try:
            # Try to aggregate by common grouping columns
            group_cols = []
            for col in ['float_id', 'profile_date', 'latitude', 'longitude']:
                if col in df.columns:
                    group_cols.append(col)
                    break  # Use first available grouping column
            
            if not group_cols:
                return {"error": "No suitable grouping column found"}
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            oceanographic_params = [col for col in numeric_cols if any(param in col.lower() 
                             for param in ['temperature', 'salinity', 'pressure', 'dissolved_oxygen'])]
            
            if not oceanographic_params:
                oceanographic_params = numeric_cols[:3].tolist()
            
            # Aggregate data
            agg_data = df.groupby(group_cols[0]).agg({
                col: ['count', 'mean', 'std', 'min', 'max'] for col in oceanographic_params[:2]
            }).round(3)
            
            # Flatten column names
            agg_data.columns = [f"{col}_{stat}" for col, stat in agg_data.columns]
            agg_data = agg_data.head(20)  # Limit to 20 rows
            
            # Create table
            fig = go.Figure(data=[go.Table(
                header=dict(values=[group_cols[0].replace('_', ' ').title()] + list(agg_data.columns),
                           fill_color='#2ecc71',
                           font=dict(color='white', size=12),
                           align='left'),
                cells=dict(values=[agg_data.index.astype(str)] + [agg_data[col].astype(str) for col in agg_data.columns],
                          fill_color='#ecf0f1',
                          align='left',
                          font=dict(size=10))
            )])
            
            fig.update_layout(
                title=f'Aggregated Data by {group_cols[0].replace("_", " ").title()}',
                height=500,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            
            return {
                "type": "data_table",
                "table": fig.to_dict(),
                "data_summary": {
                    "grouping_column": group_cols[0],
                    "aggregated_records": len(agg_data),
                    "parameters_aggregated": len(oceanographic_params)
                },
                "description": f"Aggregated data for {len(agg_data)} groups by {group_cols[0]}"
            }
            
        except Exception as e:
            logger.error("Error creating aggregated data table", error=str(e))
            return {"error": f"Failed to create aggregated data table: {str(e)}"}

    def _create_generic_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a generic table when specific type cannot be determined"""
        try:
            # Select most important columns
            important_cols = df.columns[:8].tolist()  # Take first 8 columns
            display_df = df[important_cols].head(30)  # Limit to 30 rows
            
            # Create table
            fig = go.Figure(data=[go.Table(
                header=dict(values=[col.replace('_', ' ').title() for col in important_cols],
                           fill_color='#34495e',
                           font=dict(color='white', size=12),
                           align='left'),
                cells=dict(values=[display_df[col].astype(str) for col in important_cols],
                          fill_color='#ecf0f1',
                          align='left',
                          font=dict(size=10))
            )])
            
            fig.update_layout(
                title=f'Data Table (Showing {len(display_df)} of {len(df)} records)',
                height=500,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            
            return {
                "type": "data_table",
                "table": fig.to_dict(),
                "data_summary": {
                    "total_records": len(df),
                    "displayed_records": len(display_df),
                    "columns_displayed": len(important_cols)
                },
                "description": f"Data table showing {len(display_df)} records with {len(important_cols)} columns"
            }
            
        except Exception as e:
            logger.error("Error creating generic table", error=str(e))
            return {"error": f"Failed to create generic table: {str(e)}"}

    def generate_visualization_suggestions(self, user_query: str, sql_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced visualization suggestions with bar charts and tables"""
        try:
            if not sql_results:
                return {"suggestions": [], "error": "No data available for visualization"}
            
            df = pd.DataFrame(sql_results)
            suggestions = []
            
            # Analyze data characteristics
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            
            # Analyze user query to determine priority
            query_lower = user_query.lower()
            is_parameter_comparison = any(k in query_lower for k in ['compare', 'comparison', 'vs', 'versus', 'temperature', 'salinity', 'parameters'])
            is_temporal_query = any(k in query_lower for k in ['time', 'temporal', 'over time', 'distribution', 'year', 'month', 'date'])
            is_float_query = any(k in query_lower for k in ['float', 'profile', 'statistics'])
            
            # Suggest bar charts with priority based on user query
            if len(numeric_cols) >= 2:
                if is_parameter_comparison:
                    # Prioritize parameter comparison if user asks for it
                    suggestions.insert(0, {
                        "type": "bar_chart",
                        "title": "Parameter Comparison Chart",
                        "description": "Compare different oceanographic parameters",
                        "chart_type": "parameter_comparison"
                    })
                else:
                    suggestions.append({
                        "type": "bar_chart",
                        "title": "Parameter Comparison Chart",
                        "description": "Compare different oceanographic parameters",
                        "chart_type": "parameter_comparison"
                    })
            
            if 'profile_date' in df.columns or 'date' in df.columns:
                if is_temporal_query:
                    # Prioritize temporal distribution if user asks for it
                    suggestions.insert(0, {
                        "type": "bar_chart",
                        "title": "Temporal Distribution Chart",
                        "description": "Show data distribution over time",
                        "chart_type": "temporal_distribution"
                    })
                else:
                    suggestions.append({
                        "type": "bar_chart",
                        "title": "Temporal Distribution Chart",
                        "description": "Show data distribution over time",
                        "chart_type": "temporal_distribution"
                    })
            
            if 'float_id' in df.columns and df['float_id'].nunique() > 1:
                if is_float_query:
                    # Prioritize float statistics if user asks for it
                    suggestions.insert(0, {
                        "type": "bar_chart",
                        "title": "Float Statistics Chart",
                        "description": "Compare statistics across different floats",
                        "chart_type": "float_statistics"
                    })
                else:
                    suggestions.append({
                        "type": "bar_chart",
                        "title": "Float Statistics Chart",
                        "description": "Compare statistics across different floats",
                        "chart_type": "float_statistics"
                    })
            
            # Suggest tables
            if len(sql_results) <= 100:
                suggestions.append({
                    "type": "data_table",
                    "title": "Detailed Records Table",
                    "description": "View detailed records in tabular format",
                    "table_type": "detailed_records"
                })
            
            if len(numeric_cols) >= 3:
                suggestions.append({
                    "type": "data_table",
                    "title": "Summary Statistics Table",
                    "description": "Statistical summary of all numeric parameters",
                    "table_type": "summary_statistics"
                })
            
            if 'float_id' in df.columns and df['float_id'].nunique() > 1:
                suggestions.append({
                    "type": "data_table",
                    "title": "Float Comparison Table",
                    "description": "Compare floats side by side",
                    "table_type": "comparison_table"
                })
            
            # Always suggest maps for geographic data
            if 'latitude' in df.columns and 'longitude' in df.columns:
                suggestions.append({
                    "type": "map",
                    "title": "Geographic Distribution Map",
                    "description": "Visualize data points on a map",
                    "chart_type": "geographic"
                })
            
            return {
                "suggestions": suggestions[:6],  # Limit to 6 suggestions
                "data_summary": {
                    "total_records": len(df),
                    "numeric_columns": len(numeric_cols),
                    "categorical_columns": len(categorical_cols),
                    "unique_floats": df['float_id'].nunique() if 'float_id' in df.columns else 0
                }
            }
            
        except Exception as e:
            logger.error("Error generating visualization suggestions", error=str(e))
            return {"suggestions": [], "error": f"Failed to generate suggestions: {str(e)}"}

    def _create_year_comparison_chart(self, df: pd.DataFrame, user_query: str) -> Dict[str, Any]:
        """Create bar chart comparing oceanographic parameters across different years"""
        try:
            # Extract years from the data
            if 'year' in df.columns:
                years = sorted(df['year'].unique())
            else:
                # Extract year from profile_date if available
                if 'profile_date' in df.columns:
                    df['profile_date'] = pd.to_datetime(df['profile_date'], errors='coerce')
                    df['year'] = df['profile_date'].dt.year
                    years = sorted(df['year'].dropna().unique())
                else:
                    return {"error": "No year data found for comparison"}
            
            if len(years) < 2:
                return {"error": "Need at least 2 years for comparison"}
            
            # Get oceanographic parameters
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            oceanographic_params = ['temperature', 'salinity', 'dissolved_oxygen', 'pressure', 'ph', 'nitrate', 'chlorophyll', 'temp', 'sal']
            param_cols = [col for col in numeric_cols if any(param in col.lower() for param in oceanographic_params)]
            
            if not param_cols:
                return {"error": "No oceanographic parameters found for comparison"}
            
            # Create comparison data
            comparison_data = []
            for year in years:
                year_data = df[df['year'] == year]
                for param in param_cols:
                    if param in year_data.columns:
                        values = year_data[param].dropna()
                        if len(values) > 0:
                            comparison_data.append({
                                'year': int(year),
                                'parameter': param,
                                'mean_value': float(values.mean()),
                                'std_value': float(values.std()),
                                'count': len(values)
                            })
            
            if not comparison_data:
                return {"error": "No valid data found for year comparison"}
            
            # Create DataFrame for plotting
            comp_df = pd.DataFrame(comparison_data)
            
            # Create bar chart
            fig = go.Figure()
            
            # Get unique parameters
            unique_params = comp_df['parameter'].unique()
            colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
            
            for i, param in enumerate(unique_params):
                param_data = comp_df[comp_df['parameter'] == param]
                fig.add_trace(go.Bar(
                    x=[f"{int(year)}" for year in param_data['year']],
                    y=param_data['mean_value'],
                    name=param.replace('_', ' ').title(),
                    marker_color=colors[i % len(colors)],
                    text=[f"{val:.2f}" for val in param_data['mean_value']],
                    textposition='auto',
                    error_y=dict(
                        type='data',
                        array=param_data['std_value'],
                        visible=True
                    )
                ))
            
            # Update layout
            fig.update_layout(
                title=f'Oceanographic Parameters Comparison: {min(years)} vs {max(years)}',
                xaxis_title='Year',
                yaxis_title='Mean Values',
                barmode='group',
                height=600,
                showlegend=True,
                plot_bgcolor='white',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Generate summary statistics
            summary_stats = {}
            for param in unique_params:
                param_data = comp_df[comp_df['parameter'] == param]
                summary_stats[param] = {
                    'years': [int(year) for year in param_data['year']],
                    'values': [float(val) for val in param_data['mean_value']],
                    'total_records': int(param_data['count'].sum())
                }
            
            return {
                "type": "bar_chart",
                "chart": fig.to_dict(),
                "data_summary": {
                    "years_compared": [int(year) for year in years],
                    "parameters": list(unique_params),
                    "total_records": len(df),
                    "comparison_data": summary_stats
                },
                "description": f"Comparison of {len(unique_params)} oceanographic parameters between {min(years)} and {max(years)}"
            }
            
        except Exception as e:
            logger.error("Error creating year comparison chart", error=str(e))
            return {"error": f"Failed to create year comparison chart: {str(e)}"}

    def build_visualization_payload(self, sql_results: List[Dict[str, Any]], user_query: str = "") -> Dict[str, Any]:
        coords = self.extract_coordinates(sql_results)
        geojson = self.build_geojson(coords) if coords else {}
        timeseries = self.extract_time_series(sql_results) if sql_results else []
        plotly_code = self.generate_plotly_code(coords) if coords else ""
        
        # Only generate leaflet code for explicit map/visualization requests
        leaflet_code = ""
        if coords and user_query and any(keyword in user_query.lower() for keyword in ["map", "visualization", "trajectory", "trajectories", "plot", "chart"]):
            leaflet_code = self.generate_leaflet_code(coords, sql_results)
        
        # Generate enhanced visualization suggestions
        viz_suggestions = self.generate_visualization_suggestions(user_query, sql_results)
        
        return {
            "coordinates": coords,
            "geojson": geojson,
            "plotly_code": plotly_code,
            "leaflet_code": leaflet_code,
            "time_series": timeseries,
            "visualization_suggestions": viz_suggestions
        }


visualization_generator = VisualizationGenerator()


