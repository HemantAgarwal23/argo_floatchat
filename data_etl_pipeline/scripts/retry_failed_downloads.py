#!/usr/bin/env python3
"""
Retry Failed Downloads - Retries only failed downloads from previous run
"""

import os
import sys
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from urllib.parse import urlparse
import json
import time
import logging
from datetime import datetime

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

class RetryDownloader:
    """Retry only failed downloads"""
    
    def __init__(self, year: int, max_concurrent: int = 4):
        self.year = year
        self.download_dir = Path("data/raw") / str(year)
        self.max_concurrent = max_concurrent
        self.logger = setup_logging()
        
        # Files
        self.failed_urls_file = Path(f"failed_downloads_{year}.txt")
        self.state_file = Path(f"download_state_{year}.json")
        
        # Stats
        self.stats = {
            'retry_attempts': 0,
            'success': 0,
            'still_failed': 0,
            'start_time': None
        }
    
    def load_failed_urls(self):
        """Load failed URLs from file"""
        if not self.failed_urls_file.exists():
            self.logger.error(f"❌ No failed downloads file found: {self.failed_urls_file}")
            return []
        
        failed_urls = []
        with open(self.failed_urls_file, 'r') as f:
            for line in f:
                url = line.strip()
                if url:
                    failed_urls.append(url)
        
        self.logger.info(f"📋 Found {len(failed_urls)} failed URLs to retry")
        return failed_urls
    
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
    
    async def retry_download(self, session: aiohttp.ClientSession, url: str, 
                           local_path: Path, semaphore: asyncio.Semaphore) -> tuple:
        """Retry download a single file"""
        async with semaphore:
            try:
                # Check if file already exists and is valid
                if local_path.exists():
                    file_size = local_path.stat().st_size
                    if file_size > 0:  # File exists and has content
                        self.stats['success'] += 1
                        return True, url, "already_exists"
                
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download with longer timeout for retry
                timeout = aiohttp.ClientTimeout(total=180)  # 3 minutes per file
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
                            return True, url, "retry_success"
                        else:
                            # Clean up failed download
                            if temp_path.exists():
                                temp_path.unlink()
                            self.stats['still_failed'] += 1
                            return False, url, "retry_failed"
                    else:
                        self.stats['still_failed'] += 1
                        return False, url, f"http_error_{response.status}"
                        
            except asyncio.TimeoutError:
                self.stats['still_failed'] += 1
                return False, url, "timeout"
            except Exception as e:
                self.stats['still_failed'] += 1
                return False, url, f"error_{str(e)[:50]}"
    
    async def retry_all_failed(self):
        """Retry all failed downloads"""
        self.stats['start_time'] = time.time()
        
        # Load failed URLs
        failed_urls = self.load_failed_urls()
        if not failed_urls:
            self.logger.info("✅ No failed downloads to retry")
            return True
        
        self.logger.info(f"🔄 Retrying {len(failed_urls)} failed downloads...")
        
        # Retry with multiple attempts
        max_retry_attempts = 3
        current_failed = failed_urls.copy()
        
        for attempt in range(max_retry_attempts):
            if not current_failed:
                break
            
            self.logger.info(f"🔄 Retry attempt {attempt + 1}/{max_retry_attempts} for {len(current_failed)} files...")
            
            # Reset stats for this attempt
            attempt_success = 0
            attempt_failed = 0
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300),
                connector=aiohttp.TCPConnector(limit=self.max_concurrent * 2)
            ) as session:
                
                semaphore = asyncio.Semaphore(self.max_concurrent)
                still_failed = []
                
                async def retry_and_log(url):
                    local_path = self.get_local_path(url)
                    success, _, status = await self.retry_download(session, url, local_path, semaphore)
                    if not success:
                        still_failed.append(url)
                    return success, status
                
                # Schedule retry downloads
                tasks = [retry_and_log(url) for url in current_failed]
                
                completed = 0
                for coro in asyncio.as_completed(tasks):
                    success, status = await coro
                    completed += 1
                    
                    if success:
                        attempt_success += 1
                    else:
                        attempt_failed += 1
                    
                    if completed % 10 == 0 or completed == len(tasks):
                        self.logger.info(f"  📊 Progress: {completed}/{len(tasks)} - Success: {attempt_success}, Failed: {attempt_failed}")
                
                current_failed = still_failed
                self.stats['retry_attempts'] += 1
            
            # Check if retry was successful
            if attempt_success > 0:
                self.logger.info(f"✅ Retry attempt {attempt + 1} successful: {attempt_success} files downloaded")
            
            if not current_failed:
                self.logger.info("✅ All retry attempts successful!")
                break
            else:
                self.logger.warning(f"⚠️ {len(current_failed)} files still failed after attempt {attempt + 1}")
        
        # Final results
        elapsed_time = time.time() - self.stats['start_time']
        self.logger.info(f"🔄 Retry completed in {elapsed_time:.2f} seconds")
        self.logger.info(f"📊 Total successful: {self.stats['success']}")
        self.logger.info(f"📊 Still failed: {self.stats['still_failed']}")
        
        # Update failed URLs file
        if current_failed:
            with open(self.failed_urls_file, 'w') as f:
                for url in current_failed:
                    f.write(f"{url}\n")
            self.logger.warning(f"⚠️ {len(current_failed)} files still failed - updated {self.failed_urls_file}")
            return False
        else:
            # Remove failed URLs file if all successful
            if self.failed_urls_file.exists():
                self.failed_urls_file.unlink()
            self.logger.info("✅ All downloads successful - removed failed URLs file")
            return True

async def main():
    """Main function"""
    logger = setup_logging()
    
    print("ARGO Retry Failed Downloads")
    print("=" * 30)
    
    # Get year from user or command line
    import sys
    if len(sys.argv) > 1:
        year = sys.argv[1]
    else:
        year = input("Enter year to retry (e.g., 2021): ").strip()
    
    if not year.isdigit():
        print("Please enter a valid year")
        return
    
    year = int(year)
    
    # Create retry downloader
    retry_downloader = RetryDownloader(year=year, max_concurrent=4)
    
    # Check if failed downloads exist
    if not retry_downloader.failed_urls_file.exists():
        logger.info("✅ No failed downloads found to retry")
        return True
    
    # Start retry
    success = await retry_downloader.retry_all_failed()
    
    if success:
        logger.info("All retries completed successfully!")
    else:
        logger.warning("Some downloads still failed after retry attempts")
        logger.info("You can run this script again to retry remaining failures")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
