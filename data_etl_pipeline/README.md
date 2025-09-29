# ARGO BGC Pipeline

**Automated ARGO BGC data processing pipeline for Indian Ocean region - production ready.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/argo-bgc-pipeline.git
cd argo-bgc-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run pipeline
python scripts/master_pipeline.py
# Enter year (e.g., 2021)
```

## What You Get

- **PostgreSQL SQL Dumps** - Ready for database import
- **Vector Summaries** - For semantic search
- **Compressed Files** - Optimized for transfer
- **Complete Verification** - Ensures data integrity

## Project Structure

```
argo-bgc-pipeline/
├── scripts/                    # Pipeline scripts
│   ├── master_pipeline.py     # Main orchestrator
│   ├── robust_download.py     # Download with retry
│   ├── verify_downloads.py    # File integrity checks
│   ├── process_data.py        # NetCDF to CSV conversion
│   ├── create_deliverables.py # PostgreSQL dumps
│   ├── retry_failed_downloads.py # Retry mechanism
│   └── cleanup.py             # Clean temporary files
├── data/                      # Data directory (created on first run)
│   ├── raw/YYYY/              # Downloaded NetCDF files
│   ├── processed/             # Processed CSV and JSON
│   └── deliverables/          # Final PostgreSQL deliverables
│       ├── argo_database_YYYY.sql
│       ├── argo_database_YYYY.sql.gz
│       └── argo_metadata_summaries_YYYY.json
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## Key Features

- **Fully Automated** - Single command runs everything
- **Robust Error Handling** - Retries failed downloads automatically
- **State Persistence** - Remembers progress, resumes if interrupted
- **File Verification** - Ensures data integrity before processing
- **PostgreSQL Ready** - Creates proper SQL dumps with indexes
- **Vector Summaries** - Metadata for semantic search
- **No Re-downloading** - Checks existing files first
- **Comprehensive Logging** - Detailed progress tracking

## Requirements

- Python 3.8+
- Internet connection
- ~100MB free space per year

## Pipeline Steps

1. **Download** - Robust download with retry on failure
2. **Verify** - Comprehensive file integrity checks
3. **Process** - Transform NetCDF to structured data
4. **Deliverables** - Create PostgreSQL dumps and vector summaries

## Usage Examples

### Process New Year
```bash
python scripts/master_pipeline.py
# Enter: 2021
```

### Resume Interrupted Pipeline
```bash
python scripts/master_pipeline.py
# Enter: 2021
# Choose: Continue from where it left off
```

### Individual Steps (Advanced Usage)
```bash
# Download only
python scripts/robust_download.py 2021

# Retry failed downloads
python scripts/retry_failed_downloads.py 2021

# Verify downloads
python scripts/verify_downloads.py 2021

# Process data
python scripts/process_data.py 2021

# Create deliverables
python scripts/create_deliverables.py 2021

# Clean up temporary files
python scripts/cleanup.py
```

## Database Import

### PostgreSQL Import
```bash
# Create database
createdb argo_database

# Import SQL dump
psql -d argo_database -f data/deliverables/argo_database_2021.sql

# Or import compressed version
gunzip -c data/deliverables/argo_database_2021.sql.gz | psql -d argo_database
```

### Database Schema
- **argo_floats**: Float metadata and information
- **argo_profiles**: Individual profile data with measurements
- **Indexes**: Optimized for spatial and temporal queries
- **JSONB**: Vector summaries for semantic search

## Example Output

```
Master Pipeline Completed Successfully!
Check the following directories for outputs:
  - Raw data: data/raw/2021/
  - Processed data: data/processed/
  - Deliverables: data/deliverables/
```

## Troubleshooting

- **Pipeline interrupted**: Just run again - it will resume automatically
- **Download fails**: Pipeline automatically retries failed downloads
- **Verification fails**: Check logs for specific file issues
- **Processing fails**: Ensure verification passed first

## Technical Details

- **Indian Ocean Filtering**: Automatically filters to region (20°E-146°E, 60°S-30°N)
- **PostgreSQL Schema**: Optimized with proper indexes and JSONB columns
- **Vector Summaries**: Up to 2000 profiles with metadata for semantic search
- **State Management**: Tracks progress and prevents duplicate work
- **Data Sources**: ARGO BGC data from multiple international sources
- **File Format**: NetCDF input, PostgreSQL output with CSV intermediate

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- ARGO BGC data providers
- NetCDF4 and pandas libraries
- PostgreSQL community
