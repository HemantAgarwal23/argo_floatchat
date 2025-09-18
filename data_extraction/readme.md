# ARGO Ocean Data Downloader & Verifier

This project automates the **download, verification, and integrity checking** of ARGO oceanographic NetCDF (`.nc`) data files from [https://data-argo.ifremer.fr/geo/indian_ocean/](https://data-argo.ifremer.fr/geo/indian_ocean/).

It contains three Python scripts:

| File | Purpose |
|------|---------|
| **efficient_downloader.py** | Downloads large batches of ARGO `.nc` files asynchronously. |
| **retry_failed_downloads.py** | Retries downloads that failed previously, using the `failed_files.txt` list. |
| **verify_downloads.py** | Verifies local files against the remote server: checks for missing files and size mismatches, and generates a detailed log/report. |

## 1️⃣ Prerequisites

* **Python 3.9+** (recommended 3.11+)
* Recommended: use a virtual environment (`venv` or `conda`)

Install the required Python packages:
```bash
pip install aiohttp aiofiles beautifulsoup4
```

* `aiohttp & aiofiles` → asynchronous HTTP and file I/O
* `beautifulsoup4` → parse the remote directory listings

## 2️⃣ Script Details

### A. efficient_downloader.py
* Recursively downloads all `.nc` files from a target year/region.
* Creates a local directory structure matching the remote one.
* Failed downloads are written to `failed_files.txt` for later retries.

**Run:**
```bash
python efficient_downloader.py 2023
```

**Typical directory structure created:**
```
argo_data/
   indian_ocean/
       2023/
           08/
               20230806_prof.nc
```

### B. retry_failed_downloads.py
* Reads URLs from `failed_files.txt` and attempts to download them again.
* Overwrites `failed_files.txt` with any files that still fail after retries.

**Run:**
```bash
python retry_failed_downloads.py
```

Make sure `failed_files.txt` is in the same directory as the script.

### C. verify_downloads.py
* Scans the remote ARGO server for all `.nc` files for a given year.
* Compares remote files (by size) with local copies.
* Generates:
  - A time-stamped main log: `argo_missing_data_<YEAR>_<TIMESTAMP>.log`
  - A concise missing/error log: `<YEAR>missingdata.log`

**Usage:**
```bash
python verify_downloads.py --year 2023 
```

**Optional flags:**
* `--debug` : Enable verbose debug logging

## 3️⃣ Workflow Example

1. **Download new data**
   ```bash
   python efficient_downloader.py 2023
   ```

2. **Retry failures** (if `failed_files.txt` is not empty)
   ```bash
   python retry_failed_downloads.py
   ```

3. **Verify dataset integrity**
   ```bash
   python verify_downloads.py --year 2023 
   ```

4. Check the generated log files for a summary of missing files or size mismatches.

## 4️⃣ Tips & Notes

* Ensure you have enough disk space—ARGO datasets are large.
* Network interruptions will populate `failed_files.txt`; rerun the retry script until it is empty.
* If verifying multiple years, run the checker separately for each year.
* To automate regular updates, consider scheduling these scripts via cron (Linux/macOS) or Task Scheduler (Windows).

## License

This project is provided under the MIT License. Feel free to use and modify it for research or operational needs.

---

**Project Structure:**
```
project-root/
├── README.md
├── efficient_downloader.py
├── retry_failed_downloads.py
├── verify_downloads.py
└── failed_files.txt (generated automatically during downloads)
```
