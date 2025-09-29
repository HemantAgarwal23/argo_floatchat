# ARGO FloatChat Frontend

**Multilingual AI-powered oceanographic data discovery and visualization interface built with Streamlit.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)

## 🌊 Overview

FloatChat Frontend is a sophisticated web application that provides an intuitive interface for querying and visualizing ARGO oceanographic data. Built with Streamlit, it offers multilingual support, real-time data visualization, and seamless integration with the ARGO AI backend.

## ✨ Features

### 🌍 **Multilingual Support**
- **12 Languages**: English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi
- **Intelligent Translation**: Automatic query translation and response localization
- **Scientific Terminology**: Preserved oceanographic terms across languages

### 📊 **Advanced Visualizations**
- **Interactive Maps**: Geographic visualization of ARGO float locations
- **Time Series Plots**: Temporal analysis of oceanographic parameters
- **Profile Visualizations**: Depth-based parameter analysis
- **Statistical Charts**: Bar charts, scatter plots, and correlation matrices
- **3D Surface Plots**: Multi-dimensional data representation

### 🔍 **Intelligent Query Interface**
- **Natural Language Processing**: Ask questions in plain language
- **Query Suggestions**: Pre-built query templates for common analyses
- **Real-time Results**: Instant data retrieval and visualization
- **Context-Aware Responses**: Intelligent follow-up suggestions

### 🎯 **User Experience**
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark/Light Themes**: Customizable interface appearance
- **Session Management**: Persistent chat history and user preferences
- **Export Capabilities**: Download data and visualizations

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- ARGO AI Backend running (see `../backend/README.md`)
- 4GB+ RAM recommended

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/your-org/argo-floatchat.git
cd argo-floatchat/frontend
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
# Copy and edit configuration
cp frontend_config.py.example frontend_config.py
# Edit backend URL and other settings
```

5. **Start the application**:
```bash
python start_app.py
```

6. **Open your browser**:
Navigate to `http://localhost:8501`

## 📱 Usage

### Basic Workflow

1. **Select Language**: Choose your preferred language from the sidebar
2. **Ask Questions**: Type natural language queries about ocean data
3. **View Results**: Explore interactive visualizations and data tables
4. **Export Data**: Download results in various formats

### Example Queries

#### 🌡️ **Temperature Analysis**
```
"Show me temperature profiles in the Arabian Sea for 2023"
"Compare surface temperatures between different regions"
"What are the temperature trends in the Indian Ocean?"
```

#### 🧂 **Salinity Studies**
```
"Find salinity data near the equator"
"Analyze salinity variations with depth"
"Compare salinity levels in different ocean basins"
```

#### 🧬 **Biogeochemical Parameters**
```
"Show me dissolved oxygen levels in the Bay of Bengal"
"Find chlorophyll-a concentrations for the last 6 months"
"Analyze nitrate levels in different water depths"
```

#### 🌍 **Geographic Queries**
```
"Show me all ARGO floats in the Indian Ocean"
"Find data near coordinates 20°N, 70°E"
"Compare data between Arabian Sea and Bay of Bengal"
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│  Backend Adapter │────│  ARGO Backend   │
│                 │    │                 │    │   (FastAPI)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Multilingual    │    │  HTTP Client     │    │  RAG Pipeline   │
│ Components      │    │  (aiohttp)      │    │  (AI/ML)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
frontend/
├── floatchat_app.py          # Main Streamlit application
├── backend_adapter.py         # Backend communication layer
├── frontend_config.py         # Configuration management
├── i18n.py                   # Internationalization system
├── multilingual_components.py # Multilingual UI components
├── start_app.py              # Application launcher
├── locales/                  # Translation files
│   ├── en.json              # English translations
│   ├── es.json              # Spanish translations
│   ├── fr.json              # French translations
│   └── hi.json              # Hindi translations
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## ⚙️ Configuration

### Environment Variables

```bash
# Backend Configuration
BACKEND_URL=http://localhost:8000
BACKEND_TIMEOUT=30

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
MAX_FILE_SIZE=10MB

# Multilingual Settings
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,es,fr,de,it,pt,ru,zh,ja,ko,ar,hi
```

### Frontend Configuration

Edit `frontend_config.py` to customize:

```python
class FrontendConfig:
    # Backend API settings
    BACKEND_URL = "http://localhost:8000"
    API_TIMEOUT = 30
    
    # UI settings
    PAGE_TITLE = "ARGO FloatChat"
    PAGE_ICON = "🌊"
    LAYOUT = "wide"
    
    # Visualization settings
    MAX_POINTS_PER_CHART = 10000
    DEFAULT_CHART_HEIGHT = 400
```

## 🎨 Customization

### Adding New Languages

1. **Create translation file**:
```bash
# Create new locale file
cp locales/en.json locales/your_language.json
```

2. **Add translations**:
```json
{
  "language_name": "Your Language",
  "welcome_message": "Welcome to ARGO FloatChat",
  "query_placeholder": "Ask about ocean data...",
  "visualizations": "Visualizations",
  "data_table": "Data Table"
}
```

3. **Update configuration**:
```python
# In frontend_config.py
SUPPORTED_LANGUAGES = ["en", "es", "fr", "your_language"]
```

### Custom Visualizations

Add new visualization types in `multilingual_components.py`:

```python
def create_custom_chart(data, chart_type, language="en"):
    """Create custom visualization"""
    # Implementation here
    pass
```

## 🧪 Testing

### Run Tests

```bash
# Test application startup
python test_app_startup.py

# Test backend connection
python test_backend_connection.py

# Test multilingual functionality
python test_multilingual.py

# Test internationalization
python test_i18n_simple.py
```

### Manual Testing

1. **Language Switching**: Test all supported languages
2. **Query Processing**: Try various natural language queries
3. **Visualization Rendering**: Verify charts and maps display correctly
4. **Data Export**: Test download functionality
5. **Responsive Design**: Test on different screen sizes

## 🐛 Troubleshooting

### Common Issues

1. **Backend Connection Failed**:
   ```bash
   # Check if backend is running
   curl http://localhost:8000/health
   
   # Verify backend URL in frontend_config.py
   ```

2. **Translation Not Loading**:
   ```bash
   # Check locale files exist
   ls locales/
   
   # Verify JSON syntax
   python -m json.tool locales/en.json
   ```

3. **Visualization Not Rendering**:
   ```bash
   # Check browser console for errors
   # Verify data format from backend
   # Test with smaller datasets
   ```

4. **Performance Issues**:
   ```bash
   # Reduce MAX_POINTS_PER_CHART in config
   # Enable data pagination
   # Use data sampling for large datasets
   ```

### Debug Mode

Enable debug mode for detailed logging:

```python
# In frontend_config.py
DEBUG = True
LOG_LEVEL = "DEBUG"
```

## 📊 Performance

### Optimization Tips

- **Data Pagination**: Large datasets are automatically paginated
- **Chart Limits**: Maximum points per chart configurable
- **Caching**: Query results are cached for faster subsequent access
- **Lazy Loading**: Visualizations load on-demand

### System Requirements

- **Minimum**: 4GB RAM, 2 CPU cores
- **Recommended**: 8GB RAM, 4 CPU cores
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and test thoroughly**
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open Pull Request**

### Code Style

- Follow PEP 8 for Python code
- Use type hints for function parameters
- Add docstrings for all functions
- Test all new features thoroughly

## 📜 License

This project is part of the ARGO AI Hackathon and is built for educational and research purposes.

## 🎯 Future Enhancements

- [ ] **Real-time Data**: Live data streaming from ARGO floats
- [ ] **Advanced Analytics**: Machine learning-powered insights
- [ ] **Collaborative Features**: Shared sessions and annotations
- [ ] **Mobile App**: Native mobile application
- [ ] **API Integration**: Direct API access for developers
- [ ] **Custom Dashboards**: User-configurable dashboard layouts

## 📞 Support

For issues or questions:

1. **Check the logs** for error messages
2. **Verify backend connectivity**
3. **Test with simple queries first**
4. **Check browser console for JavaScript errors**

---

**Built with ❤️ for oceanographic research and education**

*FloatChat Frontend - Making ocean data accessible to everyone, everywhere* 🌊
