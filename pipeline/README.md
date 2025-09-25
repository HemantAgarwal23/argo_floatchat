# 🌊 ARGO FloatChat

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A sophisticated **AI-powered oceanographic data analysis platform** that enables natural language querying of ARGO float data through advanced RAG (Retrieval Augmented Generation) techniques, intelligent SQL generation, and interactive visualizations.

## 🎯 Overview

ARGO FloatChat revolutionizes oceanographic data exploration by allowing researchers, students, and ocean enthusiasts to interact with complex ARGO float datasets using simple, natural language queries. The system combines cutting-edge AI technologies with robust data processing to provide accurate, real-time insights into oceanographic phenomena.

### 🌟 Key Features

- **🗣️ Natural Language Interface**: Query oceanographic data using plain English
- **🧠 Intelligent SQL Generation**: Automatic conversion of queries to optimized SQL
- **🗺️ Geographic Intelligence**: Advanced location-based queries with Haversine distance calculations
- **📊 Interactive Visualizations**: Dynamic maps, charts, and data exploration tools
- **🔄 Multi-LLM Support**: Groq API with Ollama fallback for reliable responses
- **⚡ Real-time Processing**: Fast query processing with comprehensive error handling
- **🛡️ Anti-Hallucination**: Geographic validation prevents inaccurate data responses
- **🔍 Vector Search**: Semantic search capabilities using ChromaDB
- **📈 Statistical Analysis**: Built-in statistical functions and data aggregation

## 🏗️ System Architecture

### Backend (FastAPI)
```
backend/
├── app/
│   ├── api/routes/          # REST API endpoints
│   ├── core/                # Core services (database, LLM clients)
│   ├── services/            # Business logic and AI services
│   ├── models/              # Data models and schemas
│   └── utils/               # Utility functions
├── scripts/                 # Database setup and utilities
└── tests/                   # Test suite
```

**Key Components:**
- **Query Classifier**: Determines query type (SQL, vector, hybrid)
- **SQL Generator**: Intelligent SQL creation with validation and error correction
- **Database Manager**: PostgreSQL integration with ARGO data
- **Vector Search**: ChromaDB for semantic search capabilities
- **LLM Integration**: Multi-provider LLM support (Groq, Ollama)
- **Geographic Validator**: Prevents queries for unsupported regions

### Frontend (Streamlit)
```
frontend/
├── floatchat_app.py         # Main Streamlit application
├── backend_adapter.py       # API communication layer
├── frontend_config.py       # Configuration management
└── static/                  # Static assets
```

**Key Features:**
- **Interactive UI**: User-friendly interface for querying
- **Real-time Visualization**: Dynamic maps and charts using Plotly
- **Query History**: Track and revisit previous queries
- **Responsive Design**: Optimized for various screen sizes
- **Error Handling**: Comprehensive error display and recovery

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.9+** (recommended: Python 3.11)
- **PostgreSQL 13+** with PostGIS extension
- **Git** for version control
- **8GB+ RAM** (for optimal performance)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/argo-floatchat.git
   cd argo-floatchat
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp backend/env_template.txt backend/.env
   # Edit backend/.env with your configuration:
   # - GROQ_API_KEY=your_groq_api_key
   # - DATABASE_URL=postgresql://user:password@localhost:5432/argo_db
   # - OLLAMA_BASE_URL=http://localhost:11434 (optional)
   ```

5. **Database Setup**
   ```bash
   cd backend
   python scripts/setup_database.py
   ```

6. **Launch the Application**
   ```bash
   # Terminal 1 - Backend API
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --port 8000

   # Terminal 2 - Frontend UI
   cd frontend
   source venv/bin/activate
   streamlit run floatchat_app.py --server.port 8501
   ```

7. **Access the Application**
   - **Frontend UI**: http://localhost:8501
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Interactive API**: http://localhost:8000/redoc

## 📊 Query Examples

### 🌍 Geographic Queries
```sql
-- Find floats near specific coordinates
"Find ARGO floats near coordinates 20°N, 70°E"

-- Regional data exploration
"Show float trajectories in the Arabian Sea"
"Display data from the equatorial region"
"Find floats in the Bay of Bengal"

-- Distance-based searches
"Show floats within 100km of Mumbai"
```

### 📅 Temporal Queries
```sql
-- Time-based comparisons
"Compare salinity data between 2022 and 2023"
"Show temperature profiles from the last month"
"Find data from December 2023"

-- Duration analysis
"Find floats operating for more than 2 years"
"Show floats that started in 2020"
```

### 📈 Statistical Queries
```sql
-- Aggregations
"What is the average temperature in the Indian Ocean?"
"How many profiles were collected in 2023?"
"Find the deepest profiles recorded"

-- Comparative analysis
"Compare surface temperatures across different latitudes"
"Show salinity variations by depth"
```

### 🔬 Scientific Queries
```sql
-- Oceanographic parameters
"Show temperature profiles with depth"
"Find salinity measurements near the surface"
"Display pressure data from deep profiles"

-- Environmental conditions
"Find profiles with high temperature anomalies"
"Show data from areas with low oxygen levels"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GROQ_API_KEY` | Groq API key for LLM services | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `OLLAMA_BASE_URL` | Ollama server URL for local LLM | No | `http://localhost:11434` |
| `CHROMA_PERSIST_DIR` | ChromaDB persistence directory | No | `./data/vector_db` |
| `MAX_SEARCH_RESULTS` | Maximum results per query | No | `25` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

### Database Schema

The system uses a PostgreSQL database with the following main tables:

#### `argo_profiles`
```sql
CREATE TABLE argo_profiles (
    profile_id VARCHAR PRIMARY KEY,
    float_id VARCHAR NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    profile_date TIMESTAMP,
    temperature REAL[],
    salinity REAL[],
    pressure REAL[],
    max_pressure REAL,
    -- Additional oceanographic parameters
);
```

#### `argo_floats`
```sql
CREATE TABLE argo_floats (
    float_id VARCHAR PRIMARY KEY,
    status VARCHAR,
    float_type VARCHAR,
    institution VARCHAR,
    -- Additional metadata
);
```

## 🧪 Testing

### Run Test Suite
```bash
cd backend
python -m pytest tests/ -v
```

### Test Coverage
```bash
cd backend
python -m pytest tests/ --cov=app --cov-report=html
```

### Manual Testing
1. Start both backend and frontend services
2. Navigate to http://localhost:8501
3. Try various query types from the examples above
4. Verify responses are accurate and well-formatted

## 📁 Project Structure

```
argo_floatchat/
├── 📁 backend/                    # FastAPI backend
│   ├── 📁 app/
│   │   ├── 📁 api/routes/         # API endpoints
│   │   │   ├── query.py          # Main query processing
│   │   │   ├── data.py           # Data retrieval
│   │   │   └── health.py         # Health checks
│   │   ├── 📁 core/              # Core services
│   │   │   ├── database.py       # Database management
│   │   │   ├── llm_client.py     # LLM integration
│   │   │   ├── multi_llm_client.py # Multi-provider LLM
│   │   │   ├── ollama_client.py  # Ollama integration
│   │   │   └── vector_db.py      # Vector database
│   │   ├── 📁 services/          # Business logic
│   │   │   ├── intelligent_sql_generator.py # SQL generation
│   │   │   ├── rag_pipeline.py   # RAG orchestration
│   │   │   ├── query_classifier.py # Query classification
│   │   │   ├── geographic_validator.py # Geographic validation
│   │   │   └── visualization_generator.py # Chart generation
│   │   ├── 📁 models/            # Data models
│   │   └── 📁 utils/             # Utilities
│   ├── 📁 scripts/               # Setup scripts
│   ├── 📄 requirements.txt       # Python dependencies
│   ├── 📄 env_template.txt       # Environment template
│   └── 📄 README.md             # Backend documentation
├── 📁 frontend/                   # Streamlit frontend
│   ├── 📄 floatchat_app.py       # Main application
│   ├── 📄 backend_adapter.py     # API communication
│   ├── 📄 frontend_config.py     # Configuration
│   ├── 📄 requirements.txt       # Frontend dependencies
│   └── 📁 static/                # Static assets
├── 📄 README.md                  # This file
├── 📄 .gitignore                 # Git ignore rules
└── 📄 LICENSE                    # MIT License
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Production Setup
1. Set up PostgreSQL with proper security
2. Configure environment variables
3. Use a production WSGI server (Gunicorn)
4. Set up reverse proxy (Nginx)
5. Enable HTTPS with SSL certificates

### Cloud Deployment
- **AWS**: Use RDS for PostgreSQL, ECS for containers
- **Google Cloud**: Cloud SQL + Cloud Run
- **Azure**: Azure Database + Container Instances

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/argo-floatchat.git
   cd argo-floatchat
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make Your Changes**
   - Follow PEP 8 style guidelines
   - Add tests for new functionality
   - Update documentation as needed

4. **Commit Your Changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```

5. **Push to Your Branch**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure all tests pass

### Development Guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Follow the existing code structure
- Test your changes thoroughly

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ARGO Program** for providing invaluable oceanographic data
- **FastAPI** and **Streamlit** communities for excellent frameworks
- **Groq** for high-performance LLM API services
- **Ollama** for local LLM capabilities
- **PostgreSQL** and **ChromaDB** for robust data storage
- **Plotly** for beautiful visualizations

## 📞 Support & Community

- **Issues**: [GitHub Issues](https://github.com/yourusername/argo-floatchat/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/argo-floatchat/discussions)
- **Documentation**: [Project Wiki](https://github.com/yourusername/argo-floatchat/wiki)

## 🔬 Research Applications

ARGO FloatChat is designed for:
- **Oceanographic Research**: Data analysis and hypothesis testing
- **Educational Use**: Teaching oceanography and data science
- **Climate Studies**: Long-term trend analysis
- **Marine Biology**: Environmental correlation studies
- **Policy Making**: Evidence-based ocean management

## 📈 Roadmap

### Version 2.0 (Planned)
- [ ] Real-time data streaming
- [ ] Advanced machine learning models
- [ ] Multi-language support
- [ ] Mobile application
- [ ] Collaborative features

### Version 1.1 (Next)
- [ ] Additional visualization types
- [ ] Export functionality
- [ ] User authentication
- [ ] Query optimization

---

**⚠️ Important Note**: This system is designed for oceanographic research and education. Ensure you have proper data usage permissions and follow relevant data policies when working with ARGO data.

**🌊 Dive deep into ocean data with ARGO FloatChat!** 🚀