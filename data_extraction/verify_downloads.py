import os
import sys
import asyncio
import aiohttp
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import threading
from typing import Dict, List

class ARGODataChecker:
    def __init__(self, local_base_dir: str, year: str):
        # Initialize base URL, local directory path, year to check
        self.base_url = "https://data-argo.ifremer.fr/geo/indian_ocean"
        self.local_dir = Path(local_base_dir) / year
        self.year = year
        self.missing_files = []        # store names of missing files
        self.size_mismatches = []      # store files whose sizes differ
        self.lock = threading.Lock()   # lock for thread-safe operations

        # Setup logging for progress and results
        self._setup_logging()
        self.logger.info(f"Starting ARGO data verification for year {self.year}")

    def _setup_logging(self):
        # Create filenames for the main log and missing-data log
        log_filename = f"argo_missing_data_{self.year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        missing_log_filename = f"{self.year}missingdata.log"

        # Main logger configuration
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # File handler for the main log
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler to display logs on stdout
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
        self.logger.addHandler(console_handler)

        # Separate logger for missing/error files
        self.missing_logger = logging.getLogger(f"missing_{self.year}")
        self.missing_logger.setLevel(logging.INFO)
        if self.missing_logger.hasHandlers():
            self.missing_logger.handlers.clear()

        # File handler for missing files
        missing_file_handler = logging.FileHandler(missing_log_filename, encoding='utf-8')
        missing_file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        missing_file_handler.setFormatter(missing_file_formatter)
        self.missing_logger.addHandler(missing_file_handler)

        self.logger.info(f"Log file: {log_filename}")
        self.logger.info(f"Missing/Error files log: {missing_log_filename}")

    async def _scan_directory_limited(self, session: aiohttp.ClientSession, url: str, max_depth: int = 2) -> List[str]:
        # Recursively scan a directory on the remote server up to max_depth levels
        if max_depth <= 0:
            return []
        files = []
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Cannot access {url}: HTTP {response.status}")
                    return []
                # Parse HTML to find links
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                directories = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Skip parent/current directory references and query links
                    if href in ['../', './'] or href.startswith('?'):
                        continue
                    full_url = urljoin(url + '/', href)
                    # If link ends with '/', treat it as a subdirectory
                    if href.endswith('/'):
                        directories.append(full_url)
                    # If link ends with .nc, treat it as a file
                    elif href.lower().endswith('.nc'):
                        files.append(full_url)
                self.logger.debug(f"Scanned {url}: found {len(files)} files and {len(directories)} dirs")
                # Recurse into subdirectories (limited to first 20 to avoid overload)
                for subdir in directories[:20]:
                    files.extend(await self._scan_directory_limited(session, subdir, max_depth - 1))
        except Exception as e:
            self.logger.error(f"Error scanning directory {url}: {e}")
        return files

    async def get_remote_files_async(self) -> Dict[str, int]:
        # Retrieve all remote file URLs and their sizes
        remote_url = f"{self.base_url}/{self.year}/"
        self.logger.info(f"Scanning remote directory: {remote_url}")
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            file_urls = await self._scan_directory_limited(session, remote_url, max_depth=3)
            self.logger.info(f"Found {len(file_urls)} remote files")
            remote_files = {}
            sem = asyncio.Semaphore(20)  # limit concurrent HEAD requests

            async def fetch_size(url):
                # Fetch file size using HEAD request
                async with sem:
                    try:
                        async with session.head(url) as resp:
                            if resp.status == 200:
                                size = resp.headers.get('Content-Length')
                                if size is not None:
                                    remote_files[os.path.basename(urlparse(url).path)] = int(size)
                                else:
                                    remote_files[os.path.basename(urlparse(url).path)] = -1
                            else:
                                self.logger.warning(f"HEAD request failed for {url}: {resp.status}")
                    except Exception as e:
                        self.logger.error(f"Error fetching HEAD for {url}: {e}")

            # Run HEAD requests concurrently
            tasks = [fetch_size(url) for url in file_urls]
            await asyncio.gather(*tasks)
        return remote_files

    def get_local_files(self) -> Dict[str, int]:
        # Collect all local .nc files and their sizes
        local_files = {}
        if not self.local_dir.exists():
            self.logger.error(f"Local directory does not exist: {self.local_dir}")
            return local_files
        for file_path in self.local_dir.glob("**/*.nc"):
            try:
                size = file_path.stat().st_size
                local_files[file_path.name] = size
            except Exception as e:
                self.logger.warning(f"Could not get size for {file_path}: {e}")
                local_files[file_path.name] = -1
        self.logger.info(f"Found {len(local_files)} .nc files locally")
        return local_files

    def check_files(self, remote_files: Dict[str, int], local_files: Dict[str, int]):
        # Compare remote and local files for presence and size
        for filename, remote_size in remote_files.items():
            local_size = local_files.get(filename)
            if local_size is None:
                # File missing locally
                with self.lock:
                    self.missing_files.append(filename)
                self.logger.warning(f"MISSING: {filename}")
                self.missing_logger.warning(f"MISSING: {filename}")
            elif remote_size > 0 and local_size != remote_size:
                # File size mismatch
                with self.lock:
                    self.size_mismatches.append({
                        'filename': filename,
                        'remote_size': remote_size,
                        'local_size': local_size
                    })
                self.logger.warning(f"SIZE MISMATCH: {filename} - Remote: {remote_size}, Local: {local_size}")
                self.missing_logger.warning(f"SIZE MISMATCH: {filename} - Remote: {remote_size}, Local: {local_size}")

    def generate_report(self, total_remote: int, total_local: int):
        # Print summary of verification results
        self.logger.info("="*60)
        self.logger.info("VERIFICATION SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Total files on remote server: {total_remote}")
        self.logger.info(f"Total files locally: {total_local}")
        self.logger.info(f"Missing files: {len(self.missing_files)}")
        self.logger.info(f"Size mismatches: {len(self.size_mismatches)}")

        if self.missing_files:
            self.logger.info("\nMISSING FILES:")
            for filename in self.missing_files:
                self.logger.info(f" - {filename}")

        if self.size_mismatches:
            self.logger.info("\nSIZE MISMATCHES:")
            for mismatch in self.size_mismatches:
                self.logger.info(f" - {mismatch['filename']}: Remote={mismatch['remote_size']}, Local={mismatch['local_size']}")

        if not self.missing_files and not self.size_mismatches:
            self.logger.info("✅ ALL FILES VERIFIED SUCCESSFULLY!")
        else:
            self.logger.info("❌ VERIFICATION COMPLETED WITH ISSUES")

    def run(self):
        # Orchestrate the remote scan, local scan, comparison, and report
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        remote_files = loop.run_until_complete(self.get_remote_files_async())
        if not remote_files:
            self.logger.error("No remote files found or failed to fetch remote file list.")
            return
        local_files = self.get_local_files()
        self.check_files(remote_files, local_files)
        self.generate_report(len(remote_files), len(local_files))

def main():
    import argparse
    # Parse command-line arguments for year, directory, and debug mode
    parser = argparse.ArgumentParser(description="Verify ARGO oceanographic data files")
    parser.add_argument("--year", default="2022", help="Year to check (default: 2022)")
    parser.add_argument("--dir", default=r"C:\Users\jjaya\OneDrive\Desktop\argo_project\argo_data\indian_ocean", help="Local base directory path")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create checker instance and run verification
    checker = ARGODataChecker(args.dir, args.year)
    checker.run()

if __name__ == "__main__":
    main()
