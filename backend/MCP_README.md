# ARGO FloatChat MCP Server

## Overview

The ARGO FloatChat MCP (Model Context Protocol) Server provides intelligent access to oceanographic data through a standardized protocol. This server enhances your existing ARGO dataset with advanced query capabilities, analysis tools, and visualization suggestions.

## Features

### 🌊 **Intelligent Oceanographic Analysis**
- Natural language query processing
- Multilingual support (12 languages)
- Advanced data analysis and statistics
- Intelligent query translation

### 🛠️ **Available MCP Tools**

1. **`query_argo_database`** - Query ARGO data with natural language
2. **`analyze_ocean_conditions`** - Perform intelligent oceanographic analysis
3. **`find_float_trajectories`** - Find and analyze ARGO float trajectories
4. **`generate_ocean_visualization`** - Generate intelligent visualizations
5. **`get_database_statistics`** - Get comprehensive database statistics
6. **`translate_ocean_query`** - Translate queries between languages

### 📊 **Available MCP Resources**

1. **`argo://database/overview`** - Database structure and content overview
2. **`argo://coverage/indian-ocean`** - Geographic coverage information
3. **`argo://parameters/available`** - Available oceanographic parameters
4. **`argo://floats/active`** - Information about active ARGO floats

## Installation

### 1. Install MCP Dependencies

```bash
cd argo_floatchat-main/backend
pip install -r requirements_mcp.txt
```

### 2. Verify Installation

```bash
python start_mcp_server.py
```

## Usage

### Starting the MCP Server

```bash
# From the backend directory
python start_mcp_server.py
```

### Integration with AI Clients

The MCP server can be integrated with any MCP-compatible AI client. Add this configuration to your AI client:

```json
{
  "mcpServers": {
    "argo-floatchat": {
      "command": "python",
      "args": ["start_mcp_server.py"],
      "cwd": "/path/to/argo_floatchat-main/backend"
    }
  }
}
```

## Example Queries

### Natural Language Database Queries
```
"Show me temperature profiles in the Arabian Sea for the last month"
"Find floats near coordinates 20°N, 70°E"
"Compare salinity data between 2022 and 2023"
```

### Oceanographic Analysis
```
"Analyze temperature trends in the Bay of Bengal"
"Find anomalies in dissolved oxygen levels"
"Generate correlation analysis between temperature and salinity"
```

### Multilingual Queries
```
"बंगाल की खाड़ी में तापमान डेटा दिखाएं" (Hindi)
"Montrez-moi les données de salinité dans l'océan Indien" (French)
"Mostrar datos de temperatura en el Mar Arábigo" (Spanish)
```

## Data Scope

### ✅ **What's Available**
- **Geographic Coverage**: Indian Ocean region (20°E to 160°E, -60°S to 27°N)
- **Parameters**: Temperature, Salinity, Pressure, BGC parameters
- **Time Range**: All available ARGO float data
- **Languages**: 12 supported languages with intelligent translation

### ❌ **What's NOT Available**
- External ocean data sources
- Real-time satellite data
- Weather information
- Data from other ocean basins (Atlantic, Pacific, Arctic)

## Advanced Features

### 1. **Intelligent Query Understanding**
The MCP server uses your existing RAG pipeline to understand complex oceanographic queries and provide contextual responses.

### 2. **Dynamic Analysis Tools**
Create custom analysis workflows on-the-fly based on user queries:
- Statistical analysis
- Trend detection
- Anomaly identification
- Correlation analysis

### 3. **Enhanced Visualizations**
Generate intelligent visualization suggestions:
- Geographic maps
- Time series plots
- Profile visualizations
- 3D surface plots

### 4. **Multilingual Intelligence**
- Automatic query translation
- Context-aware responses
- Scientific terminology preservation

## Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://jayansh:123456@localhost:5432/argo_db
OPENAI_API_KEY=your_openai_api_key
LOG_LEVEL=INFO
```

### MCP Configuration
Edit `mcp_config.json` to customize server behavior:

```json
{
  "capabilities": {
    "tools": true,
    "resources": true,
    "prompts": false
  },
  "supportedLanguages": [
    "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "ar", "hi"
  ]
}
```

## Troubleshooting

### Common Issues

1. **MCP Package Not Found**
   ```bash
   pip install mcp>=1.0.0
   ```

2. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in environment variables

3. **Service Initialization Failed**
   - Ensure all ARGO services are properly installed
   - Check log files for specific error messages

### Logs
- Server logs: `mcp_server.log`
- Application logs: Check console output

## Development

### Adding New Tools
1. Add tool definition in `handle_list_tools()`
2. Implement tool handler in `handle_call_tool()`
3. Add tool-specific method in `ARGOMCPServer` class

### Adding New Resources
1. Add resource definition in `handle_list_resources()`
2. Implement resource handler in `handle_read_resource()`
3. Add resource-specific method in `ARGOMCPServer` class

## Benefits of MCP Integration

### 🚀 **Enhanced Intelligence**
- Better query understanding
- Contextual responses
- Dynamic tool creation

### 🌍 **Multilingual Support**
- 12 language support
- Intelligent translation
- Scientific terminology preservation

### 📈 **Advanced Analysis**
- Statistical analysis
- Trend detection
- Anomaly identification
- Correlation analysis

### 🎯 **Focused Scope**
- No external data dependencies
- Reliable responses based on your dataset
- Consistent performance

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify all dependencies are installed
3. Ensure database connectivity
4. Test with simple queries first

---

**Note**: This MCP server is designed to work exclusively with your existing ARGO dataset. It will not provide external data but will make your existing data much more intelligent and accessible through natural language queries and advanced analysis tools.
