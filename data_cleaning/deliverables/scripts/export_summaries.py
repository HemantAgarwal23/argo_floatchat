"""
Export metadata summaries for vector database semantic search
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import os

def export_metadata_summaries():
    """Generate metadata summaries for vector database semantic search"""
    print("🧠 Generating metadata summaries for vector database...")
    
    # Ensure export directory exists
    os.makedirs("data/exports", exist_ok=True)
    
    try:
        # Use environment variable for database connection
        database_url = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/argo_database')
        conn = psycopg2.connect(database_url)
        summaries = []
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            print("📋 Fetching sample profiles...")
            
            # Get diverse sample of profiles
            cursor.execute("""
                SELECT profile_id, float_id, profile_date, latitude, longitude,
                       temperature, salinity, dissolved_oxygen, platform_number,
                       n_levels, max_pressure
                FROM argo_profiles 
                WHERE temperature IS NOT NULL 
                AND salinity IS NOT NULL
                ORDER BY RANDOM() 
                LIMIT 2000
            """)
            
            profiles = cursor.fetchall()
            print(f"📊 Processing {len(profiles)} profiles...")
            
            for i, profile in enumerate(profiles):
                try:
                    # Extract profile information
                    profile_id = profile['profile_id']
                    float_id = profile['float_id']
                    date = profile['profile_date']
                    lat = profile['latitude']
                    lon = profile['longitude']
                    
                    # Process temperature data
                    temp_data = profile['temperature'] if profile['temperature'] else []
                    if temp_data and len(temp_data) > 0:
                        valid_temps = [t for t in temp_data if t is not None]
                        if valid_temps:
                            min_temp = min(valid_temps)
                            max_temp = max(valid_temps)
                            surface_temp = valid_temps[0]
                        else:
                            min_temp = max_temp = surface_temp = None
                    else:
                        min_temp = max_temp = surface_temp = None
                    
                    # Process salinity data
                    sal_data = profile['salinity'] if profile['salinity'] else []
                    if sal_data and len(sal_data) > 0:
                        valid_sals = [s for s in sal_data if s is not None]
                        if valid_sals:
                            min_sal = min(valid_sals)
                            max_sal = max(valid_sals)
                            surface_sal = valid_sals[0]
                        else:
                            min_sal = max_sal = surface_sal = None
                    else:
                        min_sal = max_sal = surface_sal = None
                    
                    # Determine region
                    region = "indian_ocean"
                    if lat is not None and lon is not None:
                        if 10 <= lat <= 25 and 50 <= lon <= 75:
                            region = "arabian_sea"
                        elif 0 <= lat <= 15 and 60 <= lon <= 90:
                            region = "northern_indian_ocean"
                        elif -10 <= lat <= 10 and 70 <= lon <= 100:
                            region = "equatorial_indian_ocean"
                        elif lat < 0 and 60 <= lon <= 120:
                            region = "southern_indian_ocean"
                    
                    # Generate descriptive summary text
                    summary_parts = []
                    
                    # Basic info
                    summary_parts.append(f"Profile {profile_id} from ARGO float {float_id}")
                    
                    # Location and date
                    if lat is not None and lon is not None:
                        lat_dir = "N" if lat >= 0 else "S"
                        lon_dir = "E" if lon >= 0 else "W"
                        summary_parts.append(f"collected on {date} at {abs(lat):.2f}°{lat_dir} {abs(lon):.2f}°{lon_dir}")
                    
                    # Temperature info
                    if min_temp is not None and max_temp is not None:
                        if surface_temp is not None:
                            summary_parts.append(f"shows surface temperature {surface_temp:.1f}°C with profile range {min_temp:.1f}-{max_temp:.1f}°C")
                        else:
                            summary_parts.append(f"temperature profile ranging {min_temp:.1f}-{max_temp:.1f}°C")
                    
                    # Salinity info
                    if min_sal is not None and max_sal is not None:
                        if surface_sal is not None:
                            summary_parts.append(f"surface salinity {surface_sal:.1f} PSU ranging {min_sal:.1f}-{max_sal:.1f} PSU")
                        else:
                            summary_parts.append(f"salinity range {min_sal:.1f}-{max_sal:.1f} PSU")
                    
                    # Depth info
                    if profile['max_pressure']:
                        summary_parts.append(f"maximum depth {profile['max_pressure']:.0f}m")
                    
                    # BGC info
                    if profile['dissolved_oxygen']:
                        summary_parts.append("includes biogeochemical oxygen measurements")
                    
                    # Join summary
                    summary_text = " ".join(summary_parts) + "."
                    
                    # Create metadata
                    metadata = {
                        "profile_id": profile_id,
                        "float_id": float_id,
                        "date": str(date),
                        "latitude": lat,
                        "longitude": lon,
                        "region": region
                    }
                    
                    # Add measurement metadata
                    if min_temp is not None:
                        metadata.update({
                            "surface_temperature": surface_temp,
                            "min_temperature": min_temp,
                            "max_temperature": max_temp
                        })
                    
                    if min_sal is not None:
                        metadata.update({
                            "surface_salinity": surface_sal,
                            "min_salinity": min_sal,
                            "max_salinity": max_sal
                        })
                    
                    if profile['max_pressure']:
                        metadata["max_depth"] = profile['max_pressure']
                    
                    metadata["has_bgc"] = profile['dissolved_oxygen'] is not None
                    
                    # Create summary entry
                    summary_entry = {
                        "id": f"summary_{i+1}",
                        "text": summary_text,
                        "metadata": metadata
                    }
                    
                    summaries.append(summary_entry)
                    
                    # Progress indicator
                    if (i + 1) % 200 == 0:
                        print(f"  📝 Generated {i+1}/{len(profiles)} summaries...")
                        
                except Exception as e:
                    print(f"  ⚠️ Error processing profile {i}: {e}")
                    continue
        
        conn.close()
        
        # Create final summary data structure
        summary_data = {
            "generation_info": {
                "timestamp": datetime.now().isoformat(),
                "total_summaries": len(summaries),
                "source_database": "argo_database",
                "version": "1.0"
            },
            "summaries": summaries
        }
        
        # Save to JSON file
        output_filename = "data/exports/argo_metadata_summaries.json"
        with open(output_filename, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        print(f"\n✅ METADATA EXPORT COMPLETE")
        print(f"📄 Generated {len(summaries)} metadata summaries")
        print(f"💾 Saved to: {output_filename}")
        
        # Show sample summaries
        print("\n📋 Sample summaries:")
        for i, sample in enumerate(summaries[:3]):
            print(f"  {i+1}. {sample['text'][:80]}...")
        
        return output_filename
        
    except Exception as e:
        print(f"❌ METADATA EXPORT FAILED: {e}")
        return None

if __name__ == "__main__":
    export_metadata_summaries()
