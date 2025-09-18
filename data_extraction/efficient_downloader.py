import os
import asyncio
import aiohttp
import aiofiles
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import time
from typing import List, Tuple
import argparse

class ArgoDataDownloader:
    """
    Downloads Argo oceanographic data files (e.g., NetCDF) from a remote directory structure.
    Scans for target files, downloads them concurrently, and logs progress and errors.
    """
    def __init__(self, base_url: str, download_dir: str = "argo_data", 
                 max_concurrent: int = 8, file_extensions: List[str] = None):
        # Base URL to start scanning from (e.g., yearly data folder)
        self.base_url = base_url.rstrip('/')
        # Local directory to store downloaded files
        self.download_dir = Path(download_dir)
        # Maximum number of concurrent downloads
        self.max_concurrent = max_concurrent
        # Allowed file extensions to download
        self.file_extensions = file_extensions or ['.nc', '.txt', '.dat']
        
        # Ensure the download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        self.setup_logging()
        
        # Track download statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'skipped': 0,
            'failed': 0,
            'start_time': None
        }

    def setup_logging(self):
        """Configure logging format for Python 3.13 and above."""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True
        )
        self.logger = logging.getLogger(__name__)

    async def get_file_links_targeted(self, session: aiohttp.ClientSession, url: str, max_depth: int = 2) -> List[str]:
        """
        Get all target file URLs by scanning the base directory.
        Recursively searches into subdirectories (year/month structure) up to a limited depth.
        """
        all_files = []
        self.logger.info(f"Looking for data in: {url}")
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for subdirectories (months or year folders)
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith(str(url.split('/')[-1])) or href in [f'{i:02}/' for i in range(1,13)]:
                            suburl = urljoin(url + '/', href)
                            self.logger.info(f"Found directory: {href}")
                            subfiles = await self._scan_directory_limited(session, suburl, max_depth=2)
                            all_files.extend(subfiles)
        except Exception as e:
            self.logger.error(f"Error scanning base directory {url}: {str(e)}")
        
        return all_files

    async def _scan_directory_limited(self, session: aiohttp.ClientSession, url: str, max_depth: int = 2) -> List[str]:
        """
        Recursively scan a directory for files matching the allowed extensions.
        Stops scanning when max_depth reaches 0 to avoid infinite recursion.
        """
        if max_depth <= 0:
            return []
            
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Cannot access {url}: HTTP {response.status}")
                    return []
                    
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                files = []
                directories = []
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href in ['../', './'] or href.startswith('?'):
                        continue
                        
                    full_url = urljoin(url + '/', href)
                    
                    # Identify directories vs. files
                    if href.endswith('/'):
                        directories.append(full_url)
                    else:
                        if any(href.lower().endswith(ext) for ext in self.file_extensions):
                            files.append(full_url)
                
                self.logger.info(f"Found {len(files)} files and {len(directories)} dirs in {url}")
                
                # Recursively scan subdirectories (limit recursion to first 20 for safety)
                for subdir in directories[:20]:
                    subfiles = await self._scan_directory_limited(session, subdir, max_depth - 1)
                    files.extend(subfiles)
                
                return files
                
        except Exception as e:
            self.logger.error(f"Error scanning directory {url}: {str(e)}")
            return []

    async def download_file(self, session: aiohttp.ClientSession, url: str, 
                            local_path: Path, semaphore: asyncio.Semaphore) -> Tuple[bool, str]:
        """
        Download a single file to the local path with concurrency control.
        Skips if the file already exists.
        """
        async with semaphore:
            try:
                if local_path.exists():
                    self.stats['skipped'] += 1
                    return True, url
                
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                async with session.get(url) as response:
                    if response.status == 200:
                        # Stream the file in chunks
                        async with aiofiles.open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        self.stats['success'] += 1
                        return True, url
                    else:
                        self.stats['failed'] += 1
                        self.logger.error(f"Failed to download {url}: HTTP {response.status}")
                        return False, url
                        
            except Exception as e:
                self.stats['failed'] += 1
                self.logger.error(f"Error downloading {url}: {str(e)}")
                return False, url

    def get_local_path(self, url: str) -> Path:
        """
        Convert a remote URL into the appropriate local file path inside the download directory.
        Preserves relative directory structure.
        """
        parsed = urlparse(url)
        relative_path = parsed.path
        # Remove leading '/geo/' to avoid redundant folders
        if relative_path.startswith('/geo/'):
            relative_path = relative_path[5:]
        return self.download_dir / relative_path.lstrip('/')

    def log_progress(self):
        """
        Print a concise progress summary to the console.
        Shows how many files processed, skipped, failed, etc.
        """
        total_processed = self.stats['success'] + self.stats['skipped'] + self.stats['failed']
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        ms = int(now.microsecond / 1000)
        
        print(f"{timestamp},{ms:03d} - INFO - Progress: {total_processed}/{self.stats['total']} - "
              f"Success: {self.stats['success']}, Skipped: {self.stats['skipped']}, Failed: {self.stats['failed']}")

    async def download_all(self):
        """
        Orchestrates the full download process:
        1. Discovers files to download.
        2. Downloads them concurrently.
        3. Logs progress and statistics.
        """
        self.stats['start_time'] = time.time()
        self.logger.info(f"Starting download from {self.base_url}")
        self.logger.info(f"Download directory: {self.download_dir.absolute()}")
        self.logger.info(f"Max concurrent downloads: {self.max_concurrent}")
        self.logger.info(f"File extensions: {self.file_extensions}")
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(limit=self.max_concurrent * 2)
        ) as session:
            
            # Discover all files
            self.logger.info("Discovering files (targeted scan)...")
            file_urls = await self.get_file_links_targeted(session, self.base_url)
            self.stats['total'] = len(file_urls)
            
            if not file_urls:
                self.logger.warning("No files found to download")
                return
                
            self.logger.info(f"Found {self.stats['total']} files to download")
            
            # Show first few examples for verification
            if len(file_urls) > 0:
                self.logger.info("Example files found:")
                for i, url in enumerate(file_urls[:5]):
                    filename = Path(url).name
                    self.logger.info(f"  {i+1}. {filename}")
                if len(file_urls) > 5:
                    self.logger.info(f"  ... and {len(file_urls) - 5} more files")
            
            failed_urls = []
            # Keep a log of all downloaded URLs
            all_downloaded_file = open('all_downloaded_urls.txt', 'a', encoding='utf-8')

            async def download_and_log(url):
                local_path = self.get_local_path(url)
                success, _ = await self.download_file(session, url, local_path, semaphore)
                if success:
                    all_downloaded_file.write(url + '\n')
                    all_downloaded_file.flush()
                else:
                    failed_urls.append(url)

            # Schedule all download tasks
            tasks = [download_and_log(url) for url in file_urls]

            completed = 0
            # Track progress as tasks complete
            for coro in asyncio.as_completed(tasks):
                await coro
                completed += 1
                if completed % 25 == 0 or completed == len(tasks):
                    self.log_progress()

            all_downloaded_file.close()

            # Final summary
            elapsed_time = time.time() - self.stats['start_time']
            self.logger.info(f"Download completed in {elapsed_time:.2f} seconds")
            self.log_progress()

            # Save list of failed downloads for later retry
            with open('failed_files.txt', 'w', encoding='utf-8') as f:
                for url in failed_urls:
                    f.write(url + '\n')
            
            # Calculate total size of downloaded data
            total_mb = 0
            if self.stats['success'] > 0:
                try:
                    total_size = sum(f.stat().st_size for f in self.download_dir.rglob('*') if f.is_file())
                    total_mb = total_size / (1024 * 1024)
                except Exception:
                    pass
            
            # Final log output
            self.logger.info(f"DOWNLOAD COMPLETE!")
            self.logger.info(f"Files downloaded: {self.stats['success']}")
            self.logger.info(f"Files skipped: {self.stats['skipped']}")
            self.logger.info(f"Files failed: {self.stats['failed']}")
            if total_mb > 0:
                self.logger.info(f"Total size: {total_mb:.1f} MB")
            self.logger.info(f"Download folder: {self.download_dir.absolute()}")

def main():
    """
    Parse command-line arguments and start the Argo data download.
    Example usage:
        python script.py 2023 -d argo_data -c 10 -e .nc .txt
    """
    parser = argparse.ArgumentParser(description='Download Argo oceanographic data by year')
    parser.add_argument('year', help='Year to download data for, e.g., 2023')
    parser.add_argument('-d', '--download-dir', default='argo_data', 
                        help='Directory to save files (default: argo_data)')
    parser.add_argument('-c', '--concurrent', type=int, default=8,
                        help='Max concurrent downloads (default: 8)')
    parser.add_argument('-e', '--extensions', nargs='+', 
                        default=['.nc'],
                        help='File extensions to download (default: .nc)')

    args = parser.parse_args()

    base_url = f'https://data-argo.ifremer.fr/geo/indian_ocean/{args.year}'

    # Initialize downloader with user-provided options
    downloader = ArgoDataDownloader(
        base_url=base_url,
        download_dir=args.download_dir,
        max_concurrent=args.concurrent,
        file_extensions=args.extensions
    )

    # User-friendly startup message
    print(f"🚀 Starting Argo Data Download for year {args.year}")
    print(f"📂 Target: {base_url}")
    print(f"💾 Saving to: {args.download_dir}")
    print(f"🔄 Concurrent downloads: {args.concurrent}")
    print(f"📋 File types: {args.extensions}")
    print("-" * 50)

    # Run the main async download routine
    asyncio.run(downloader.download_all())

if __name__ == "__main__":
    main()
