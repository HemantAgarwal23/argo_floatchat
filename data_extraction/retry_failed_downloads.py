import aiohttp
import aiofiles
import asyncio
import os
from urllib.parse import urlparse

async def download_file(url: str, base_out_dir: str, max_attempts: int = 3) -> bool:
    """
    Download a single file from the given URL into a local directory structure
    that mirrors the URL path.

    Parameters
    ----------
    url : str
        The full URL of the file to download.
    base_out_dir : str
        The root directory where files will be saved.
    max_attempts : int
        Number of retry attempts if the download fails.

    Returns
    -------
    bool
        True if the file was downloaded successfully, False otherwise.
    """
    # Parse the URL to reconstruct region/year/month folder structure.
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    # Example: ['geo', 'indian_ocean', '2023', '08', '20230806_prof.nc']

    region = path_parts[1] if len(path_parts) > 1 else ''  # e.g. 'indian_ocean'
    year   = path_parts[2] if len(path_parts) > 2 else ''
    month  = path_parts[3] if len(path_parts) > 3 else ''

    # Build local directory path: base_out_dir/region/year/month
    local_dir = os.path.join(base_out_dir, region, year, month)
    os.makedirs(local_dir, exist_ok=True)

    # Final local file path
    filename = path_parts[-1]
    local_path = os.path.join(local_dir, filename)

    # Remove any existing file to ensure a clean re-download
    if os.path.exists(local_path):
        os.remove(local_path)

    # Attempt the download up to max_attempts times
    for attempt in range(1, max_attempts + 1):
        try:
            # Create a new client session for each attempt
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status == 200:
                        # Stream file contents to disk in 8 KB chunks
                        async with aiofiles.open(local_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        print(f"✅ Downloaded: {local_path}")
                        return True
                    else:
                        print(f"⚠️  Failed {attempt}/{max_attempts}: {url} - HTTP {response.status}")
        except Exception as e:
            # Catch network or I/O errors and retry
            print(f"⚠️  Error {attempt}/{max_attempts} on {url}: {e}")

    # If all attempts fail, report failure
    print(f"❌ Failed after {max_attempts} attempts: {url}")
    return False


async def main():
    """
    Read a list of failed URLs from 'failed_files.txt', attempt to download each
    one concurrently, and rewrite the file with any that still fail.
    """
    base_out_dir = "argo_data"
    failed_file_path = "failed_files.txt"

    # Read all URLs from the failed list, ignoring blank lines
    with open(failed_file_path, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    final_failed: list[str] = []

    async def download_file_wrapper(url: str):
        # Wrapper to collect any URLs that remain failed
        success = await download_file(url, base_out_dir)
        if not success:
            final_failed.append(url)

    # Launch all download tasks concurrently
    tasks = [download_file_wrapper(url) for url in urls]
    await asyncio.gather(*tasks)

    # Overwrite failed_files.txt with only the URLs that still failed
    with open(failed_file_path, 'w') as f:
        for url in final_failed:
            f.write(url + '\n')

    print(f"Finished retries. {len(final_failed)} files still failed.")

if __name__ == "__main__":
    # Run the asynchronous main function
    asyncio.run(main())
