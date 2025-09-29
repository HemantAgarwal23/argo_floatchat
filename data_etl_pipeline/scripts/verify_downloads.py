#!/usr/bin/env python3
"""
Verify Downloads - Comprehensive verification of downloaded files
"""

import os
import sys
import asyncio
import aiohttp
from pathlib import Path
from urllib.parse import urlparse
import json
import logging
from datetime import datetime
import hashlib
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

class DownloadVerifier:
    """Comprehensive download verification"""
    
    def __init__(self, year: int):
        self.year = year
        self.download_dir = Path("data/raw") / str(year)
        self.logger = setup_logging()
        
        # Verification files
        self.verification_file = Path(f"download_verification_{year}.json")
        self.corrupted_files_file = Path(f"corrupted_files_{year}.txt")
        
        # Stats
        self.stats = {
            'total_files': 0,
            'verified_files': 0,
            'corrupted_files': 0,
            'missing_files': 0,
            'total_size_mb': 0,
            'verification_time': 0
        }
    
    def get_remote_file_info(self, url: str) -> dict:
        """Get file information from remote server"""
        try:
            # This would need to be implemented based on the server's API
            # For now, we'll return basic info
            return {
                'url': url,
                'size': None,  # Would need server API to get this
                'last_modified': None,
                'checksum': None
            }
        except Exception as e:
            self.logger.warning(f"Could not get remote info for {url}: {e}")
            return None
    
    def verify_netcdf_file(self, file_path: Path) -> dict:
        """Verify NetCDF file integrity and content"""
        try:
            if not file_path.exists():
                return {'status': 'missing', 'error': 'File does not exist'}
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size == 0:
                return {'status': 'corrupted', 'error': 'File is empty'}
            
            # Try to open with netCDF4
            try:
                with netCDF4.Dataset(file_path, 'r') as nc:
                    # Check if it's a valid NetCDF file
                    if not hasattr(nc, 'dimensions'):
                        return {'status': 'corrupted', 'error': 'Invalid NetCDF structure'}
                    
                    # Check for required ARGO variables
                    required_vars = ['LATITUDE', 'LONGITUDE', 'PRES', 'TEMP', 'PSAL']
                    missing_vars = [var for var in required_vars if var not in nc.variables]
                    
                    if missing_vars:
                        return {'status': 'corrupted', 'error': f'Missing required variables: {missing_vars}'}
                    
                    # Check data quality
                    try:
                        # Try to read some data
                        lat = nc.variables['LATITUDE'][:]
                        lon = nc.variables['LONGITUDE'][:]
                        
                        # Check for reasonable coordinate values
                        if len(lat) > 0 and len(lon) > 0:
                            lat_val = float(lat[0]) if hasattr(lat, '__getitem__') else float(lat)
                            lon_val = float(lon[0]) if hasattr(lon, '__getitem__') else float(lon)
                            
                            if not (-90 <= lat_val <= 90) or not (-180 <= lon_val <= 360):
                                return {'status': 'corrupted', 'error': 'Invalid coordinate values'}
                        
                        return {
                            'status': 'verified',
                            'file_size': file_size,
                            'variables': list(nc.variables.keys()),
                            'dimensions': {name: int(dim.size) for name, dim in nc.dimensions.items()},
                            'attributes': {k: str(v) for k, v in nc.__dict__.items()}
                        }
                    
                    except Exception as e:
                        return {'status': 'corrupted', 'error': f'Data read error: {str(e)}'}
            
            except Exception as e:
                return {'status': 'corrupted', 'error': f'NetCDF read error: {str(e)}'}
        
        except Exception as e:
            return {'status': 'error', 'error': f'Verification error: {str(e)}'}
    
    def verify_all_downloads(self):
        """Verify all downloaded files"""
        self.logger.info(f"🔍 Starting verification for {self.year}")
        
        if not self.download_dir.exists():
            self.logger.error(f"❌ Download directory not found: {self.download_dir}")
            return False
        
        # Find all NetCDF files
        nc_files = list(self.download_dir.rglob("*.nc"))
        self.stats['total_files'] = len(nc_files)
        
        if not nc_files:
            self.logger.error("❌ No NetCDF files found to verify")
            return False
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in nc_files)
        self.logger.info(f"📁 Found {len(nc_files)} NetCDF files to verify ({total_size / (1024*1024):.1f} MB)")
        
        # Verify each file
        verification_results = {}
        corrupted_files = []
        
        for i, nc_file in enumerate(nc_files):
            if i % 25 == 0 or i == len(nc_files) - 1:
                self.logger.info(f"🔍 Verifying file {i+1}/{len(nc_files)}: {nc_file.name}")
            
            # Verify file
            result = self.verify_netcdf_file(nc_file)
            verification_results[str(nc_file)] = result
            
            # Track stats
            if result['status'] == 'verified':
                self.stats['verified_files'] += 1
                self.stats['total_size_mb'] += nc_file.stat().st_size / (1024 * 1024)
            elif result['status'] == 'corrupted':
                self.stats['corrupted_files'] += 1
                corrupted_files.append(str(nc_file))
            elif result['status'] == 'missing':
                self.stats['missing_files'] += 1
        
        # Save verification results
        verification_data = {
            'year': self.year,
            'verification_time': datetime.now().isoformat(),
            'stats': self.stats,
            'results': verification_results
        }
        
        with open(self.verification_file, 'w') as f:
            json.dump(verification_data, f, indent=2)
        
        # Save corrupted files list
        if corrupted_files:
            with open(self.corrupted_files_file, 'w') as f:
                for file_path in corrupted_files:
                    f.write(f"{file_path}\n")
        
        # Report results
        self.logger.info("📊 Verification Results:")
        self.logger.info(f"  ✅ Verified files: {self.stats['verified_files']}")
        self.logger.info(f"  ❌ Corrupted files: {self.stats['corrupted_files']}")
        self.logger.info(f"  📏 Total size: {self.stats['total_size_mb']:.1f} MB")
        
        if corrupted_files:
            self.logger.warning(f"⚠️ {len(corrupted_files)} corrupted files found")
            self.logger.info(f"📄 Corrupted files list saved to: {self.corrupted_files_file}")
        
        # Check if verification passed
        success_rate = self.stats['verified_files'] / self.stats['total_files'] if self.stats['total_files'] > 0 else 0
        
        if success_rate >= 0.95:  # 95% success rate required
            self.logger.info("✅ Verification passed - downloads are ready for processing")
            return True
        else:
            self.logger.warning(f"⚠️ Verification failed - only {success_rate:.1%} files are valid")
            self.logger.info("💡 Consider re-downloading corrupted files")
            return False
    
    def get_verification_summary(self):
        """Get verification summary"""
        if not self.verification_file.exists():
            return None
        
        try:
            with open(self.verification_file, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            self.logger.error(f"Could not load verification summary: {e}")
            return None

def main():
    """Main function"""
    logger = setup_logging()
    
    print("ARGO Download Verification")
    print("=" * 30)
    
    # Get year from user or command line
    import sys
    if len(sys.argv) > 1:
        year = sys.argv[1]
    else:
        year = input("Enter year to verify (e.g., 2021): ").strip()
    
    if not year.isdigit():
        print("Please enter a valid year")
        return
    
    year = int(year)
    
    # Create verifier
    verifier = DownloadVerifier(year=year)
    
    # Check if verification already exists
    summary = verifier.get_verification_summary()
    if summary:
        logger.info(f"📋 Found existing verification: {summary['stats']['verified_files']} verified files")
        proceed = input("Do you want to re-verify? (y/n): ").strip().lower()
        if proceed == 'n':
            logger.info("✅ Using existing verification results")
            return summary['stats']['verified_files'] > 0
    
    # Start verification
    success = verifier.verify_all_downloads()
    
    if success:
        logger.info("Verification completed successfully!")
        logger.info("Downloads are ready for processing")
    else:
        logger.warning("Verification completed with issues")
        logger.info("Check corrupted files and consider re-downloading")
    
    return success

if __name__ == "__main__":
    main()
