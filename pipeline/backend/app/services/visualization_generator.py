"""
visualization_generator.py
Generate coordinate arrays, Plotly code, GeoJSON, and time series for trajectories.
Uses Hugging Face for code generation when beneficial, with robust local fallbacks.
"""
from typing import Dict, Any, List, Tuple, Optional
import json
import structlog

from app.core.multi_llm_client import multi_llm_client


logger = structlog.get_logger()


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

    def build_visualization_payload(self, sql_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        coords = self.extract_coordinates(sql_results)
        geojson = self.build_geojson(coords) if coords else {}
        timeseries = self.extract_time_series(sql_results) if sql_results else []
        plotly_code = self.generate_plotly_code(coords) if coords else ""
        leaflet_code = self.generate_leaflet_code(coords, sql_results) if coords else ""
        return {
            "coordinates": coords,
            "geojson": geojson,
            "plotly_code": plotly_code,
            "leaflet_code": leaflet_code,
            "time_series": timeseries,
        }


visualization_generator = VisualizationGenerator()


