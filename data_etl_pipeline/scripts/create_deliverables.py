#!/usr/bin/env python3
"""
Create Deliverables - Generate final deliverables from processed data
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import gzip

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

class DeliverablesCreator:
    """Create final deliverables from processed data"""
    
    def __init__(self, year: int):
        self.year = year
        self.logger = setup_logging()
        
        # Paths
        self.processed_dir = Path("data/processed")
        self.deliverables_dir = Path("data/deliverables")
        self.deliverables_dir.mkdir(parents=True, exist_ok=True)
        
        # Input files
        self.csv_path = self.processed_dir / f"argo_data_{year}.csv"
        self.summary_path = self.processed_dir / f"argo_summary_{year}.json"
        
        # Output files
        self.sql_dump_path = self.deliverables_dir / f"argo_database_{year}.sql"
        self.compressed_sql_path = self.deliverables_dir / f"argo_database_{year}.sql.gz"
        self.vector_summaries_path = self.deliverables_dir / f"argo_metadata_summaries_{year}.json"
        
        # State file
        self.deliverables_state_file = Path(f"deliverables_state_{year}.json")
        
        # Stats
        self.stats = {
            'csv_loaded': False,
            'sql_dump_created': False,
            'compressed_dump_created': False,
            'vector_summaries_created': False,
            'total_profiles': 0,
            'creation_time': 0
        }
    
    def check_input_files(self):
        """Check if required input files exist"""
        if not self.csv_path.exists():
            self.logger.error(f"❌ CSV file not found: {self.csv_path}")
            return False
        
        if not self.summary_path.exists():
            self.logger.warning(f"⚠️ Summary file not found: {self.summary_path}")
        
        self.logger.info(f"✅ Input files found")
        return True
    
    def create_postgres_sql_schema(self):
        """Create PostgreSQL schema for ARGO data"""
        schema = """
-- ARGO Database Schema for PostgreSQL
-- Generated for {year} ARGO data

-- Create database (run this separately)
-- CREATE DATABASE argo_database;

-- Create argo_floats table
CREATE TABLE IF NOT EXISTS argo_floats (
    id SERIAL PRIMARY KEY,
    platform_number VARCHAR(50),
    cycle_number INTEGER,
    longitude DECIMAL(10,6),
    latitude DECIMAL(10,6),
    profile_date TIMESTAMP,
    julian_day DECIMAL(15,6),
    max_pressure DECIMAL(10,2),
    n_levels INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create argo_profiles table
CREATE TABLE IF NOT EXISTS argo_profiles (
    id SERIAL PRIMARY KEY,
    profile_id VARCHAR(100),
    float_id VARCHAR(50),
    cycle_number INTEGER,
    longitude DECIMAL(10,6),
    latitude DECIMAL(10,6),
    profile_date TIMESTAMP,
    julian_day DECIMAL(15,6),
    pressure JSONB,  -- JSON array for PostgreSQL
    temperature JSONB,  -- JSON array for PostgreSQL
    salinity JSONB,  -- JSON array for PostgreSQL
    depth JSONB,  -- JSON array for PostgreSQL
    n_levels INTEGER,
    max_pressure DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_argo_floats_platform ON argo_floats(platform_number);
CREATE INDEX IF NOT EXISTS idx_argo_floats_date ON argo_floats(profile_date);
CREATE INDEX IF NOT EXISTS idx_argo_floats_location ON argo_floats(longitude, latitude);

CREATE INDEX IF NOT EXISTS idx_argo_profiles_float ON argo_profiles(float_id);
CREATE INDEX IF NOT EXISTS idx_argo_profiles_date ON argo_profiles(profile_date);
CREATE INDEX IF NOT EXISTS idx_argo_profiles_location ON argo_profiles(longitude, latitude);
CREATE INDEX IF NOT EXISTS idx_argo_profiles_pressure ON argo_profiles USING GIN(pressure);
CREATE INDEX IF NOT EXISTS idx_argo_profiles_temperature ON argo_profiles USING GIN(temperature);
CREATE INDEX IF NOT EXISTS idx_argo_profiles_salinity ON argo_profiles USING GIN(salinity);
""".format(year=self.year)
        return schema
    
    def create_postgres_sql_dump(self):
        """Create PostgreSQL-compatible SQL dump from CSV data"""
        self.logger.info("🗄️ Creating PostgreSQL SQL dump from CSV data...")
        
        # Read CSV data
        df = pd.read_csv(self.csv_path)
        self.logger.info(f"📊 Loaded {len(df)} profiles from CSV")
        
        # Create SQL content
        sql_content = []
        sql_content.append("-- ARGO Database SQL Dump for PostgreSQL")
        sql_content.append(f"-- Generated: {datetime.now().isoformat()}")
        sql_content.append(f"-- Source: {self.year} ARGO data")
        sql_content.append("-- Database: argo_database")
        sql_content.append("")
        
        # Add schema
        schema = self.create_postgres_sql_schema()
        sql_content.append(schema)
        sql_content.append("")
        
        # Insert float data
        self.logger.info("📋 Generating argo_floats INSERT statements...")
        # Check if required columns exist
        required_cols = ['platform_number', 'cycle_number', 'longitude', 'latitude', 
                        'profile_date', 'julian_day', 'max_pressure', 'n_levels']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            self.logger.error(f"❌ Missing required columns: {missing_cols}")
            self.logger.error(f"Available columns: {list(df.columns)}")
            return False
            
        float_data = df[required_cols].copy()
        
        for _, row in float_data.iterrows():
            values = []
            for col in ['platform_number', 'cycle_number', 'longitude', 'latitude', 
                       'profile_date', 'julian_day', 'max_pressure', 'n_levels']:
                value = row[col]
                if pd.isna(value):
                    values.append('NULL')
                elif col in ['platform_number']:
                    # Escape single quotes for strings
                    escaped = str(value).replace("'", "''")
                    values.append(f"'{escaped}'")
                elif col == 'profile_date':
                    if pd.notna(value):
                        values.append(f"'{value}'")
                    else:
                        values.append('NULL')
                else:
                    values.append(str(value))
            
            sql_content.append(f"INSERT INTO argo_floats (platform_number, cycle_number, longitude, latitude, profile_date, julian_day, max_pressure, n_levels) VALUES ({', '.join(values)});")
        
        sql_content.append("")
        
        # Insert profile data
        self.logger.info("📋 Generating argo_profiles INSERT statements...")
        # Check if required columns exist for profiles
        profile_required_cols = ['profile_id', 'float_id', 'cycle_number', 'longitude', 'latitude',
                                'profile_date', 'julian_day', 'pressure', 'temperature', 'salinity',
                                'depth', 'n_levels', 'max_pressure']
        profile_missing_cols = [col for col in profile_required_cols if col not in df.columns]
        
        if profile_missing_cols:
            self.logger.error(f"❌ Missing required columns for profiles: {profile_missing_cols}")
            return False
            
        profile_data = df[profile_required_cols].copy()
        
        for i, (_, row) in enumerate(profile_data.iterrows()):
            if i % 1000 == 0:
                self.logger.info(f"  📝 Processing profile {i+1}/{len(profile_data)}...")
                
            values = []
            for col in ['profile_id', 'float_id', 'cycle_number', 'longitude', 'latitude',
                       'profile_date', 'julian_day', 'pressure', 'temperature', 'salinity',
                       'depth', 'n_levels', 'max_pressure']:
                value = row[col]
                if pd.isna(value):
                    values.append('NULL')
                elif col in ['profile_id', 'float_id']:
                    # Escape single quotes for strings
                    escaped = str(value).replace("'", "''")
                    values.append(f"'{escaped}'")
                elif col == 'profile_date':
                    if pd.notna(value):
                        values.append(f"'{value}'")
                    else:
                        values.append('NULL')
                elif col in ['pressure', 'temperature', 'salinity', 'depth']:
                    # Convert to JSON for PostgreSQL
                    if isinstance(value, list):
                        json_str = json.dumps(value)
                        # Escape single quotes in JSON
                        json_str = json_str.replace("'", "''")
                        values.append(f"'{json_str}'")
                    else:
                        values.append('NULL')
                else:
                    values.append(str(value))
            
            sql_content.append(f"INSERT INTO argo_profiles (profile_id, float_id, cycle_number, longitude, latitude, profile_date, julian_day, pressure, temperature, salinity, depth, n_levels, max_pressure) VALUES ({', '.join(values)});")
        
        # Write SQL dump
        with open(self.sql_dump_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_content))
        
        self.logger.info(f"✅ PostgreSQL SQL dump created: {self.sql_dump_path}")
        self.stats['sql_dump_created'] = True
        return True
    
    def create_compressed_sql_dump(self):
        """Create compressed SQL dump"""
        self.logger.info("🗜️ Creating compressed SQL dump...")
        
        try:
            with open(self.sql_dump_path, 'rb') as f_in:
                with gzip.open(self.compressed_sql_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Get file sizes
            original_size = self.sql_dump_path.stat().st_size / (1024 * 1024)
            compressed_size = self.compressed_sql_path.stat().st_size / (1024 * 1024)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            self.logger.info(f"✅ Compressed SQL dump created: {self.compressed_sql_path}")
            self.logger.info(f"📏 Original size: {original_size:.1f} MB")
            self.logger.info(f"📏 Compressed size: {compressed_size:.1f} MB")
            self.logger.info(f"📊 Compression ratio: {compression_ratio:.1f}%")
            
            self.stats['compressed_dump_created'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create compressed dump: {e}")
            return False
    
    def create_vector_summaries(self):
        """Create vector summaries for semantic search"""
        self.logger.info("🧠 Creating vector summaries...")
        
        try:
            # Read CSV data
            df = pd.read_csv(self.csv_path)
            self.logger.info(f"📊 Processing {len(df)} profiles for summaries...")
            
            # Sample up to 2000 profiles
            if len(df) > 2000:
                df_sample = df.sample(n=2000, random_state=42)
                self.logger.info(f"📊 Sampling 2000 profiles from {len(df)} total")
            else:
                df_sample = df
            
            summaries = []
            
            for i, (_, row) in enumerate(df_sample.iterrows()):
                try:
                    profile_id = row['profile_id']
                    float_id = row['float_id']
                    date = row['profile_date']
                    lat = row['latitude']
                    lon = row['longitude']
                    
                    # Parse measurement data
                    temp_data = row['temperature'] if isinstance(row['temperature'], list) else []
                    sal_data = row['salinity'] if isinstance(row['salinity'], list) else []
                    
                    # Process temperature data
                    if temp_data:
                        valid_temps = [t for t in temp_data if t is not None and not pd.isna(t)]
                        if valid_temps:
                            min_temp = min(valid_temps)
                            max_temp = max(valid_temps)
                            surface_temp = valid_temps[0]
                        else:
                            min_temp = max_temp = surface_temp = None
                    else:
                        min_temp = max_temp = surface_temp = None
                    
                    # Process salinity data
                    if sal_data:
                        valid_sals = [s for s in sal_data if s is not None and not pd.isna(s)]
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
                    if lat is not None and lon is not None and not pd.isna(lat) and not pd.isna(lon):
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
                    if lat is not None and lon is not None and not pd.isna(lat) and not pd.isna(lon):
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
                    if pd.notna(row['max_pressure']):
                        summary_parts.append(f"maximum depth {row['max_pressure']:.0f}m")
                    
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
                    
                    if pd.notna(row['max_pressure']):
                        metadata["max_depth"] = row['max_pressure']
                    
                    # Create summary entry
                    summary_entry = {
                        "id": f"summary_{i+1}",
                        "text": summary_text,
                        "metadata": metadata
                    }
                    
                    summaries.append(summary_entry)
                    
                    # Progress indicator
                    if (i + 1) % 200 == 0:
                        self.logger.info(f"  📝 Generated {i+1}/{len(df_sample)} summaries...")
                        
                except Exception as e:
                    self.logger.warning(f"  ⚠️ Error processing profile {i}: {e}")
                    continue
            
            # Create final summary data structure
            summary_data = {
                "generation_info": {
                    "timestamp": datetime.now().isoformat(),
                    "total_summaries": len(summaries),
                    "source_database": f"argo_{self.year}_csv",
                    "version": "1.0"
                },
                "summaries": summaries
            }
            
            # Save to JSON file
            with open(self.vector_summaries_path, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            
            self.logger.info(f"✅ Vector summaries created: {self.vector_summaries_path}")
            self.logger.info(f"📄 Generated {len(summaries)} metadata summaries")
            
            self.stats['vector_summaries_created'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create vector summaries: {e}")
            return False
    
    def create_all_deliverables(self):
        """Create all deliverables"""
        self.logger.info(f"🚀 Creating deliverables for {self.year}")
        self.logger.info("=" * 50)
        
        # Check input files
        self.logger.info("📋 Checking input files...")
        if not self.check_input_files():
            return False
        
        # Create SQL dump
        self.logger.info("🗄️ Creating PostgreSQL SQL dump...")
        if not self.create_postgres_sql_dump():
            self.logger.error("❌ Failed to create SQL dump")
            return False
        
        # Create compressed SQL dump
        self.logger.info("🗜️ Creating compressed SQL dump...")
        if not self.create_compressed_sql_dump():
            self.logger.error("❌ Failed to create compressed SQL dump")
            return False
        
        # Create vector summaries
        self.logger.info("📊 Creating vector summaries...")
        if not self.create_vector_summaries():
            self.logger.error("❌ Failed to create vector summaries")
            return False
        
        # Save deliverables state
        self.logger.info("💾 Saving deliverables state...")
        self.save_deliverables_state()
        
        # Final summary
        self.logger.info("🎉 All deliverables created successfully!")
        self.logger.info("📁 Files created:")
        self.logger.info(f"  - PostgreSQL SQL Dump: {self.sql_dump_path}")
        self.logger.info(f"  - Compressed SQL Dump: {self.compressed_sql_path}")
        self.logger.info(f"  - Vector Summaries: {self.vector_summaries_path}")
        
        # Show file sizes
        for file_path in [self.sql_dump_path, self.compressed_sql_path, self.vector_summaries_path]:
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                self.logger.info(f"  📏 {file_path.name}: {size_mb:.1f} MB")
        
        self.logger.info("\n📋 To import into PostgreSQL:")
        self.logger.info(f"  1. Create database: CREATE DATABASE argo_database;")
        self.logger.info(f"  2. Import: psql -d argo_database -f {self.sql_dump_path}")
        self.logger.info(f"  3. Or compressed: gunzip -c {self.compressed_sql_path} | psql -d argo_database")
        
        return True
    
    def save_deliverables_state(self):
        """Save deliverables state"""
        state = {
            'year': self.year,
            'stats': self.stats,
            'creation_time': datetime.now().isoformat(),
            'deliverables_dir': str(self.deliverables_dir),
            'files_created': [
                str(self.sql_dump_path),
                str(self.compressed_sql_path),
                str(self.vector_summaries_path)
            ]
        }
        
        with open(self.deliverables_state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_deliverables_summary(self):
        """Get deliverables summary"""
        if not self.deliverables_state_file.exists():
            return None
        
        try:
            with open(self.deliverables_state_file, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            self.logger.error(f"Could not load deliverables summary: {e}")
            return None

def main():
    """Main function"""
    logger = setup_logging()
    
    print("ARGO Deliverables Creator")
    print("=" * 30)
    
    # Get year from user or command line
    import sys
    if len(sys.argv) > 1:
        year = sys.argv[1]
    else:
        year = input("Enter year to create deliverables for (e.g., 2021): ").strip()
    
    if not year.isdigit():
        print("Please enter a valid year")
        return
    
    year = int(year)
    
    # Create deliverables creator
    creator = DeliverablesCreator(year=year)
    
    # Check if already created
    summary = creator.get_deliverables_summary()
    if summary:
        logger.info(f"📋 Found existing deliverables for {year}")
        # If called from master pipeline (no interactive input), skip re-creation prompt
        if len(sys.argv) > 1:
            logger.info("✅ Using existing deliverables")
            return True
        else:
            proceed = input("Do you want to re-create? (y/n): ").strip().lower()
            if proceed == 'n':
                logger.info("✅ Using existing deliverables")
                return True
    
    # Create deliverables
    success = creator.create_all_deliverables()
    
    if success:
        logger.info("Deliverables created successfully!")
        logger.info("Ready for delivery")
    else:
        logger.error("Deliverables creation failed")
        logger.info("Check the logs for details")
    
    return success

if __name__ == "__main__":
    main()
