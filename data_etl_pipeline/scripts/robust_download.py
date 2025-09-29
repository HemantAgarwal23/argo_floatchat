#!/usr/bin/env python3
"""
Robust Download Script - Downloads ARGO NetCDF files with comprehensive error handling
"""

import os
import sys
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json
import time
import logging
from datetime import datetime
import hashlib

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

class RobustDownloader:
    """Robust ARGO downloader with comprehensive error handling"""
    
    def __init__(self, year: int, download_dir: str = "data/raw", max_concurrent: int = 8):
        self.year = year
        self.download_dir = Path(download_dir) / str(year)
        self.max_concurrent = max_concurrent
        self.logger = setup_logging()
        
        # Create download directory
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # State tracking
        self.state_file = Path(f"download_state_{year}.json")
        self.failed_urls_file = Path(f"failed_downloads_{year}.txt")
        self.verification_file = Path(f"download_verification_{year}.json")
        
        # Stats
        self.stats = {
            'total': 0,
            'success': 0,
            'skipped': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Load previous state if exists
        self.load_state()
    
    def load_state(self):
        """Load previous download state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.stats.update(state.get('stats', {}))
                    self.logger.info(f"📋 Loaded previous state: {self.stats['success']} successful, {self.stats['failed']} failed")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load previous state: {e}")
    
    def save_state(self):
        """Save current download state"""
        state = {
            'year': self.year,
            'stats': self.stats,
            'timestamp': datetime.now().isoformat(),
            'download_dir': str(self.download_dir)
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    async def get_file_links(self, session: aiohttp.ClientSession, url: str) -> list:
        """Get all NetCDF file URLs from the directory"""
        all_files = []
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for subdirectories (months)
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.endswith('/') and href not in ['../', './']:
                            suburl = urljoin(url + '/', href)
                            subfiles = await self._scan_directory(session, suburl)
                            all_files.extend(subfiles)
        except Exception as e:
            self.logger.error(f"Error scanning {url}: {e}")
        
        return all_files
    
    async def _scan_directory(self, session: aiohttp.ClientSession, url: str) -> list:
        """Scan directory for NetCDF files"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return []
                    
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                files = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.endswith('.nc'):
                        full_url = urljoin(url + '/', href)
                        files.append(full_url)
                
                return files
                
        except Exception as e:
            return []
    
    def get_local_path(self, url: str) -> Path:
        """Convert URL to local path with year/month structure"""
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        
        # Extract month from filename (e.g., 20210101_prof.nc -> 01)
        if filename.startswith(str(self.year)):
            month = filename[4:6]  # Extract month from YYYYMMDD format
            month_dir = self.download_dir / month
            month_dir.mkdir(parents=True, exist_ok=True)
            return month_dir / filename
        else:
            # Fallback to year directory
            return self.download_dir / filename
    
    async def download_file(self, session: aiohttp.ClientSession, url: str, 
                           local_path: Path, semaphore: asyncio.Semaphore) -> tuple:
        """Download a single file with comprehensive error handling"""
        async with semaphore:
            try:
                # Check if file already exists and is valid
                if local_path.exists():
                    file_size = local_path.stat().st_size
                    if file_size > 0:  # File exists and has content
                        self.stats['skipped'] += 1
                        return True, url, "already_exists"
                
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download with timeout and retry
                timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes per file
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        # Download to temporary file first
                        temp_path = local_path.with_suffix('.tmp')
                        
                        async with aiofiles.open(temp_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        # Verify download completed successfully
                        if temp_path.exists() and temp_path.stat().st_size > 0:
                            # Move temp file to final location
                            temp_path.rename(local_path)
                            self.stats['success'] += 1
                            return True, url, "downloaded"
                        else:
                            # Clean up failed download
                            if temp_path.exists():
                                temp_path.unlink()
                            self.stats['failed'] += 1
                            return False, url, "download_failed"
                    else:
                        self.stats['failed'] += 1
                        return False, url, f"http_error_{response.status}"
                        
            except asyncio.TimeoutError:
                self.stats['failed'] += 1
                return False, url, "timeout"
            except Exception as e:
                self.stats['failed'] += 1
                return False, url, f"error_{str(e)[:50]}"
    
    async def download_all(self):
        """Main download process with comprehensive error handling"""
        self.stats['start_time'] = time.time()
        self.logger.info(f"🚀 Starting robust download for {self.year}")
        
        # Try multiple sources for NetCDF files
        sources = [
            f'https://data-argo.ifremer.fr/geo/indian_ocean/{self.year}',
            f'https://data-argo.ifremer.fr/geo/global/{self.year}',
            f'https://data-argo.ucsd.edu/geo/indian_ocean/{self.year}',
            f'https://data-argo.ucsd.edu/geo/global/{self.year}'
        ]
        
        all_files = []
        failed_sources = []
        
        self.logger.info("🔍 Scanning remote sources for available files...")
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            connector=aiohttp.TCPConnector(limit=self.max_concurrent * 2)
        ) as session:
            
            # Try each source
            for source in sources:
                self.logger.info(f"🔍 Scanning {source}...")
                try:
                    files = await self.get_file_links(session, source)
                    all_files.extend(files)
                    self.logger.info(f"  📁 Found {len(files)} files from {source}")
                except Exception as e:
                    self.logger.error(f"  ❌ Error with {source}: {e}")
                    failed_sources.append(source)
            
            # Remove duplicates
            all_files = list(set(all_files))
            self.stats['total'] = len(all_files)
            
            if not all_files:
                self.logger.error("❌ No files found to download")
                return False
            
            self.logger.info("=" * 50)
            self.logger.info(f"📁 Remote scan complete: {self.stats['total']} unique files found")
            if failed_sources:
                self.logger.warning(f"⚠️ Failed to scan {len(failed_sources)} sources: {failed_sources}")
            self.logger.info("=" * 50)
            
            # Check what's already downloaded locally
            local_files = list(self.download_dir.rglob("*.nc"))
            local_filenames = {f.name for f in local_files}
            local_size = sum(f.stat().st_size for f in local_files)
            
            # Find missing files
            remote_filenames = {url.split('/')[-1] for url in all_files}
            missing_files = remote_filenames - local_filenames
            existing_files = remote_filenames & local_filenames
            
            # Always show the analysis
            self.logger.info(f"📊 Download Analysis:")
            self.logger.info(f"  🌐 Remote files available: {len(remote_filenames)}")
            self.logger.info(f"  💾 Local files: {len(local_files)} ({local_size / (1024*1024):.1f} MB)")
            self.logger.info(f"  ✅ Already downloaded: {len(existing_files)}")
            self.logger.info(f"  ⬇️  Missing files: {len(missing_files)}")
            
            if missing_files:
                self.logger.info(f"🚀 Starting download of {len(missing_files)} missing files...")
                # Filter URLs to only download missing files
                missing_urls = [url for url in all_files if url.split('/')[-1] in missing_files]
                failed_urls = await self._download_with_progress(session, missing_urls)
            else:
                self.logger.info("✅ All files already downloaded locally!")
                self.logger.info("⏭️  Skipping download step")
                failed_urls = []
            
            # Save failed URLs for retry
            if failed_urls:
                with open(self.failed_urls_file, 'w') as f:
                    for url in failed_urls:
                        f.write(f"{url}\n")
                self.logger.warning(f"⚠️ {len(failed_urls)} files failed - saved to {self.failed_urls_file}")
        
        # Final stats
        self.stats['end_time'] = time.time()
        elapsed_time = self.stats['end_time'] - self.stats['start_time']
        
        self.logger.info(f"✅ Download completed in {elapsed_time:.2f} seconds")
        self.logger.info(f"📊 Files downloaded: {self.stats['success']}")
        self.logger.info(f"📊 Files skipped: {self.stats['skipped']}")
        self.logger.info(f"📊 Files failed: {self.stats['failed']}")
        
        # Save final state
        self.save_state()
        
        # Return success status
        success_rate = self.stats['success'] / self.stats['total'] if self.stats['total'] > 0 else 0
        return success_rate >= 0.95  # 95% success rate required
    
    async def _download_with_progress(self, session, urls):
        """Download files with progress tracking"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        failed_urls = []
        
        async def download_and_log(url):
            local_path = self.get_local_path(url)
            success, _, status = await self.download_file(session, url, local_path, semaphore)
            if not success:
                failed_urls.append(url)
            return success, status
        
        # Schedule downloads
        tasks = [download_and_log(url) for url in urls]
        
        completed = 0
        start_time = time.time()
        
        for coro in asyncio.as_completed(tasks):
            success, status = await coro
            completed += 1
            
            # Show progress more frequently for better user experience
            if completed % 10 == 0 or completed == len(tasks):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                remaining = (len(tasks) - completed) / rate if rate > 0 else 0
                
                self.logger.info(f"📊 Progress: {completed}/{len(tasks)} ({completed/len(tasks)*100:.1f}%) - "
                               f"Success: {self.stats['success']}, Failed: {self.stats['failed']} - "
                               f"Rate: {rate:.1f} files/sec - ETA: {remaining/60:.1f} min")
        
        return failed_urls
    
    def get_download_summary(self):
        """Get summary of downloaded files"""
        if not self.download_dir.exists():
            return None
        
        nc_files = list(self.download_dir.rglob("*.nc"))
        total_size = sum(f.stat().st_size for f in nc_files)
        
        return {
            'total_files': len(nc_files),
            'total_size_mb': total_size / (1024 * 1024),
            'download_dir': str(self.download_dir),
            'stats': self.stats
        }

async def main():
    """Main function"""
    logger = setup_logging()
    
    print("Robust ARGO Downloader")
    print("=" * 30)
    
    # Get year from user or command line
    import sys
    if len(sys.argv) > 1:
        year = sys.argv[1]
    else:
        year = input("Enter year to download (e.g., 2021): ").strip()
    
    if not year.isdigit():
        print("Please enter a valid year")
        return
    
    year = int(year)
    
    # Create downloader
    downloader = RobustDownloader(year=year, max_concurrent=8)
    
    # Check if already downloaded
    summary = downloader.get_download_summary()
    if summary and summary['total_files'] > 0:
        logger.info(f"📁 Found existing download: {summary['total_files']} files, {summary['total_size_mb']:.1f} MB")
        proceed = input("Do you want to continue with existing files? (y/n): ").strip().lower()
        if proceed == 'n':
            logger.info("🔄 Starting fresh download...")
            # Start download
            logger.info("🔄 Downloading ARGO BGC data...")
            success = await downloader.download_all()
        else:
            logger.info("✅ Using existing files")
            return True
    else:
        # Start download
        logger.info("🔄 Downloading ARGO BGC data...")
        success = await downloader.download_all()
    
    if success:
        logger.info("Download completed successfully!")
        summary = downloader.get_download_summary()
        if summary:
            logger.info(f"Final summary: {summary['total_files']} files, {summary['total_size_mb']:.1f} MB")
    else:
        logger.warning("Download completed with some failures")
        logger.info(f"Run retry script to retry failed downloads: python scripts/retry_failed_downloads.py")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
