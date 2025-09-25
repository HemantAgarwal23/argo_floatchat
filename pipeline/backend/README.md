# ARGO FloatChat Backend

FastAPI-based backend service for the ARGO FloatChat oceanographic data analysis platform.

## 🏗️ Architecture

The backend is built using FastAPI and follows a modular architecture:

```
app/
├── api/routes/          # REST API endpoints
├── core/               # Core services (database, LLM clients)
├── services/           # Business logic and AI services
├── models/             # Data models and schemas
└── utils/              # Utility functions
```

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   cp env_template.txt .env
   # Edit .env with your configuration
   ```

3. **Run the Server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## 📡 API Endpoints

### Query Processing
- `POST /api/v1/query/process` - Process natural language queries
- `GET /api/v1/query/health` - Health check endpoint

### Data Retrieval
- `GET /api/v1/data/profiles` - Get ARGO profiles
- `GET /api/v1/data/floats` - Get ARGO float metadata

## 🔧 Configuration

See `config.py` for all configuration options.

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

## 📊 Database

The system uses PostgreSQL with the following main tables:
- `argo_profiles` - Float profile data
- `argo_floats` - Float metadata

## 🤖 AI Services

- **SQL Generation**: Intelligent SQL query creation
- **Query Classification**: Determines query type
- **Geographic Validation**: Prevents hallucination
- **LLM Integration**: Multi-provider support (Groq, Ollama)