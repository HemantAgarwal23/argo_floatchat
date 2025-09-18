"""
Database verification and statistics for ARGO data processing system
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from .config import Config
import pandas as pd
from datetime import datetime

def verify_database():
    """Verify database content and display statistics"""
    
    try:
        connection = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
        
        print("🔍 DATABASE VERIFICATION")
        print("=" * 50)
        
        with connection.cursor() as cursor:
            # 1. Basic counts
            cursor.execute("SELECT COUNT(*) as count FROM argo_profiles")
            profile_count = cursor.fetchone()['count']
            print(f"📊 Total profiles: {profile_count:,}")
            
            cursor.execute("SELECT COUNT(*) as count FROM argo_floats") 
            float_count = cursor.fetchone()['count']
            print(f"🚢 Total floats: {float_count:,}")
            
            # 2. Date range
            cursor.execute("""
                SELECT MIN(profile_date) as min_date, MAX(profile_date) as max_date 
                FROM argo_profiles
            """)
            date_range = cursor.fetchone()
            print(f"📅 Date range: {date_range['min_date']} to {date_range['max_date']}")
            
            # 3. Geographic coverage
            cursor.execute("""
                SELECT MIN(latitude) as min_lat, MAX(latitude) as max_lat,
                       MIN(longitude) as min_lon, MAX(longitude) as max_lon
                FROM argo_profiles
            """)
            geo_range = cursor.fetchone()
            print(f"🌍 Geographic coverage:")
            print(f"   Latitude: {geo_range['min_lat']:.2f}° to {geo_range['max_lat']:.2f}°")
            print(f"   Longitude: {geo_range['min_lon']:.2f}° to {geo_range['max_lon']:.2f}°")
            
            # 4. Data depth statistics
            cursor.execute("""
                SELECT AVG(max_pressure) as avg_depth, 
                       MIN(max_pressure) as min_depth, 
                       MAX(max_pressure) as max_depth,
                       AVG(n_levels) as avg_levels
                FROM argo_profiles
            """)
            depth_stats = cursor.fetchone()
            print(f"🌊 Depth statistics:")
            print(f"   Average max depth: {depth_stats['avg_depth']:.0f} dbar")
            print(f"   Depth range: {depth_stats['min_depth']:.0f} to {depth_stats['max_depth']:.0f} dbar")
            print(f"   Average levels per profile: {depth_stats['avg_levels']:.1f}")
            
            # 5. Top 10 most active floats
            cursor.execute("""
                SELECT float_id, COUNT(*) as profile_count
                FROM argo_profiles 
                GROUP BY float_id 
                ORDER BY profile_count DESC 
                LIMIT 10
            """)
            top_floats = cursor.fetchall()
            print(f"\n🏆 Top 10 most active floats:")
            for float_data in top_floats:
                print(f"   {float_data['float_id']}: {float_data['profile_count']} profiles")
            
            # 6. Monthly profile distribution
            cursor.execute("""
                SELECT EXTRACT(year FROM profile_date) as year,
                       EXTRACT(month FROM profile_date) as month,
                       COUNT(*) as profile_count
                FROM argo_profiles 
                GROUP BY year, month 
                ORDER BY year, month 
                LIMIT 10
            """)
            monthly_dist = cursor.fetchall()
            print(f"\n📈 Monthly profile distribution (first 10 months):")
            for month_data in monthly_dist:
                print(f"   {int(month_data['year'])}-{int(month_data['month']):02d}: {month_data['profile_count']} profiles")
            
            # 7. Sample temperature/salinity data
            cursor.execute("""
                SELECT profile_id, float_id, profile_date, latitude, longitude,
                       array_length(temperature, 1) as temp_measurements,
                       array_length(salinity, 1) as sal_measurements,
                       temperature[1:3] as surface_temps,
                       salinity[1:3] as surface_sals
                FROM argo_profiles 
                WHERE array_length(temperature, 1) > 5 
                LIMIT 5
            """)
            sample_data = cursor.fetchall()
            print(f"\n🌡️  Sample temperature/salinity data:")
            for sample in sample_data:
                print(f"   {sample['profile_id']}: {sample['profile_date']}")
                print(f"     Location: ({sample['latitude']:.2f}°, {sample['longitude']:.2f}°)")
                print(f"     Measurements: {sample['temp_measurements']} temp, {sample['sal_measurements']} salinity")
                if sample['surface_temps']:
                    temps = [f"{t:.2f}°C" for t in sample['surface_temps'] if t is not None]
                    print(f"     Surface temps: {', '.join(temps)}")
                if sample['surface_sals']:
                    sals = [f"{s:.2f} PSU" for s in sample['surface_sals'] if s is not None]
                    print(f"     Surface salinity: {', '.join(sals)}")
                print()
        
        print("✅ Database verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False
    
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    verify_database()
