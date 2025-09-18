# ARGO Oceanographic Data Processing System

A comprehensive Python-based system for processing, storing, and analyzing ARGO oceanographic data with PostgreSQL database integration and vector search capabilities.

## 🌊 Overview

This project processes ARGO (Array for Real-time Geostrophic Oceanography) NetCDF files, extracts oceanographic profiles, and stores them in a PostgreSQL database with advanced search capabilities using vector embeddings.

## 📊 Features

- **NetCDF Processing**: Automated processing of ARGO NetCDF files
- **PostgreSQL Database**: Structured storage of oceanographic profiles
- **Vector Search**: Semantic search using ChromaDB and sentence transformers
- **Quality Control**: Data validation and quality filtering
- **Batch Processing**: Efficient processing of large datasets
- **Export Capabilities**: Database exports and metadata summaries

## 🏗️ Project Structure

```
argo-project/
├── src/                          # Source code
│   ├── argo_data_processor.py    # Main NetCDF processor
│   ├── batch_processor.py        # Batch processing utilities
│   ├── vector_db_manager.py      # Vector database operations
│   ├── database_verification.py  # Database validation
│   └── config.py                 # Configuration settings
├── sql/                          # Database schema
│   └── database_schema.sql       # PostgreSQL schema
├── deliverables/                 # Export and delivery scripts
│   └── scripts/                  # Utility scripts
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git
- 4GB+ RAM (for vector processing)
- 10GB+ disk space (for data storage)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd argo-project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb argo_database
   
   # Run schema
   psql -d argo_database -f sql/database_schema.sql
   
   # Verify database setup
   psql -d argo_database -c "\dt"
   ```

5. **Configure environment**
   ```bash
   # Set database URL as environment variable
   export DATABASE_URL="postgresql://your_username:your_password@localhost:5432/argo_database"
   
   # Or create a .env file with your credentials
   echo "DATABASE_URL=postgresql://your_username:your_password@localhost:5432/argo_database" > .env
   ```

## 📖 Usage

### Quick Test (Recommended First Step)

```python
# Test the complete system
from src.database_verification import verify_database
verify_database()
```

### Getting Sample Data

If you don't have ARGO NetCDF files, you can:

1. **Download sample data** from [ARGO GDAC](https://www.argodatamgt.org/Access-to-data/Argo-data-download/)
2. **Use the provided test data** (if available in the repository)
3. **Start with vector database** using existing metadata summaries

```python
# Test vector database with sample data
from src.vector_db_manager import VectorDBManager
vector_manager = VectorDBManager()
vector_manager.test_sample_processing(sample_size=5)
```

### 1. Process NetCDF Files

```python
from src.argo_data_processor import ArgoDataProcessor

# Initialize processor
processor = ArgoDataProcessor()

# Connect to database
if processor.connect_db():
    # Process a single file
    success = processor.process_single_file("path/to/file.nc")
    
    if success:
        print("✅ File processed successfully!")
```

### 2. Batch Processing

```python
from src.batch_processor import BatchProcessor

# Process all NetCDF files
batch_processor = BatchProcessor()
summary = batch_processor.process_all_files()

print(f"Processed {summary['processed_files']} files")
print(f"Total profiles: {summary['total_profiles']}")
```

### 3. Vector Database Setup

```python
from src.vector_db_manager import VectorDBManager

# Initialize vector database
vector_manager = VectorDBManager()

# Test with sample data
vector_manager.test_sample_processing(sample_size=10)

# Process all profiles for vector search
vector_manager.process_all_profiles(batch_size=100)
```

### 4. Database Verification

```python
from src.database_verification import verify_database

# Check database content and statistics
verify_database()
```

### 5. Chatbot Integration

```python
from deliverables.scripts.database_interface import ARGODatabaseInterface

# Initialize chatbot interface
db = ARGODatabaseInterface("postgresql://user:pass@localhost:5432/argo_database")
db.connect()

# Search by location
results = db.search_by_location(10, 25, 50, 75, limit=10)  # Arabian Sea

# Search by temperature
warm_waters = db.search_by_temperature(28, 32, limit=10)

# Semantic search
semantic_results = db.search_profiles_semantic("warm tropical waters", n_results=5)
```

## 🔄 Complete Workflow

### Step-by-Step Process

1. **Setup Environment**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Setup database
   createdb argo_database
   psql -d argo_database -f sql/database_schema.sql
   
   # Set environment
   export DATABASE_URL="postgresql://user:pass@localhost:5432/argo_database"
   ```

2. **Process Data**
   ```python
   # Process NetCDF files
   from src.batch_processor import BatchProcessor
   processor = BatchProcessor()
   summary = processor.process_all_files()
   ```

3. **Setup Vector Search**
   ```python
   # Create vector database
   from src.vector_db_manager import VectorDBManager
   vector_manager = VectorDBManager()
   vector_manager.process_all_profiles()
   ```

4. **Verify Results**
   ```python
   # Check everything works
   from src.database_verification import verify_database
   verify_database()
   ```

5. **Use in Applications**
   ```python
   # Chatbot integration
   from deliverables.scripts.database_interface import ARGODatabaseInterface
   db = ARGODatabaseInterface("your_database_url")
   results = db.search_by_location(10, 25, 50, 75)
   ```

## 🔧 Configuration

### Database Configuration

**⚠️ SECURITY WARNING: Never commit real credentials to version control!**

The project uses environment variables for database configuration. Set your database URL:

```bash
export DATABASE_URL="postgresql://your_username:your_password@localhost:5432/argo_database"
```

Or create a `.env` file (make sure to add it to `.gitignore`):
```bash
echo "DATABASE_URL=postgresql://your_username:your_password@localhost:5432/argo_database" > .env
```

### Processing Settings

```python
# Indian Ocean bounds
INDIAN_OCEAN_BOUNDS = {
    'lon_min': 20.0,   # 20°E
    'lon_max': 146.0,  # 146°E
    'lat_min': -60.0,  # 60°S
    'lat_max': 30.0    # 30°N
}

# Quality control flags
ACCEPTED_QC_FLAGS = [1, 2]  # 1=good, 2=probably good
```

## 📊 Database Schema

### Core Tables

- **`argo_profiles`**: Main profile data with measurements
- **`argo_floats`**: Float metadata and status

### Key Fields

- `profile_id`: Unique identifier
- `float_id`: ARGO float identifier
- `latitude`, `longitude`: Geographic coordinates
- `temperature[]`, `salinity[]`: Measurement arrays
- `profile_date`, `profile_time`: Temporal information

## 🔍 Vector Search

The system includes semantic search capabilities:

```python
# Search for similar profiles
results = vector_manager.search_similar_profiles(
    query="warm tropical surface waters",
    n_results=5
)
```

## 📈 Data Statistics

- **Coverage**: Indian Ocean (2019-2025)
- **Profiles**: 122,215+ oceanographic profiles
- **Floats**: 1,000+ ARGO floats
- **Measurements**: Temperature, salinity, pressure, depth
- **Quality**: QC-filtered data

## 🛠️ Development

### Running Tests

```bash
# Test database connection
python -c "from src.argo_data_processor import ArgoDataProcessor; ArgoDataProcessor().connect_db()"

# Test vector database
python -c "from src.vector_db_manager import VectorDBManager; VectorDBManager().test_sample_processing()"
```

### Adding New Features

1. Create new modules in `src/`
2. Update `requirements.txt` for new dependencies
3. Add database migrations in `sql/`
4. Update documentation

## 📦 Export and Delivery

### Database Export

```python
from deliverables.scripts.create_database_export import create_database_export

# Create compressed database export
export_file = create_database_export()
print(f"Database exported to: {export_file}")
```

### Metadata Summaries

```python
from deliverables.scripts.export_summaries import export_metadata_summaries

# Generate metadata summaries for vector search
summary_file = export_metadata_summaries()
print(f"Summaries exported to: {summary_file}")
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify connection string in environment variables
   - Ensure database exists: `psql -l | grep argo_database`
   - Check user permissions: `psql -d argo_database -c "\du"`

2. **NetCDF Processing Errors**
   - Check file format: `ncdump -h your_file.nc`
   - Verify Python dependencies: `pip list | grep netCDF4`
   - Review log files in `logs/processing.log`
   - Test with single file first

3. **Vector Database Issues**
   - Ensure ChromaDB is installed: `pip show chromadb`
   - Check sentence-transformers model download
   - Verify sufficient disk space: `df -h`
   - Test with sample data first: `vector_manager.test_sample_processing()`

4. **Memory Issues**
   - Reduce batch size in `config.py`
   - Process files in smaller batches
   - Monitor memory usage: `htop` or `top`

### Log Files

- `logs/processing.log`: NetCDF processing logs
- `logs/batch_processing.log`: Batch operation logs
- `logs/vector_db.log`: Vector database operations

## 📝 Dependencies

### Core Dependencies
- `numpy>=1.21.0`
- `pandas>=1.3.0`
- `netCDF4>=1.6.0`
- `xarray>=0.20.0`
- `psycopg2-binary>=2.9.0`
- `SQLAlchemy>=1.4.0`

### Vector Search
- `sentence-transformers>=2.2.0`
- `chromadb>=0.4.0`
- `faiss-cpu>=1.7.0`

### Development
- `pytest>=6.0.0`
- `pytest-cov>=3.0.0`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or issues:
- Check the troubleshooting section
- Review log files for error details
- Create an issue in the repository

## 🎯 Use Cases

- **Oceanographic Research**: Climate studies, ocean circulation analysis
- **Data Science**: Machine learning on oceanographic data
- **Education**: Teaching oceanography and data processing
- **Chatbot Integration**: Semantic search for oceanographic queries
- **Marine Biology**: Study of ocean ecosystems and habitats
- **Climate Monitoring**: Long-term ocean temperature and salinity trends

## 📊 Performance

- **Processing Speed**: ~100 files/minute
- **Database Size**: ~747 MB (compressed)
- **Vector Search**: Sub-second response times
- **Memory Usage**: ~2-4 GB during processing

---

**Built with ❤️ for oceanographic data processing and analysis.**
