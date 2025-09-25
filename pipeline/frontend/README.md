# ARGO FloatChat Frontend

Streamlit-based frontend application for the ARGO FloatChat oceanographic data analysis platform.

## 🎨 Features

- **Interactive UI**: User-friendly interface for querying oceanographic data
- **Real-time Visualization**: Dynamic maps and charts using Plotly
- **Query History**: Track and revisit previous queries
- **Responsive Design**: Optimized for various screen sizes
- **Error Handling**: Comprehensive error display and recovery

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   streamlit run floatchat_app.py --server.port 8501
   ```

3. **Access the UI**
   Open http://localhost:8501 in your browser

## 📁 Structure

- `floatchat_app.py` - Main Streamlit application
- `backend_adapter.py` - API communication layer
- `frontend_config.py` - Configuration management
- `static/` - Static assets

## 🔧 Configuration

The frontend connects to the backend API at `http://localhost:8000` by default.

## 🎨 UI Components

- **Query Input**: Natural language query interface
- **Results Display**: Formatted data presentation
- **Visualizations**: Interactive maps and charts
- **Query History**: Previous queries sidebar
- **Error Messages**: User-friendly error display
