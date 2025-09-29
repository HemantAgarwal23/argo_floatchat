#!/usr/bin/env python3
"""
Process Data - Transform NetCDF files into processed data
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import netCDF4
import numpy as np

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def extract_netcdf_data_with_stats(nc_file, logger):
    """Extract data from NetCDF file with statistics"""
    try:
        with netCDF4.Dataset(nc_file, 'r') as nc:
            # Check if file has required variables
            required_vars = ['LATITUDE', 'LONGITUDE', 'PRES', 'TEMP', 'PSAL']
            missing_vars = [var for var in required_vars if var not in nc.variables]
            
            if missing_vars:
                logger.warning(f"  ⚠️ Missing variables in {Path(nc_file).name}: {missing_vars}")
                return None, 0, 0
            
            # Extract coordinates
            lat = nc.variables['LATITUDE'][:]
            lon = nc.variables['LONGITUDE'][:]
            
            # Filter for Indian Ocean region (20°E to 120°E, 30°S to 30°N)
            indian_ocean_mask = (
                (lon >= 20) & (lon <= 120) & 
                (lat >= -30) & (lat <= 30)
            )
            
            if not np.any(indian_ocean_mask):
                logger.info(f"  🌍 No Indian Ocean profiles in {Path(nc_file).name}")
                return None, 0, 1
            
            # Extract data for Indian Ocean profiles only
            data = {}
            for var in required_vars:
                if var in nc.variables:
                    var_data = nc.variables[var][:]
                    if var_data.ndim > 0:
                        data[var] = var_data[indian_ocean_mask]
                    else:
                        data[var] = var_data
            
            # Add metadata
            data['file_name'] = Path(nc_file).name
            data['extraction_time'] = datetime.now().isoformat()
            
            # Add global attributes if available
            for attr in ['WMO_INST_TYPE', 'PLATFORM_NUMBER', 'CYCLE_NUMBER']:
                if hasattr(nc, attr):
                    data[attr] = getattr(nc, attr)
            
            indian_ocean_profiles = np.sum(indian_ocean_mask)
            total_profiles = len(lat)
            outside_profiles = total_profiles - indian_ocean_profiles
            
            logger.info(f"  📊 Results: {indian_ocean_profiles} Indian Ocean profiles extracted, {outside_profiles} profiles filtered out (outside bounds)")
            
            return data, indian_ocean_profiles, outside_profiles
            
    except Exception as e:
        logger.error(f"  ❌ Error processing {Path(nc_file).name}: {str(e)}")
        return None, 0, 0

def transform_data(data_list, year, logger):
    """Transform extracted data into structured format"""
    if not data_list:
        logger.warning("No data to transform")
        return None
    
    # Flatten the data
    flattened_data = []
    
    for data in data_list:
        if data is None:
            continue
            
        # Get the number of profiles
        n_profiles = len(data.get('LATITUDE', []))
        
        for i in range(n_profiles):
            # Get pressure data for this profile
            pressure_data = data['PRES'][i] if i < len(data['PRES']) else []
            
            # Calculate derived fields
            if len(pressure_data) > 0:
                # Handle masked arrays properly
                if hasattr(pressure_data, 'mask'):
                    valid_pressure = pressure_data[~pressure_data.mask] if np.any(~pressure_data.mask) else []
                else:
                    valid_pressure = pressure_data[~np.isnan(pressure_data)] if not np.all(np.isnan(pressure_data)) else []
                
                max_pressure = float(np.max(valid_pressure)) if len(valid_pressure) > 0 else None
                n_levels = len(valid_pressure)
            else:
                max_pressure = None
                n_levels = 0
            
            # Create profile ID
            platform_number = data.get('PLATFORM_NUMBER', '')
            cycle_number = data.get('CYCLE_NUMBER', '')
            profile_id = f"{platform_number}_{cycle_number}_{i+1}"
            
            # Create float ID
            float_id = f"{platform_number}_{cycle_number}"
            
            # Calculate depth from pressure (approximate: 1 dbar ≈ 1 meter)
            depth_data = pressure_data.copy() if len(pressure_data) > 0 else []
            
            profile = {
                'profile_id': profile_id,
                'float_id': float_id,
                'file_name': data.get('file_name', ''),
                'extraction_time': data.get('extraction_time', ''),
                'wmo_inst_type': data.get('WMO_INST_TYPE', ''),
                'platform_number': platform_number,
                'cycle_number': cycle_number,
                'latitude': float(data['LATITUDE'][i]) if i < len(data['LATITUDE']) else None,
                'longitude': float(data['LONGITUDE'][i]) if i < len(data['LONGITUDE']) else None,
                'profile_date': None,  # Will be filled from NetCDF if available
                'julian_day': None,    # Will be filled from NetCDF if available
                'pressure': pressure_data.tolist() if len(pressure_data) > 0 else [],
                'temperature': data['TEMP'][i].tolist() if i < len(data['TEMP']) else [],
                'salinity': data['PSAL'][i].tolist() if i < len(data['PSAL']) else [],
                'depth': depth_data.tolist() if len(depth_data) > 0 else [],
                'max_pressure': max_pressure,
                'n_levels': n_levels
            }
            flattened_data.append(profile)
    
    # Create DataFrame
    df = pd.DataFrame(flattened_data)
    
    if df.empty:
        logger.warning("No valid profiles found")
        return None
    
    # Add profile_date and julian_day if available from NetCDF files
    # For now, we'll set them to None and they can be filled later if needed
    df['profile_date'] = None
    df['julian_day'] = None
    
    logger.info(f"📊 Transformed {len(df)} profiles into structured format")
    logger.info(f"📊 Columns: {list(df.columns)}")
    return df

class DataProcessor:
    """Process downloaded NetCDF files into structured data"""
    
    def __init__(self, year: int):
        self.year = year
        self.logger = setup_logging()
        
        # Paths
        self.raw_dir = Path("data/raw") / str(year)
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # State files
        self.processing_state_file = Path(f"processing_state_{year}.json")
        self.verification_file = Path(f"download_verification_{year}.json")
        
        # Stats
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'total_profiles': 0,
            'indian_ocean_profiles': 0,
            'processing_time': 0
        }
    
    def load_verification_results(self):
        """Load verification results to get valid files"""
        if not self.verification_file.exists():
            self.logger.warning("⚠️ No verification file found - processing all files")
            return None
        
        try:
            with open(self.verification_file, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            self.logger.error(f"Could not load verification results: {e}")
            return None
    
    def get_valid_files(self):
        """Get list of valid files to process"""
        verification_data = self.load_verification_results()
        
        if not verification_data:
            # Process all files if no verification
            nc_files = list(self.raw_dir.rglob("*.nc"))
            self.logger.info(f"📁 Processing all {len(nc_files)} files")
            return nc_files
        
        # Get only verified files
        valid_files = []
        for file_path, result in verification_data.get('results', {}).items():
            if result.get('status') == 'verified':
                valid_files.append(Path(file_path))
        
        self.logger.info(f"📁 Processing {len(valid_files)} verified files")
        return valid_files
    
    def process_files(self):
        """Process all valid NetCDF files"""
        self.logger.info(f"🔄 Starting data processing for {self.year}")
        
        # Get valid files
        nc_files = self.get_valid_files()
        if not nc_files:
            self.logger.error("❌ No valid files found to process")
            return False
        
        self.stats['total_files'] = len(nc_files)
        
        # Process each file
        all_profiles = []
        indian_ocean_count = 0
        failed_files = []
        
        for i, nc_file in enumerate(nc_files):
            self.logger.info(f"📁 Processing file {i+1}/{len(nc_files)}: {nc_file.name}")
            
            try:
                # Extract profiles from this file
                data, file_indian_ocean, file_outside = extract_netcdf_data_with_stats(str(nc_file), self.logger)
                
                if data is not None:
                    # Add the extracted data to our list
                    all_profiles.append(data)
                    indian_ocean_count += file_indian_ocean
                    
                    self.stats['processed_files'] += 1
                    self.stats['indian_ocean_profiles'] += file_indian_ocean
                    
                    # Enhanced logging with detailed stats
                    total_file_profiles = len(data) if data else 0
                    self.logger.info(f"  📊 Results: {file_indian_ocean} Indian Ocean profiles extracted, {file_outside} profiles filtered out (outside bounds)")
                    self.logger.info(f"  ✅ {file_indian_ocean} profiles extracted from {nc_file.name}")
                else:
                    self.stats['failed_files'] += 1
                    failed_files.append(str(nc_file))
                    self.logger.info(f"  ⚠️ No valid profiles in {nc_file.name}")
                    
            except Exception as e:
                self.logger.warning(f"❌ Failed to process {nc_file.name}: {e}")
                self.stats['failed_files'] += 1
                failed_files.append(str(nc_file))
                continue
        
        self.stats['total_profiles'] = indian_ocean_count
        
        if not all_profiles:
            self.logger.warning("⚠️ No valid profiles extracted. Cannot proceed with processing.")
            return False
        
        # Transform data
        self.logger.info("🔄 Transforming data...")
        df = transform_data(all_profiles, self.year, self.logger)
        
        # Save processed data
        self.save_processed_data(df)
        
        # Save processing state
        self.save_processing_state(failed_files)
        
        # Final summary
        self.logger.info("🎉 Data processing completed!")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 YEAR {self.year} PROCESSING SUMMARY:")
        self.logger.info(f"  📁 Total files processed: {self.stats['processed_files']}")
        self.logger.info(f"  📁 Files failed: {self.stats['failed_files']}")
        self.logger.info(f"  🌊 Total profiles extracted: {self.stats['total_profiles']}")
        self.logger.info(f"  🎯 Indian Ocean profiles (in bounds): {self.stats['indian_ocean_profiles']}")
        self.logger.info(f"  ❌ Profiles filtered out (out of bounds): {self.stats['total_profiles'] - self.stats['indian_ocean_profiles']}")
        self.logger.info("=" * 60)
        
        return True
    
    def save_processed_data(self, df):
        """Save processed data to files"""
        # Save to CSV
        csv_path = self.processed_dir / f"argo_data_{self.year}.csv"
        df.to_csv(csv_path, index=False)
        self.logger.info(f"💾 CSV saved to: {csv_path}")
        
        # Create summary
        summary = {
            "year": self.year,
            "total_profiles": int(len(df)),
            "files_processed": int(self.stats['processed_files']),
            "files_failed": int(self.stats['failed_files']),
            "indian_ocean_profiles": int(self.stats['indian_ocean_profiles']),
            "columns": list(df.columns),
            "processing_time": datetime.now().isoformat(),
            "sample_data": {
                "first_profile": df.iloc[0].to_dict() if len(df) > 0 else None
            }
        }
        
        summary_file = self.processed_dir / f"argo_summary_{self.year}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        self.logger.info(f"💾 Summary saved to: {summary_file}")
    
    def save_processing_state(self, failed_files):
        """Save processing state"""
        # Convert numpy types to Python types for JSON serialization
        stats_serializable = {}
        for key, value in self.stats.items():
            if hasattr(value, 'item'):  # numpy scalar
                stats_serializable[key] = value.item()
            else:
                stats_serializable[key] = int(value) if isinstance(value, (np.integer, np.int64)) else value
        
        state = {
            'year': int(self.year),
            'stats': stats_serializable,
            'processing_time': datetime.now().isoformat(),
            'failed_files': failed_files,
            'processed_dir': str(self.processed_dir)
        }
        
        with open(self.processing_state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_processing_summary(self):
        """Get processing summary"""
        if not self.processing_state_file.exists():
            return None
        
        try:
            with open(self.processing_state_file, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            self.logger.error(f"Could not load processing summary: {e}")
            return None

def main():
    """Main function"""
    logger = setup_logging()
    
    print("ARGO Data Processing")
    print("=" * 30)
    
    # Get year from user or command line
    import sys
    if len(sys.argv) > 1:
        year = sys.argv[1]
    else:
        year = input("Enter year to process (e.g., 2021): ").strip()
    
    if not year.isdigit():
        print("Please enter a valid year")
        return
    
    year = int(year)
    
    # Create processor
    processor = DataProcessor(year=year)
    
    # Check if already processed
    summary = processor.get_processing_summary()
    if summary:
        logger.info(f"📋 Found existing processing: {summary['stats']['total_profiles']} profiles")
        proceed = input("Do you want to re-process? (y/n): ").strip().lower()
        if proceed == 'n':
            logger.info("✅ Using existing processed data")
            return True
    
    # Start processing
    success = processor.process_files()
    
    if success:
        logger.info("Data processing completed successfully!")
        logger.info("Processed data is ready for deliverables")
    else:
        logger.error("Data processing failed")
        logger.info("Check the logs for details")
    
    return success

if __name__ == "__main__":
    main()
