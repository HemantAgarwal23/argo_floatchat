# ARGO FloatChat 🌊

**AI-Powered Oceanographic Data Discovery & Visualization Platform**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🎯 Overview

ARGO FloatChat is a comprehensive AI-powered platform for discovering, analyzing, and visualizing oceanographic data from ARGO floats. Built for researchers, educators, and ocean enthusiasts, it provides natural language interfaces, multilingual support, and advanced visualization capabilities for ocean data exploration.

### 🌟 Key Features

- **🤖 AI-Powered Queries**: Natural language processing for oceanographic data
- **🌍 Multilingual Support**: 12 languages with intelligent translation
- **📊 Advanced Visualizations**: Interactive maps, charts, and 3D plots
- **🔍 RAG Pipeline**: Retrieval-Augmented Generation for accurate responses
- **⚡ Real-time Processing**: Fast responses using modern AI models
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **🔧 MCP Integration**: Model Context Protocol for AI client integration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ARGO FloatChat Platform                  │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Streamlit)   │  Backend (FastAPI)   │  Data Pipeline │
│  ┌─────────────────┐    │  ┌─────────────────┐ │ ┌────────────┐ │
│  │ Multilingual UI │    │  │ RAG Pipeline    │ │ │ETL Process │ │
│  │ Visualization   │◄───┤  │ LLM Integration │◄──┤Data Source │ │
│  │ Query Interface │    │  │ Vector Search   │ │ │ Processing │ │
│  └─────────────────┘    │  └─────────────────┘ │ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **PostgreSQL 12+** (for data storage)
- **8GB+ RAM** (for AI models and data processing)
- **Internet connection** (for AI API access)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/HemantAgarwal23/argo_floatchat.git
cd argo_floatchat
```

2. **Set up the backend**:
```bash
cd backend
pip install -r requirements.txt
python scripts/complete_setup.py
```

3. **Set up the frontend**:
```bash
cd ../frontend
pip install -r requirements.txt
```

4. **Set up the data pipeline** (optional):
```bash
cd ../data_etl_pipeline
pip install -r requirements.txt
```

5. **Configure environment**:
```bash
# Create .env file in backend directory
# Copy the example and edit with your credentials
# You'll need to create .env file manually with your database and API keys
```

### Running the Application

1. **Start the backend**:
```bash
cd backend
python run.py
```

2. **Start the frontend** (in a new terminal):
```bash
cd frontend
python start_app.py
```

3. **Open your browser**:
Navigate to `http://localhost:8501`

## 📁 Project Structure

```
argo_floatchat/
├── 📁 backend/                 # FastAPI backend with AI/ML capabilities
│   ├── 📁 app/                 # Core application modules
│   │   ├── 📁 api/             # REST API endpoints
│   │   ├── 📁 core/            # Database and LLM clients
│   │   ├── 📁 services/        # Business logic and RAG pipeline
│   │   └── 📁 models/          # Pydantic data models
│   ├── 📁 scripts/             # Setup and utility scripts
│   ├── 📄 README.md           # Backend documentation
│   └── 📄 requirements.txt    # Backend dependencies
├── 📁 frontend/                # Streamlit web interface
│   ├── 📁 locales/             # Multilingual translation files
│   ├── 📄 floatchat_app.py    # Main Streamlit application
│   ├── 📄 README.md           # Frontend documentation
│   └── 📄 requirements.txt    # Frontend dependencies
├── 📁 data_etl_pipeline/       # Data processing and ETL
│   ├── 📁 scripts/            # Data processing scripts
│   ├── 📁 data/               # Processed data files
│   ├── 📄 README.md           # Pipeline documentation
│   └── 📄 requirements.txt    # Pipeline dependencies
├── 📄 .gitignore              # Git ignore rules
└── 📄 README.md               # This file
```

## 🌊 Data Coverage

### Geographic Scope
- **Primary Focus**: Indian Ocean region (20°E to 160°E, -60°S to 27°N)
- **Sub-regions**: Arabian Sea, Bay of Bengal, Andaman Sea
- **Coverage**: 122,000+ ARGO profiles from 1,800+ floats

### Oceanographic Parameters
- **Core Parameters**: Temperature, Salinity, Pressure, Depth
- **BGC Parameters**: Dissolved Oxygen, pH, Nitrate, Chlorophyll-a
- **Temporal Range**: 2000-present (with focus on recent data)

### Data Sources
- **ARGO Float Network**: International oceanographic floats
- **Real-time Data**: Live data from active floats
- **Historical Archives**: Comprehensive historical datasets

## 🎯 Use Cases

### 🔬 **Research Applications**
- **Climate Studies**: Ocean temperature and salinity trends
- **Ecosystem Analysis**: Biogeochemical parameter studies
- **Ocean Circulation**: Current and water mass analysis
- **Environmental Monitoring**: Pollution and ecosystem health

### 🎓 **Educational Use**
- **Student Projects**: Oceanographic data analysis assignments
- **Interactive Learning**: Visual exploration of ocean processes
- **Multilingual Education**: Global accessibility for students
- **Data Literacy**: Teaching data analysis and visualization

### 🌍 **Public Engagement**
- **Ocean Awareness**: Public understanding of ocean processes
- **Climate Communication**: Visualizing climate change impacts
- **Citizen Science**: Community involvement in ocean research
- **Policy Support**: Data-driven ocean management decisions

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=argo_database
DB_USER=your_username
DB_PASSWORD=your_password

# AI/ML Configuration
GROQ_API_KEY=your_groq_api_key
HUGGINGFACE_API_KEY=your_hf_api_key  # Optional

# Application Settings
DEBUG=true
HOST=127.0.0.1
PORT=8000
```

### API Keys

1. **Groq API**: Get your free API key from [console.groq.com](https://console.groq.com/)
2. **Hugging Face** (optional): Get API key from [huggingface.co](https://huggingface.co/)

## 📊 Features by Component

### 🖥️ **Frontend (Streamlit)**
- **Multilingual Interface**: 12 language support
- **Interactive Visualizations**: Maps, charts, and 3D plots
- **Natural Language Queries**: Ask questions in plain language
- **Real-time Results**: Instant data retrieval and visualization
- **Export Capabilities**: Download data and visualizations
- **Responsive Design**: Works on all devices

### ⚙️ **Backend (FastAPI)**
- **RAG Pipeline**: Intelligent query processing
- **Vector Search**: Semantic similarity matching
- **SQL Generation**: Automatic database query creation
- **LLM Integration**: Multiple AI model support
- **API Documentation**: Interactive API docs
- **Health Monitoring**: System status and diagnostics

### 📊 **Data Pipeline (ETL)**
- **Automated Processing**: NetCDF to structured data
- **Data Validation**: Quality checks and verification
- **PostgreSQL Integration**: Optimized database schema
- **Vector Summaries**: Metadata for semantic search
- **Error Handling**: Robust retry mechanisms

## 🧪 Testing

### Run All Tests

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd ../frontend
python test_app_startup.py
python test_backend_connection.py
python test_multilingual.py

# Data pipeline tests
cd ../data_etl_pipeline
python scripts/verify_downloads.py 2021
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/database

# Vector database health
curl http://localhost:8000/health/vector-db
```

## 🚀 Deployment

### Development

```bash
# Start all services
cd backend && python run.py &
cd frontend && python start_app.py &
```

### Production

```bash
# Use production configuration
export DEBUG=false
export LOG_LEVEL=INFO

# Start with production settings
cd backend && python run.py
cd frontend && python start_app.py
```

### Docker (Coming Soon)

```bash
# Build and run with Docker
docker-compose up -d
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and test thoroughly
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Guidelines

- **Code Style**: Follow PEP 8 for Python
- **Documentation**: Add docstrings and comments
- **Testing**: Write tests for new features
- **Multilingual**: Update all language files for UI changes

## 📜 License

This project is built for educational and research purposes as part of the ARGO AI Hackathon. See [LICENSE](LICENSE) for details.

## 🎯 Roadmap

### 🚀 **Phase 1 - Current**
- ✅ Core RAG pipeline implementation
- ✅ Multilingual frontend interface
- ✅ Basic visualization capabilities
- ✅ Data ETL pipeline

### 🔮 **Phase 2 - Near Future**
- [ ] Real-time data streaming
- [ ] Advanced ML models
- [ ] Mobile application
- [ ] API rate limiting and optimization

### 🌟 **Phase 3 - Future**
- [ ] Satellite data integration
- [ ] Custom model fine-tuning
- [ ] Collaborative features
- [ ] Advanced analytics dashboard

## 📞 Support

### Getting Help

1. **Documentation**: Check component-specific README files
2. **Issues**: Report bugs on GitHub Issues
3. **Discussions**: Join community discussions
4. **Email**: Contact the development team

### Common Issues

- **Database Connection**: Check PostgreSQL service and credentials
- **API Keys**: Verify Groq API key is valid and has credits
- **Memory Issues**: Ensure sufficient RAM for AI models
- **Port Conflicts**: Check if ports 8000 and 8501 are available

## 🙏 Acknowledgments

- **ARGO Program**: For providing oceanographic data
- **Open Source Community**: For excellent Python libraries
- **AI/ML Providers**: Groq and Hugging Face for AI capabilities
- **Ocean Research Community**: For inspiration and feedback

## 📈 Statistics

- **122,000+** ARGO profiles processed
- **1,800+** ARGO floats in database
- **12** supported languages
- **50+** API endpoints
- **100+** visualization types

---

**Built with ❤️ for oceanographic research and education**

*Making ocean data accessible to everyone, everywhere* 🌊

---

## 🔗 Quick Links

- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [Data Pipeline Documentation](data_etl_pipeline/README.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Live Demo](http://localhost:8501) (when running)
