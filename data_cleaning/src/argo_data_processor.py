"""
ARGO NetCDF Data Processor - Extracts oceanographic profiles and stores in PostgreSQL
"""

import netCDF4 as nc
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional, Tuple
from .config import Config

class ArgoDataProcessor:
    """Processes ARGO NetCDF files and stores oceanographic data in PostgreSQL"""
    
    def __init__(self):
        """Initialize processor with config and logging"""
        self.config = Config()
        self.setup_logging()
        self.connection = None
        
    def setup_logging(self):
        """Setup file and console logging"""
        Config.ensure_directories()
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(Config.LOGS_PATH / 'processing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_db(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(
                Config.DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = True
            self.logger.info("✅ Database connected successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def safe_float(self, value, fill_values=[99999.0, 999999.0]) -> Optional[float]:
        """Convert value to float, handling masked arrays and fill values"""
        try:
            # Handle masked arrays (NetCDF missing data)
            if hasattr(value, 'mask'):
                if value.mask:
                    return None
                value = value.data
            
            # Handle numpy arrays (extract scalar value)
            if hasattr(value, 'item'):
                value = value.item()
            
            # Convert to float
            val = float(value)
            
            # Check for NaN (Not a Number)
            if np.isnan(val):
                return None
                
            # Check for fill values (ARGO uses specific values for missing data)
            for fill_val in fill_values:
                if abs(val - fill_val) < 1e-6:
                    return None
            
            return val
            
        except (ValueError, TypeError, OverflowError):
            return None
    
    def extract_platform_number(self, platform_data, prof_idx: int) -> str:
        """Extract ARGO float platform number from NetCDF data"""
        try:
            platform_bytes = platform_data[prof_idx, :]
            platform_str = ''.join([
                b.decode('utf-8').strip() if isinstance(b, (bytes, np.bytes_)) 
                else str(b).strip() 
                for b in platform_bytes
            ]).strip()
            
            # Clean up the platform number - remove trailing dashes, spaces, and null chars
            platform_str = platform_str.rstrip('- \x00\xff').strip()
            
            return platform_str if platform_str else f"unknown_{prof_idx}"
        except:
            return f"unknown_{prof_idx}"
    
    def julian_to_datetime(self, julian_days: float) -> Tuple[str, str]:
        """Convert ARGO Julian days (since 1950-01-01) to date and time"""
        try:
            # ARGO uses days since 1950-01-01 00:00:00 UTC
            reference_date = datetime(1950, 1, 1)
            target_datetime = reference_date + timedelta(days=float(julian_days))
            
            date_str = target_datetime.strftime('%Y-%m-%d')
            time_str = target_datetime.strftime('%H:%M:%S')
            
            return date_str, time_str
        except:
            return None, None
    
    def extract_profile_data(self, nc_file_path: str) -> List[Dict[str, Any]]:
        """Extract oceanographic profiles from NetCDF file with quality control"""
        profiles = []
        
        try:
            with nc.Dataset(nc_file_path, 'r') as dataset:
                self.logger.info(f"Processing file: {nc_file_path}")
                
                n_prof = dataset.dimensions['N_PROF'].size
                n_levels = dataset.dimensions['N_LEVELS'].size
                
                self.logger.info(f"Found {n_prof} profiles with {n_levels} levels each")
                
                # Extract all data at once
                platform_data = dataset.variables['PLATFORM_NUMBER'][:]
                juld_data = dataset.variables['JULD'][:]
                lat_data = dataset.variables['LATITUDE'][:]
                lon_data = dataset.variables['LONGITUDE'][:]
                cycle_data = dataset.variables['CYCLE_NUMBER'][:]
                pres_data = dataset.variables['PRES'][:]
                temp_data = dataset.variables['TEMP'][:]
                psal_data = dataset.variables['PSAL'][:]
                
                # Process each profile
                for prof_idx in range(n_prof):
                    try:
                        # Extract basic info
                        float_id = self.extract_platform_number(platform_data, prof_idx)
                        
                        # Convert coordinates and time safely
                        julian_day = self.safe_float(juld_data[prof_idx], [999999.0])
                        if julian_day is None:
                            continue
                            
                        lat = self.safe_float(lat_data[prof_idx])
                        if lat is None or lat < -90 or lat > 90:
                            continue
                            
                        lon = self.safe_float(lon_data[prof_idx])
                        if lon is None or lon < -180 or lon > 360:
                            continue
                        
                        # Convert longitude to -180 to 180 range
                        if lon > 180:
                            lon = lon - 360
                        
                        # Check Indian Ocean bounds
                        if not (Config.INDIAN_OCEAN_BOUNDS['lon_min'] <= lon <= Config.INDIAN_OCEAN_BOUNDS['lon_max'] and
                                Config.INDIAN_OCEAN_BOUNDS['lat_min'] <= lat <= Config.INDIAN_OCEAN_BOUNDS['lat_max']):
                            continue
                        
                        # Convert julian date
                        profile_date, profile_time = self.julian_to_datetime(julian_day)
                        if profile_date is None:
                            continue
                        
                        # Get cycle number
                        cycle_num = self.safe_float(cycle_data[prof_idx], [99999])
                        if cycle_num is None:
                            cycle_num = prof_idx
                        else:
                            cycle_num = int(cycle_num)
                        
                        profile_id = f"{float_id}_{cycle_num}"
                        
                        # Extract measurement arrays for this profile
                        pres_profile = pres_data[prof_idx, :]
                        temp_profile = temp_data[prof_idx, :]
                        psal_profile = psal_data[prof_idx, :]
                        
                        # Build valid data lists
                        pres_list = []
                        temp_list = []
                        psal_list = []
                        
                        for i in range(len(pres_profile)):
                            # Check pressure first
                            p = self.safe_float(pres_profile[i])
                            if p is not None and p > 0:
                                pres_list.append(p)
                                
                                # Add temperature if valid
                                t = self.safe_float(temp_profile[i])
                                if t is not None:
                                    temp_list.append(t)
                                
                                # Add salinity if valid
                                s = self.safe_float(psal_profile[i])
                                if s is not None:
                                    psal_list.append(s)
                        
                        # Skip if no valid pressure data
                        if len(pres_list) == 0:
                            continue
                        
                        # Calculate depth (simple conversion)
                        depth_list = [p / 1.019716 for p in pres_list]
                        
                        # Create profile record
                        profile_data = {
                            'profile_id': profile_id,
                            'float_id': float_id,
                            'cycle_number': cycle_num,
                            'latitude': lat,
                            'longitude': lon,
                            'profile_date': profile_date,
                            'profile_time': profile_time,
                            'julian_day': julian_day,
                            'position_qc': 1,
                            'pressure': pres_list,
                            'depth': depth_list,
                            'temperature': temp_list,
                            'salinity': psal_list,
                            'temperature_qc': [],
                            'salinity_qc': [],
                            'dissolved_oxygen': [],
                            'ph_in_situ': [],
                            'nitrate': [],
                            'chlorophyll_a': [],
                            'platform_number': float_id,
                            'n_levels': len(pres_list),
                            'max_pressure': max(pres_list) if pres_list else 0
                        }
                        
                        profiles.append(profile_data)
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing profile {prof_idx}: {e}")
                        continue
                
                self.logger.info(f"Successfully extracted {len(profiles)} valid profiles")
                
        except Exception as e:
            self.logger.error(f"Error reading NetCDF file {nc_file_path}: {e}")
        
        return profiles
    
    def create_or_update_float(self, float_id: str) -> bool:
        """Create or update ARGO float metadata in database"""
        try:
            insert_sql = """
            INSERT INTO argo_floats (float_id, platform_number, status)
            VALUES (%s, %s, 'ACTIVE')
            ON CONFLICT (float_id) DO NOTHING
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(insert_sql, (float_id, float_id))
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating float record {float_id}: {e}")
            return False
    
    def process_single_file(self, nc_file_path: str) -> bool:
        """Process single NetCDF file and store profiles in database"""
        try:
            profiles = self.extract_profile_data(nc_file_path)
            
            if not profiles:
                self.logger.warning(f"No valid profiles found in {nc_file_path}")
                return False
            
            # Create float metadata records first
            unique_floats = set([profile['float_id'] for profile in profiles])
            self.logger.info(f"Creating metadata for {len(unique_floats)} unique floats")
            
            for float_id in unique_floats:
                self.create_or_update_float(float_id)
            
            # Now store profiles
            success_count = 0
            for profile in profiles:
                if self.store_profile(profile):
                    success_count += 1
            
            self.logger.info(f"Stored {success_count}/{len(profiles)} profiles")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error processing file {nc_file_path}: {e}")
            return False
    
    def store_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Store oceanographic profile data in PostgreSQL database"""
        try:
            insert_sql = """
            INSERT INTO argo_profiles (
                profile_id, float_id, cycle_number, latitude, longitude,
                profile_date, profile_time, julian_day, position_qc,
                pressure, depth, temperature, salinity, 
                temperature_qc, salinity_qc, dissolved_oxygen, ph_in_situ, 
                nitrate, chlorophyll_a, platform_number, n_levels, max_pressure
            ) VALUES (
                %(profile_id)s, %(float_id)s, %(cycle_number)s, %(latitude)s, %(longitude)s,
                %(profile_date)s, %(profile_time)s, %(julian_day)s, %(position_qc)s,
                %(pressure)s, %(depth)s, %(temperature)s, %(salinity)s,
                %(temperature_qc)s, %(salinity_qc)s, %(dissolved_oxygen)s, %(ph_in_situ)s,
                %(nitrate)s, %(chlorophyll_a)s, %(platform_number)s, %(n_levels)s, %(max_pressure)s
            ) ON CONFLICT (profile_id) DO NOTHING
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(insert_sql, profile_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing profile {profile_data.get('profile_id', 'unknown')}: {e}")
            return False

# Test script
if __name__ == "__main__":
    processor = ArgoDataProcessor()
    
    if processor.connect_db():
        print("✅ Database connection successful")
        
        raw_path = Config.RAW_NETCDF_PATH
        nc_files = list(raw_path.rglob("*.nc"))
        
        if nc_files:
            test_file = nc_files[0]
            print(f"🧪 Testing with: {test_file}")
            
            success = processor.process_single_file(str(test_file))
            if success:
                print("✅ NetCDF processing successful!")
                
                with processor.connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as count FROM argo_profiles")
                    result = cursor.fetchone()
                    print(f"✅ Total profiles in database: {result['count']}")
                    
                    cursor.execute("SELECT COUNT(*) as count FROM argo_floats")
                    result = cursor.fetchone()
                    print(f"✅ Total floats in database: {result['count']}")
                    
                    cursor.execute("""
                        SELECT profile_id, float_id, profile_date, profile_time, 
                               latitude, longitude, n_levels 
                        FROM argo_profiles LIMIT 3
                    """)
                    samples = cursor.fetchall()
                    print("\n🎉 Sample profiles:")
                    for sample in samples:
                        print(f"  {sample['profile_id']}: {sample['profile_date']} {sample['profile_time']} "
                              f"({sample['latitude']:.2f}, {sample['longitude']:.2f}) - {sample['n_levels']} levels")
            else:
                print("❌ Processing failed")
        else:
            print("❌ No NetCDF files found")
    else:
        print("❌ Database connection failed")
