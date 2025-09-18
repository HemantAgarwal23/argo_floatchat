"""
Batch Processing for ARGO NetCDF Files - Handles multiple files with progress tracking
"""

from pathlib import Path
import time
from typing import List
from .argo_data_processor import ArgoDataProcessor
from .config import Config
import logging

class BatchProcessor:
    """Processes multiple ARGO NetCDF files in batch with progress tracking"""
    
    def __init__(self):
        """Initialize batch processor with data processor and logging"""
        self.processor = ArgoDataProcessor()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup batch processing logging"""
        Config.ensure_directories()
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(Config.LOGS_PATH / 'batch_processing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def find_all_netcdf_files(self) -> List[Path]:
        """Find all NetCDF files in raw data directory"""
        raw_path = Config.RAW_NETCDF_PATH
        nc_files = list(raw_path.rglob("*.nc"))
        self.logger.info(f"Found {len(nc_files)} NetCDF files")
        return nc_files
    
    def process_all_files(self) -> dict:
        """Process all NetCDF files and return processing summary"""
        if not self.processor.connect_db():
            self.logger.error("Failed to connect to database")
            return {}
        
        nc_files = self.find_all_netcdf_files()
        if not nc_files:
            self.logger.warning("No NetCDF files found")
            return {}
        
        summary = {
            'total_files': len(nc_files),
            'processed_files': 0,
            'failed_files': 0,
            'total_profiles': 0,
            'total_floats': 0,
            'start_time': time.time(),
            'failed_file_list': []
        }
        
        self.logger.info(f"Starting batch processing of {len(nc_files)} files...")
        
        for i, nc_file in enumerate(nc_files, 1):
            try:
                self.logger.info(f"Processing file {i}/{len(nc_files)}: {nc_file.name}")
                
                success = self.processor.process_single_file(str(nc_file))
                
                if success:
                    summary['processed_files'] += 1
                else:
                    summary['failed_files'] += 1
                    summary['failed_file_list'].append(str(nc_file))
                
                # Show progress every 10 files
                if i % 10 == 0:
                    elapsed = time.time() - summary['start_time']
                    rate = i / elapsed if elapsed > 0 else 0
                    remaining = (len(nc_files) - i) / rate if rate > 0 else 0
                    self.logger.info(f"Progress: {i}/{len(nc_files)} files ({rate:.1f} files/sec, {remaining:.0f}s remaining)")
                
            except Exception as e:
                self.logger.error(f"Error processing file {nc_file}: {e}")
                summary['failed_files'] += 1
                summary['failed_file_list'].append(str(nc_file))
        
        # Get final database counts
        try:
            with self.processor.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM argo_profiles")
                summary['total_profiles'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM argo_floats")
                summary['total_floats'] = cursor.fetchone()['count']
        except Exception as e:
            self.logger.error(f"Error getting final counts: {e}")
        
        summary['end_time'] = time.time()
        summary['total_time'] = summary['end_time'] - summary['start_time']
        
        self.print_summary(summary)
        return summary
    
    def print_summary(self, summary: dict):
        """Print batch processing summary with statistics"""
        print("\n" + "="*60)
        print("🎉 BATCH PROCESSING COMPLETE")
        print("="*60)
        print(f"📁 Total files found: {summary['total_files']}")
        print(f"✅ Successfully processed: {summary['processed_files']}")
        print(f"❌ Failed files: {summary['failed_files']}")
        print(f"🌊 Total profiles stored: {summary['total_profiles']}")
        print(f"🚢 Total floats processed: {summary['total_floats']}")
        print(f"⏱️  Total processing time: {summary['total_time']:.1f} seconds")
        
        if summary['processed_files'] > 0:
            avg_time = summary['total_time'] / summary['processed_files']
            print(f"📊 Average time per file: {avg_time:.2f} seconds")
        
        if summary['failed_files'] > 0:
            print(f"\n❌ Failed files:")
            for failed_file in summary['failed_file_list'][:5]:  # Show first 5
                print(f"   - {Path(failed_file).name}")
            if len(summary['failed_file_list']) > 5:
                print(f"   ... and {len(summary['failed_file_list']) - 5} more")
        
        print("="*60)

if __name__ == "__main__":
    batch_processor = BatchProcessor()
    summary = batch_processor.process_all_files()
