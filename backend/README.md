# ARGO AI Backend

An AI-powered conversational system for ARGO float oceanographic data that enables users to query, explore, and visualize ocean data using natural language.

## 🌊 Features

- **Natural Language Queries**: Ask questions like "Show me salinity profiles near the equator in March 2023"
- **Intelligent Query Classification**: Automatically determines whether to use SQL or semantic search
- **RAG Pipeline**: Retrieval-Augmented Generation for accurate, context-aware responses
- **Multi-modal Data Access**: Both structured database queries and semantic vector search
- **Real-time Processing**: Fast responses using Groq API with Llama 3.1
- **Comprehensive API**: RESTful endpoints for all functionality
- **Visualization Suggestions**: Automatically suggests appropriate charts and maps

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │────│   FastAPI API    │────│  Query Classifier│
│   (External)    │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   RAG Pipeline   │────│   LLM Client    │
                       │                  │    │   (Groq API)    │
                       └──────────────────┘    └─────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌───────────────┐      ┌─────────────────┐
            │ PostgreSQL DB │      │ ChromaDB Vector │
            │ (Structured)  │      │ (Semantic)      │
            └───────────────┘      └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- 8GB+ RAM (for embedding models)

### Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd argo-ai-backend
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. **Run complete setup**:
```bash
python scripts/complete_setup.py
```

5. **Start the server**:
```bash
python run.py
```

6. **Test the API**:
Visit `http://localhost:8000/docs` for interactive API documentation

## 📊 Data Coverage

Our system includes:
- **122,000+ ARGO profiles**
- **1,800+ floats**
- **Core parameters**: Temperature, Salinity, Pressure, Depth
- **BGC parameters**: Dissolved Oxygen, pH, Nitrate, Chlorophyll-a
- **Geographic focus**: Indian Ocean, Arabian Sea, Bay of Bengal
- **Temporal coverage**: 2000-present

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=argo_database
DB_USER=jayansh
DB_PASSWORD=your_password

# Groq API
GROQ_API_KEY=your_groq_api_key

# Application
DEBUG=true
HOST=127.0.0.1
PORT=8000
```

### Database Setup

The system uses two databases:

1. **PostgreSQL** (Structured Data):
   - `argo_floats`: Float metadata
   - `argo_profiles`: Profile measurements with arrays for oceanographic parameters

2. **ChromaDB** (Semantic Search):
   - Metadata summaries for semantic search
   - Embedding-based similarity matching

## 📡 API Usage

### Main Query Endpoint

```bash
curl -X POST 'http://localhost:8000/api/v1/query' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Show me temperature profiles in the Arabian Sea from 2023",
    "max_results": 10
  }'
```

### Direct Data Search

```bash
curl -X POST 'http://localhost:8000/api/v1/data/search' \
  -H 'Content-Type: application/json' \
  -d '{
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "min_latitude": 10,
    "max_latitude": 25,
    "parameters": ["temperature", "salinity"]
  }'
```

### Example Queries

#### Data Retrieval Queries
- "Show me salinity profiles for float 7900617"
- "Get temperature data near the equator in March 2023"
- "Find all profiles with dissolved oxygen measurements"

#### Analytical Queries
- "Compare BGC parameters in the Arabian Sea for the last 6 months"
- "What are the temperature trends in the Indian Ocean?"
- "Summarize seasonal variations in chlorophyll levels"

#### Exploratory Queries
- "What can you tell me about ocean warming patterns?"
- "Describe the characteristics of ARGO float data"
- "How does salinity vary with depth in the Southern Ocean?"

## 🔍 Query Processing

The system intelligently routes queries:

1. **SQL Retrieval**: For specific data requests
   - Structured filtering and aggregation
   - Precise geographic and temporal queries
   - Parameter-specific searches

2. **Vector Retrieval**: For conceptual questions
   - Semantic similarity search
   - Pattern analysis and summaries
   - Exploratory data questions

3. **Hybrid Retrieval**: For complex analytical queries
   - Combines both approaches
   - Comprehensive data analysis

## 🛠️ Development

### Project Structure

```
argo-ai-backend/
├── app/
│   ├── api/routes/          # API endpoints
│   ├── core/               # Database and LLM clients
│   ├── services/           # Business logic
│   ├── models/             # Pydantic models
│   └── utils/              # Utilities
├── data/                   # Data files
├── scripts/               # Setup scripts
└── tests/                 # Test suite
```

### Running Tests

```bash
pytest tests/
```

### Manual Setup (Alternative)

If the complete setup fails, run individual steps:

```bash
# Database setup
python scripts/setup_database.py

# Vector database setup
python scripts/setup_vector_db.py
```

## 📈 Performance

- **Query Response Time**: < 2 seconds average
- **Concurrent Users**: 50+ simultaneous queries
- **Database Performance**: Optimized for ARGO data patterns
- **Vector Search**: Sub-second semantic similarity

## 🔒 Security

- Input validation on all endpoints
- SQL injection prevention
- Rate limiting (configurable)
- Structured logging for audit trails

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   ```bash
   # Check PostgreSQL service
   brew services restart postgresql  # macOS
   sudo systemctl restart postgresql # Linux
   ```

2. **Vector Database Empty**:
   ```bash
   python scripts/setup_vector_db.py
   ```

3. **Groq API Errors**:
   - Verify API key in `.env`
   - Check rate limits

4. **Memory Issues**:
   - Reduce `max_results` in queries
   - Restart the application

### Health Checks

```bash
# Overall system health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/database

# Vector database health
curl http://localhost:8000/health/vector-db
```

## 🤝 Contributing

This is a hackathon project built for the ARGO AI challenge. The system demonstrates:

- **End-to-end RAG pipeline** for oceanographic data
- **Natural language interface** for complex scientific queries
- **Scalable architecture** for real-world deployment
- **Multi-modal data access** combining SQL and vector search

## 📜 License

This project is built for educational and research purposes.

## 🎯 Future Enhancements

- [ ] Real-time data ingestion from ARGO DAC
- [ ] Advanced visualization generation
- [ ] Multi-language support
- [ ] Custom model fine-tuning
- [ ] Integration with satellite data
- [ ] Export to NetCDF format
- [ ] Advanced geospatial analysis

---

Built with ❤️ for the ARGO AI Hackathon