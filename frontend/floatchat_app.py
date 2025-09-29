# #!/usr/bin/env python3
# """
# floatchat_app.py
# FloatChat - AI-Powered ARGO Ocean Data Discovery & Visualization
# Complete frontend application with backend integration
# """

# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import requests
# import json
# import datetime
# from datetime import date, timedelta
# import time
# import os
# import logging
# from typing import Dict, List, Any, Optional
# import sys
# from pathlib import Path

# # Import custom modules
# from frontend_config import FrontendConfig
# from backend_adapter import BackendAdapter

# # Configure logging
# logging.basicConfig(
#     level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('logs/frontend.log'),
#         logging.StreamHandler(sys.stdout)
#     ] if os.path.exists('logs') else [logging.StreamHandler(sys.stdout)]
# )
# logger = logging.getLogger(__name__)

# # Page configuration
# st.set_page_config(
#     page_title=FrontendConfig.PAGE_TITLE,
#     page_icon=FrontendConfig.PAGE_ICON,
#     layout=FrontendConfig.LAYOUT,
#     initial_sidebar_state="expanded"
# )

# # Enhanced CSS styling
# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
#     :root {
#         --primary-blue: #06b6d4;
#         --primary-indigo: #3b82f6;
#         --primary-purple: #8b5cf6;
#         --success-green: #10b981;
#         --error-red: #ef4444;
#         --warning-orange: #f97316;
#         --dark-bg: #0f172a;
#         --dark-surface: #1e293b;
#         --glass-bg: rgba(255, 255, 255, 0.05);
#         --glass-border: rgba(255, 255, 255, 0.1);
#     }
    
#     * {
#         font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
#     }
    
#     .main {
#         background: linear-gradient(135deg, var(--dark-bg) 0%, var(--dark-surface) 50%, #334155 100%);
#         background-attachment: fixed;
#     }
    
#     /* Header styling */
#     .header-container {
#         background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-indigo) 50%, var(--primary-purple) 100%);
#         padding: 3rem 2rem;
#         border-radius: 24px;
#         margin-bottom: 2rem;
#         box-shadow: 0 20px 40px rgba(0,0,0,0.2), 0 0 0 1px rgba(255,255,255,0.1);
#         text-align: center;
#         position: relative;
#         overflow: hidden;
#     }
    
#     .header-title {
#         color: white;
#         font-size: 3.5rem;
#         font-weight: 800;
#         margin: 0;
#         text-shadow: 0 4px 8px rgba(0,0,0,0.3);
#         letter-spacing: -0.02em;
#     }
    
#     .header-subtitle {
#         color: rgba(255,255,255,0.9);
#         font-size: 1.3rem;
#         margin-top: 1rem;
#         font-weight: 400;
#         text-shadow: 0 2px 4px rgba(0,0,0,0.2);
#     }
    
#     /* Chat messages */
#     .user-message {
#         background: linear-gradient(135deg, var(--primary-indigo) 0%, #1d4ed8 100%);
#         color: white;
#         padding: 1.5rem 2rem;
#         border-radius: 24px 24px 8px 24px;
#         margin: 1rem 0 1rem auto;
#         max-width: 80%;
#         box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
#         animation: slideInRight 0.3s ease-out;
#     }
    
#     .assistant-message {
#         background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
#         color: white;
#         padding: 1.5rem 2rem;
#         border-radius: 24px 24px 24px 8px;
#         margin: 1rem 0;
#         max-width: 85%;
#         box-shadow: 0 8px 25px rgba(55, 65, 81, 0.3);
#         border: 1px solid rgba(255,255,255,0.1);
#         animation: slideInLeft 0.3s ease-out;
#     }
    
#     @keyframes slideInRight {
#         from { transform: translateX(50px); opacity: 0; }
#         to { transform: translateX(0); opacity: 1; }
#     }
    
#     @keyframes slideInLeft {
#         from { transform: translateX(-50px); opacity: 0; }
#         to { transform: translateX(0); opacity: 1; }
#     }
    
#     /* Glass containers */
#     .glass-container {
#         background: var(--glass-bg);
#         backdrop-filter: blur(20px);
#         border: 1px solid var(--glass-border);
#         border-radius: 20px;
#         padding: 2rem;
#         margin: 1rem 0;
#         box-shadow: 0 8px 32px rgba(0,0,0,0.2);
#     }
    
#     /* Metric cards */
#     .metric-card {
#         background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
#         border: 1px solid rgba(255,255,255,0.1);
#         padding: 1.5rem;
#         border-radius: 16px;
#         margin: 0.8rem 0;
#         backdrop-filter: blur(20px);
#         box-shadow: 0 8px 32px rgba(0,0,0,0.2);
#         transition: all 0.3s ease;
#         position: relative;
#         overflow: hidden;
#     }
    
#     .metric-card:hover {
#         transform: translateY(-2px);
#         box-shadow: 0 12px 40px rgba(0,0,0,0.3);
#         border-color: var(--primary-blue);
#     }
    
#     .metric-card::before {
#         content: '';
#         position: absolute;
#         top: 0;
#         left: 0;
#         right: 0;
#         height: 3px;
#         background: linear-gradient(90deg, var(--primary-blue), var(--primary-indigo), var(--primary-purple));
#     }
    
#     /* Status indicators */
#     .status-indicator {
#         display: inline-flex;
#         align-items: center;
#         gap: 0.5rem;
#         padding: 0.5rem 1rem;
#         border-radius: 12px;
#         font-weight: 600;
#         font-size: 0.9rem;
#     }
    
#     .status-online {
#         background: rgba(16, 185, 129, 0.2);
#         color: var(--success-green);
#         border: 1px solid rgba(16, 185, 129, 0.3);
#     }
    
#     .status-offline {
#         background: rgba(239, 68, 68, 0.2);
#         color: var(--error-red);
#         border: 1px solid rgba(239, 68, 68, 0.3);
#     }
    
#     .status-pulse {
#         animation: pulse 2s infinite;
#     }
    
#     @keyframes pulse {
#         0% { opacity: 1; }
#         50% { opacity: 0.7; }
#         100% { opacity: 1; }
#     }
    
#     /* Enhanced buttons */
#     .stButton > button {
#         background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-indigo) 100%);
#         color: white !important;
#         border: none;
#         border-radius: 16px;
#         padding: 1rem 2rem;
#         font-weight: 600;
#         transition: all 0.3s ease;
#         box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
#     }
    
#     .stButton > button:hover {
#         transform: translateY(-2px);
#         box-shadow: 0 8px 25px rgba(6, 182, 212, 0.4);
#     }
    
#     /* Input styling */
#     .stTextInput > div > div > input {
#         background: rgba(255, 255, 255, 0.08);
#         border: 2px solid rgba(255, 255, 255, 0.15);
#         border-radius: 16px;
#         color: white;
#         padding: 1rem 1.5rem;
#         backdrop-filter: blur(10px);
#         transition: all 0.3s ease;
#     }
    
#     .stTextInput > div > div > input:focus {
#         border-color: var(--primary-blue);
#         box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.2);
#         background: rgba(255, 255, 255, 0.12);
#     }
    
#     /* Loading animation */
#     .loading-container {
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         padding: 2rem;
#         gap: 1rem;
#     }
    
#     .loading-dots {
#         display: flex;
#         gap: 0.5rem;
#     }
    
#     .loading-dot {
#         width: 12px;
#         height: 12px;
#         border-radius: 50%;
#         background: var(--primary-blue);
#         animation: loadingBounce 1.4s infinite ease-in-out both;
#     }
    
#     .loading-dot:nth-child(1) { animation-delay: -0.32s; }
#     .loading-dot:nth-child(2) { animation-delay: -0.16s; }
#     .loading-dot:nth-child(3) { animation-delay: 0s; }
    
#     @keyframes loadingBounce {
#         0%, 80%, 100% {
#             transform: scale(0.8);
#             opacity: 0.5;
#         }
#         40% {
#             transform: scale(1.2);
#             opacity: 1;
#         }
#     }
# </style>
# """, unsafe_allow_html=True)

# # Initialize backend adapter
# @st.cache_resource
# def get_backend_adapter():
#     return BackendAdapter()

# backend_adapter = get_backend_adapter()

# # Session state initialization
# def init_session_state():
#     """Initialize session state with default values"""
#     defaults = {
#         "messages": [],
#         "query_history": [],
#         "current_data": None,
#         "current_query_id": None,
#         "backend_status": {"status": "checking", "last_check": None},
#         "current_filters": {},
#         "performance_metrics": {
#             "query_count": 0,
#             "avg_response_time": 0,
#             "last_query_time": None
#         }
#     }
    
#     for key, value in defaults.items():
#         if key not in st.session_state:
#             st.session_state[key] = value

# # UI Components
# def render_header():
#     """Render the main header with status"""
#     backend_status = st.session_state.backend_status
#     status_text = "🟢 Online" if backend_status.get("status") == "online" else "🔴 Offline"
#     status_class = "status-online" if backend_status.get("status") == "online" else "status-offline"
    
#     st.markdown(f"""
#         <div class="header-container">
#             <h1 class="header-title">🌊 FloatChat</h1>
#             <p class="header-subtitle">AI-Powered ARGO Ocean Data Discovery & Visualization</p>
#             <div style="margin-top: 1rem;">
#                 <span class="status-indicator {status_class} status-pulse">
#                     {status_text}
#                 </span>
#             </div>
#         </div>
#     """, unsafe_allow_html=True)

# def render_sidebar():
#     """Render enhanced sidebar with controls"""
#     with st.sidebar:
#         st.markdown("### 🎛️ Control Panel")
        
#         # Backend status check
#         if st.button("🔄 Refresh Status", use_container_width=True):
#             with st.spinner("Checking backend..."):
#                 status = backend_adapter.health_check()
#                 st.session_state.backend_status = {
#                     "status": "online" if status.get("backend_available") else "offline",
#                     "details": status,
#                     "last_check": datetime.datetime.now()
#                 }
#             st.rerun()
        
#         # Status display
#         status = st.session_state.backend_status
#         if status.get("last_check"):
#             last_check = status["last_check"].strftime("%H:%M:%S")
#             status_text = "🟢 Online" if status["status"] == "online" else "🔴 Offline"
#             st.markdown(f"""
#                 <div class="metric-card">
#                     <h4>Backend Status</h4>
#                     <p style="color: {'#10b981' if status['status'] == 'online' else '#ef4444'};">
#                         {status_text}
#                     </p>
#                     <small style="color: rgba(255,255,255,0.6);">Last check: {last_check}</small>
#                 </div>
#             """, unsafe_allow_html=True)
        
#         st.markdown("---")
        
#         # Query filters
#         st.markdown("### 📊 Query Filters")
        
#         # Date range
#         col1, col2 = st.columns(2)
#         with col1:
#             start_date = st.date_input(
#                 "Start Date",
#                 value=date.today() - timedelta(days=365),
#                 key="start_date"
#             )
#         with col2:
#             end_date = st.date_input(
#                 "End Date", 
#                 value=date.today(),
#                 key="end_date"
#             )
        
#         # Geographic region
#         st.markdown("### 🗺️ Geographic Region")
#         region_preset = st.selectbox(
#             "Quick Region",
#             ["Custom"] + list(FrontendConfig.REGIONS.keys()),
#             key="region_preset"
#         )
        
#         if region_preset != "Custom":
#             region = FrontendConfig.REGIONS[region_preset]
#             lat_range = region["lat"]
#             lon_range = region["lon"]
#         else:
#             lat_range = [-90, 90]
#             lon_range = [-180, 180]
        
#         lat_min, lat_max = st.slider(
#             "Latitude Range",
#             -90.0, 90.0,
#             (float(lat_range[0]), float(lat_range[1])),
#             key="lat_range"
#         )
        
#         lon_min, lon_max = st.slider(
#             "Longitude Range", 
#             -180.0, 180.0,
#             (float(lon_range[0]), float(lon_range[1])),
#             key="lon_range"
#         )
        
#         # Parameters
#         st.markdown("### 🌡️ Parameters")
#         parameters = st.multiselect(
#             "Select Parameters",
#             ["Temperature", "Salinity", "Pressure", "Oxygen", "Chlorophyll", "Nitrate", "pH"],
#             default=["Temperature", "Salinity"],
#             key="parameters"
#         )
        
#         # Data quality
#         st.markdown("### ✅ Data Quality")
#         min_quality = st.slider("Min Quality Flag", 1, 4, 1, key="min_quality")
#         exclude_bad_data = st.checkbox("Exclude flagged data", True, key="exclude_bad")
        
#         # Export
#         if st.session_state.current_data:
#             st.markdown("### 📥 Export")
#             export_format = st.selectbox(
#                 "Format",
#                 FrontendConfig.EXPORT_FORMATS,
#                 key="export_format"
#             )
            
#             if st.button("📊 Export Data", use_container_width=True):
#                 if st.session_state.current_query_id:
#                     with st.spinner("Preparing export..."):
#                         export_data = backend_adapter.export_query_results(
#                             st.session_state.current_query_id,
#                             export_format
#                         )
#                         if export_data:
#                             st.download_button(
#                                 "⬇️ Download",
#                                 export_data,
#                                 f"floatchat_export.{export_format}",
#                                 use_container_width=True
#                             )
#                         else:
#                             st.error("Export failed")
#                 else:
#                     st.warning("No data to export")
        
#         return {
#             "date_range": (start_date, end_date),
#             "geographic_bounds": (lat_min, lat_max, lon_min, lon_max),
#             "parameters": [p.lower() for p in parameters],
#             "quality_filters": {
#                 "min_quality": min_quality,
#                 "exclude_bad_data": exclude_bad_data
#             },
#             "region_preset": region_preset
#         }

# def render_chat_interface():
#     """Render the chat interface"""
#     st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
#     # Display messages
#     for message in st.session_state.messages:
#         if message["role"] == "user":
#             st.markdown(
#                 f'<div class="user-message">{message["content"]}</div>',
#                 unsafe_allow_html=True
#             )
#         else:
#             st.markdown(
#                 f'<div class="assistant-message">{message["content"]}</div>',
#                 unsafe_allow_html=True
#             )
            
#             # Show visualization if available
#             if "visualization" in message and message["visualization"]:
#                 st.plotly_chart(message["visualization"], use_container_width=True)
    
#     st.markdown('</div>', unsafe_allow_html=True)

# def render_quick_queries():
#     """Render quick query buttons"""
#     st.markdown("### 🚀 Quick Queries")
    
#     queries = FrontendConfig.QUICK_QUERIES[:6]  # Show first 6
    
#     cols = st.columns(2)
#     for i, query in enumerate(queries):
#         col = cols[i % 2]
#         with col:
#             if st.button(query, key=f"quick_{i}", use_container_width=True):
#                 handle_query(query)

# def render_loading_animation(message: str = "Processing..."):
#     """Render loading animation"""
#     return st.markdown(f"""
#         <div class="loading-container">
#             <div class="loading-dots">
#                 <div class="loading-dot"></div>
#                 <div class="loading-dot"></div>
#                 <div class="loading-dot"></div>
#             </div>
#             <span style="color: rgba(255,255,255,0.8); font-weight: 500;">
#                 {message}
#             </span>
#         </div>
#     """, unsafe_allow_html=True)

# # Visualization functions
# def create_visualization(viz_config: Dict) -> Optional[go.Figure]:
#     """Create visualization from backend configuration"""
#     try:
#         viz_type = viz_config.get("type", "scatter")
#         data = viz_config.get("data", [])
        
#         if not data:
#             return None
        
#         df = pd.DataFrame(data)
        
#         if viz_type == "map":
#             return create_map_visualization(df, viz_config)
#         elif viz_type == "profile":
#             return create_profile_visualization(df, viz_config)
#         elif viz_type == "timeseries":
#             return create_timeseries_visualization(df, viz_config)
#         else:
#             return create_scatter_visualization(df, viz_config)
    
#     except Exception as e:
#         logger.error(f"Visualization creation failed: {e}")
#         return None

# def create_map_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
#     """Create interactive map"""
#     fig = go.Figure()
    
#     if 'latitude' in df and 'longitude' in df:
#         color_param = config.get("color_by", "temperature")
        
#         if color_param in df.columns:
#             fig.add_trace(go.Scattermap(
#                 lat=df['latitude'],
#                 lon=df['longitude'],
#                 mode='markers',
#                 marker=dict(
#                     size=10,
#                     color=df[color_param],
#                     colorscale='RdYlBu_r',
#                     showscale=True,
#                     colorbar=dict(title=f"{color_param.title()}"),
#                     opacity=0.8
#                 ),
#                 text=df.get('float_id', ''),
#                 hovertemplate=(
#                     "<b>Float:</b> %{text}<br>" +
#                     "<b>Lat:</b> %{lat:.3f}°<br>" +
#                     "<b>Lon:</b> %{lon:.3f}°<br>" +
#                     f"<b>{color_param.title()}:</b> %{{marker.color:.2f}}<br>" +
#                     "<extra></extra>"
#                 ),
#                 name="ARGO Floats"
#             ))
    
#     center_lat = df['latitude'].mean() if 'latitude' in df else 0
#     center_lon = df['longitude'].mean() if 'longitude' in df else 0
    
#     fig.update_layout(
#         mapbox=dict(
#             style="open-street-map",
#             center=dict(lat=center_lat, lon=center_lon),
#             zoom=4
#         ),
#         height=600,
#         margin=dict(l=0, r=0, t=50, b=0),
#         paper_bgcolor='rgba(0,0,0,0)',
#         title=config.get("title", "ARGO Float Locations"),
#         font=dict(color='white')
#     )
    
#     return fig

# def create_profile_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
#     """Create depth profile"""
#     params = ['temperature', 'salinity', 'pressure', 'oxygen']
#     available_params = [p for p in params if p in df.columns]
    
#     if not available_params:
#         return None
    
#     n_params = min(len(available_params), 3)
#     fig = make_subplots(
#         rows=1, cols=n_params,
#         shared_yaxes=True,
#         subplot_titles=[p.title() for p in available_params[:n_params]]
#     )
    
#     depth_col = 'depth' if 'depth' in df else 'pressure'
#     colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
    
#     for i, param in enumerate(available_params[:n_params]):
#         sorted_df = df.sort_values(depth_col)
        
#         fig.add_trace(
#             go.Scatter(
#                 x=sorted_df[param],
#                 y=sorted_df[depth_col],
#                 mode='lines+markers',
#                 name=param.title(),
#                 line=dict(color=colors[i], width=3),
#                 marker=dict(size=6),
#                 showlegend=False
#             ),
#             row=1, col=i+1
#         )
        
#         fig.update_xaxes(title_text=param.title(), row=1, col=i+1)
    
#     fig.update_yaxes(
#         title_text="Depth (m)",
#         autorange='reversed',
#         row=1, col=1
#     )
    
#     fig.update_layout(
#         height=600,
#         paper_bgcolor='rgba(0,0,0,0)',
#         title=config.get("title", "Ocean Parameter Profiles"),
#         font=dict(color='white')
#     )
    
#     return fig

# def create_timeseries_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
#     """Create time series plot"""
#     if 'date' in df.columns:
#         df['datetime'] = pd.to_datetime(df['date'])
#     else:
#         return None
    
#     numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
#     params = [col for col in numeric_cols if col not in ['depth', 'pressure', 'latitude', 'longitude']]
    
#     if not params:
#         return None
    
#     fig = go.Figure()
#     colors = FrontendConfig.COLOR_PALETTE
    
#     for i, param in enumerate(params[:3]):  # Limit to 3 parameters
#         fig.add_trace(go.Scatter(
#             x=df['datetime'],
#             y=df[param],
#             mode='lines+markers',
#             name=param.title(),
#             line=dict(color=colors[i % len(colors)], width=2),
#             marker=dict(size=4)
#         ))
    
#     fig.update_layout(
#         title=config.get("title", "Parameter Time Series"),
#         xaxis_title="Date",
#         yaxis_title="Value",
#         height=500,
#         paper_bgcolor='rgba(0,0,0,0)',
#         font=dict(color='white')
#     )
    
#     return fig

# def create_scatter_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
#     """Create scatter plot"""
#     x_col = df.columns[0] if len(df.columns) > 0 else 'x'
#     y_col = df.columns[1] if len(df.columns) > 1 else 'y'
    
#     fig = px.scatter(
#         df, x=x_col, y=y_col,
#         title=config.get("title", f"{x_col.title()} vs {y_col.title()}"),
#         color=df.columns[2] if len(df.columns) > 2 else None
#     )
    
#     fig.update_layout(
#         paper_bgcolor='rgba(0,0,0,0)',
#         font=dict(color='white'),
#         height=500
#     )
    
#     return fig

# # Query handling
# def handle_query(query: str):
#     """Handle user query"""
#     start_time = time.time()
    
#     # Add user message
#     st.session_state.messages.append({
#         "role": "user",
#         "content": query,
#         "timestamp": datetime.datetime.now()
#     })
    
#     # Show loading
#     loading_placeholder = st.empty()
#     with loading_placeholder:
#         render_loading_animation("🤔 Processing your query...")
    
#     try:
#         # Get current filters
#         filters = st.session_state.get("current_filters", {})
        
#         # Process query
#         with loading_placeholder:
#             render_loading_animation("🔍 Searching ocean data...")
        
#         # Try backend first
#         result = backend_adapter.process_natural_language_query(query, filters)
        
#         # Debug: Print result to identify the issue
#         print(f"DEBUG - Result type: {type(result)}")
#         print(f"DEBUG - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
#         print(f"DEBUG - Success value: {result.get('success') if isinstance(result, dict) else 'N/A'}")
        
#         # If backend fails, generate mock data for demonstration
#         if not result.get("success"):
#             logger.info("Backend query failed, generating mock data")
#             result = backend_adapter.generate_mock_data(query)
        
#         # Clear loading
#         loading_placeholder.empty()
        
#         # Calculate response time
#         response_time = time.time() - start_time
        
#         # Update performance metrics
#         metrics = st.session_state.performance_metrics
#         metrics["query_count"] += 1
#         metrics["avg_response_time"] = (
#             (metrics["avg_response_time"] * (metrics["query_count"] - 1) + response_time) /
#             metrics["query_count"]
#         )
#         metrics["last_query_time"] = response_time
        
#         if result.get("success"):
#             # Get response content - handle both "response" and "answer" keys
#             response_content = result.get("response") or result.get("answer") or "Query processed successfully"
            
#             # Create assistant message
#             message_data = {
#                 "role": "assistant",
#                 "content": response_content,
#                 "timestamp": datetime.datetime.now(),
#                 "response_time": response_time
#             }
            
#             # Add visualization if available - handle both "visualization" and "visualizations"
#             viz_data = result.get("visualization") or result.get("visualizations")
#             if viz_data:
#                 # If visualizations is a list, take the first one
#                 if isinstance(viz_data, list) and viz_data:
#                     viz_config = {
#                         "type": viz_data[0].get("type", "map"),
#                         "data": result.get("data", {}).get("records", []),
#                         "title": viz_data[0].get("title", "ARGO Data Visualization"),
#                         "color_by": viz_data[0].get("config", {}).get("color_by", "temperature")
#                     }
#                 else:
#                     viz_config = viz_data
                
#                 viz_fig = create_visualization(viz_config)
#                 if viz_fig:
#                     message_data["visualization"] = viz_fig
            
#             # Store data for export
#             if "data" in result:
#                 st.session_state.current_data = result["data"]
#                 st.session_state.current_query_id = result.get("query_id") or result.get("response_id")
            
#             st.session_state.messages.append(message_data)
            
#             # Show success notification
#             success_msg = f"✅ Query processed in {response_time:.1f}s"
#             if result.get("is_mock"):
#                 success_msg += " (Demo data - connect backend for real data)"
#             st.success(success_msg)
        
#         else:
#             # Handle error - be more careful about accessing the response
#             error_content = result.get("response") or result.get("error") or "Unknown error occurred"
#             error_message = {
#                 "role": "assistant",
#                 "content": error_content,
#                 "error": True,
#                 "timestamp": datetime.datetime.now()
#             }
#             st.session_state.messages.append(error_message)
#             st.error("❌ Query failed")
    
#     except Exception as e:
#         loading_placeholder.empty()
#         logger.error(f"Query handling failed: {e}")
        
#         error_message = {
#             "role": "assistant", 
#             "content": f"I apologize, but I encountered an unexpected error: {str(e)}",
#             "error": True,
#             "timestamp": datetime.datetime.now()
#         }
#         st.session_state.messages.append(error_message)
#         st.error(f"❌ Unexpected error: {str(e)}")
    
#     # Rerun to update UI
#     st.rerun()

# # Main application
# def main():
#     """Main application function"""
#     # Initialize session state
#     init_session_state()
    
#     # Periodic backend status check
#     current_time = datetime.datetime.now()
#     last_check = st.session_state.backend_status.get("last_check")
    
#     if (not last_check or 
#         (current_time - last_check).seconds > 60):
#         status = backend_adapter.health_check()
#         st.session_state.backend_status = {
#             "status": "online" if status.get("backend_available") else "offline",
#             "details": status,
#             "last_check": current_time
#         }
    
#     # Render UI
#     render_header()
    
#     # Sidebar
#     current_filters = render_sidebar()
#     st.session_state.current_filters = current_filters
    
#     # Main content
#     col1, col2 = st.columns([2.5, 1.5])
    
#     with col1:
#         # Chat interface
#         st.markdown("### 💬 Chat with FloatChat")
#         render_chat_interface()
        
#         # Query input
#         st.markdown("### 🎯 Ask Your Question")
        
#         # Show example queries for new users
#         if not st.session_state.messages:
#             st.markdown("""
#                 <div style="background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.3); 
#                            border-radius: 12px; padding: 1rem; margin: 1rem 0;">
#                     <h4 style="color: #06b6d4; margin: 0 0 0.5rem 0;">💡 Try asking:</h4>
#                     <ul style="margin: 0; color: rgba(255,255,255,0.8);">
#                         <li>"Show me temperature profiles in the Indian Ocean"</li>
#                         <li>"Compare salinity data in the Arabian Sea vs Bay of Bengal"</li>
#                         <li>"Find ARGO floats near coordinates 20°N, 70°E"</li>
#                         <li>"What are the oxygen levels in the equatorial Pacific?"</li>
#                     </ul>
#                 </div>
#             """, unsafe_allow_html=True)
        
#         # Query input
#         query = st.text_input(
#             "",  # Empty label causing warning
#             placeholder="Type your ocean data query here...",
#             key="query_input",
#             label_visibility="collapsed"
#         )
        
#         # Action buttons
#         col_send, col_clear = st.columns([3, 1])
        
#         with col_send:
#             if st.button("🚀 Send Query", type="primary", use_container_width=True):
#                 if query.strip():
#                     handle_query(query)
#                     st.session_state.query_input = ""
#                     st.rerun()
        
#         with col_clear:
#             if st.button("🗑️ Clear", use_container_width=True):
#                 st.session_state.messages = []
#                 st.session_state.current_data = None
#                 st.rerun()
    
#     with col2:
#         # Quick queries
#         render_quick_queries()
        
#         # Current data stats
#         if st.session_state.current_data:
#             st.markdown("### 📈 Current Dataset")
            
#             data_records = st.session_state.current_data.get("records", [])
#             if data_records:
#                 df = pd.DataFrame(data_records)
                
#                 st.markdown(f"""
#                     <div class="metric-card">
#                         <h4>Dataset Overview</h4>
#                         <p><strong>Records:</strong> {len(df):,}</p>
#                         <p><strong>Parameters:</strong> {len(df.select_dtypes(include=[np.number]).columns)}</p>
#                         <p><strong>Floats:</strong> {df.get('float_id', pd.Series()).nunique()}</p>
#                     </div>
#                 """, unsafe_allow_html=True)
        
#         # Performance metrics
#         if st.session_state.performance_metrics["query_count"] > 0:
#             metrics = st.session_state.performance_metrics
#             st.markdown("### ⚡ Performance")
            
#             st.markdown(f"""
#                 <div class="metric-card">
#                     <p><strong>Queries:</strong> {metrics['query_count']}</p>
#                     <p><strong>Avg Response:</strong> {metrics['avg_response_time']:.1f}s</p>
#                 </div>
#             """, unsafe_allow_html=True)
    
#     # Footer
#     st.markdown("---")
#     st.markdown(f"""
#         <div style="text-align: center; color: rgba(255,255,255,0.6); padding: 2rem;">
#             <p>🌊 <strong>FloatChat</strong> - Democratizing Ocean Data Access through AI</p>
#             <p>Backend: {'🟢 Connected' if st.session_state.backend_status['status'] == 'online' else '🔴 Disconnected'} | 
#                Session: {len(st.session_state.messages)} messages</p>
#         </div>
#     """, unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
"""
floatchat_app.py
FloatChat - AI-Powered ARGO Ocean Data Discovery & Visualization
Complete frontend application with backend integration
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import datetime
from datetime import date, timedelta
import time
import os
import logging
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Import custom modules
from frontend_config import FrontendConfig
from backend_adapter import BackendAdapter

# Visualization Configuration
class VisualizationConfig:
    """Configuration for visualization behavior"""
    MAX_VISUALIZATIONS = 2  # Maximum number of visualizations to generate
    MAX_PER_TYPE_MIXED = 1  # Maximum per type for mixed requests
    MIXED_KEYWORDS = ["both", "and", "also", "plus", "along with", "together with"]
    DATA_TABLE_KEYWORDS = ["data table", "table", "tabular", "statistics", "summary"]
    BAR_CHART_KEYWORDS = ["bar chart", "bar graph", "chart", "graph", "compare", "comparison"]

# Initialize i18n system first
try:
    from i18n import i18n
    from multilingual_components import (
        language_selector, render_header as render_multilingual_header,
        render_quick_queries as render_multilingual_queries,
        render_data_statistics,
        render_status_indicator, render_error_message, render_loading_message
    )
    MULTILINGUAL_AVAILABLE = True
    print("✅ Multilingual system loaded successfully")
    
    # Initialize with default language
    i18n.set_language('en')
    
except ImportError as e:
    print(f"⚠️ Multilingual system not available: {e}")
    MULTILINGUAL_AVAILABLE = False
    
    # Fallback functions
    class FallbackI18n:
        def t(self, key):
            return key
        def set_language(self, lang):
            pass
        def get_language(self):
            return "en"
    
    i18n = FallbackI18n()
    
    def language_selector():
        return "en"
    
    def render_multilingual_header():
        st.markdown("# 🌊 FloatChat")
        st.markdown("AI-Powered ARGO Ocean Data Discovery & Visualization")
    
    def render_multilingual_queries():
        st.markdown("### 🚀 Quick Queries")
        queries = [
            "Show me temperature profiles in the Indian Ocean for the last month",
            "Compare salinity data near the equator between 2022 and 2023",
            "Find the nearest ARGO floats to coordinates 20°N, 70°E",
            "Display BGC oxygen levels in the Arabian Sea",
            "Show float trajectories in the Bay of Bengal",
            "What's the temperature anomaly in the equatorial Pacific?"
        ]
        cols = st.columns(2)
        for i, query in enumerate(queries):
            with cols[i % 2]:
                if st.button(query, key=f"quick_{i}"):
                    return query
        return None

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/frontend.log'),
        logging.StreamHandler(sys.stdout)
    ] if os.path.exists('logs') else [logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=FrontendConfig.PAGE_TITLE,
    page_icon=FrontendConfig.PAGE_ICON,
    layout=FrontendConfig.LAYOUT,
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --primary-blue: #06b6d4;
        --primary-indigo: #3b82f6;
        --primary-purple: #8b5cf6;
        --success-green: #10b981;
        --error-red: #ef4444;
        --warning-orange: #f97316;
        --dark-bg: #0f172a;
        --dark-surface: #1e293b;
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        /* Restore previous gradient background */
        background: linear-gradient(135deg, var(--dark-bg) 0%, var(--dark-surface) 50%, #334155 100%);
        background-attachment: fixed;
    }
    
    /* Main content area styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Chat container styling */
    .chat-container {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* Empty state styling */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 2rem 0;
    }
    
    /* Header styling */
    .header-container {
        /* Restore ocean gradient header */
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 55%, #7c3aed 100%);
        padding: 0.75rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        box-shadow: 0 6px 16px rgba(0,0,0,0.18), 0 0 0 1px rgba(255,255,255,0.06);
        text-align: center;
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }
    
    .header-title {
        color: white;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.35);
        letter-spacing: -0.01em;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.85);
        font-size: 0.9rem;
        margin-top: 0.25rem;
        font-weight: 500;
        text-shadow: none;
    }
    
    /* Chat messages */
    .user-message {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 20px 20px 8px 20px;
        margin: 1rem 0 1rem auto;
        max-width: 80%;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        animation: slideInRight 0.3s ease-out;
        position: relative;
    }
    
    .user-message::before {
        content: '👤';
        position: absolute;
        top: -12px;
        right: 20px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 6px 10px;
        border-radius: 50%;
        font-size: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        max-width: 90%;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(59, 130, 246, 0.2);
        border: 2px solid rgba(59, 130, 246, 0.3);
        animation: slideInLeft 0.4s ease-out;
        position: relative;
        backdrop-filter: blur(10px);
    }
    
    .assistant-message::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #06b6d4, #3b82f6, #8b5cf6);
        border-radius: 20px 20px 0 0;
    }
    
    .assistant-message::after {
        content: '🤖';
        position: absolute;
        top: -15px;
        left: 20px;
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 8px 12px;
        border-radius: 50%;
        font-size: 1.2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border: 2px solid rgba(59, 130, 246, 0.3);
    }
    
    /* Enhanced content styling within assistant messages */
    .assistant-message h1, .assistant-message h2, .assistant-message h3 {
        color: #06b6d4 !important;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .assistant-message h1 {
        font-size: 1.5rem;
        font-weight: 700;
        border-bottom: 2px solid rgba(6, 182, 212, 0.3);
        padding-bottom: 0.5rem;
    }
    
    .assistant-message h2 {
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    .assistant-message h3 {
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .assistant-message p {
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .assistant-message strong {
        color: #10b981;
        font-weight: 600;
    }
    
    .assistant-message code {
        background: rgba(0, 0, 0, 0.3);
        color: #fbbf24;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
    }
    
    .assistant-message ul, .assistant-message ol {
        margin-left: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .assistant-message li {
        margin-bottom: 0.5rem;
        line-height: 1.5;
    }
    
    /* Special styling for data tables and visualizations */
    .assistant-message .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        margin: 1rem 0;
    }
    
    .assistant-message .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        margin: 1rem 0;
    }
    
    @keyframes slideInRight {
        from { transform: translateX(50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Glass containers */
    .glass-container {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 1.5rem;
        border-radius: 16px;
        margin: 0.8rem 0;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
        border-color: var(--primary-blue);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-indigo), var(--primary-purple));
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .status-online {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-green);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-offline {
        background: rgba(239, 68, 68, 0.2);
        color: var(--error-red);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .status-pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Enhanced buttons - default to Quick Queries card style */
    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 50%, #1d4ed8 100%);
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 0.75rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 8px 20px rgba(2, 132, 199, 0.3);
        text-align: center;
        width: 100%;
        min-height: 100px;
        line-height: 1.3;
        font-size: 0.8rem;
        white-space: normal;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 28px rgba(2, 132, 199, 0.45);
        border-color: rgba(255,255,255,0.2);
    }

    /* Sidebar buttons remain neutral */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.04);
        color: rgba(255,255,255,0.96) !important;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 0.7rem 1rem;
        box-shadow: none;
        text-align: left;
        min-height: auto;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.25);
    }

    /* Clear chat button styling */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
        color: white !important;
        border: 1px solid rgba(14, 165, 233, 0.3) !important;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
        text-align: center;
        min-height: auto;
        width: 100%;
        margin-bottom: 1rem;
    }
    
    .stButton > button[kind="secondary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(14, 165, 233, 0.4);
        border-color: rgba(14, 165, 233, 0.5) !important;
    }

    /* Section headers */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: rgba(255,255,255,0.95);
        margin: 0 0 0.15rem 0;
    }
    .section-subtitle {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.6);
        margin: 0 0 0.6rem 0;
    }
    .section-divider {
        height: 1px;
        width: 100%;
        background: rgba(255,255,255,0.08);
        margin: 0.25rem 0 0.75rem 0;
        border-radius: 1px;
    }

    /* Remove scoped QQ styles (global rules above handle it) */
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.08);
        border: 2px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        color: white;
        padding: 1rem 1.5rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-blue);
        box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.2);
        background: rgba(255, 255, 255, 0.12);
    }
    
    /* Loading animation */
    .loading-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        gap: 1rem;
    }

    /* Big hero prompt */
    .hero-prompt {
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 3rem 0 1rem 0;
    }
    .hero-title {
        font-size: 2.25rem;
        font-weight: 700;
        color: rgba(255,255,255,0.95);
        letter-spacing: -0.02em;
        margin: 0;
    }

    /* Make chat input more prominent */
    .stChatInput textarea, .stChatInput input {
        font-size: 1.05rem !important;
        padding: 1rem 1.25rem !important;
        border-radius: 14px !important;
    }
    .stChatInput button {
        margin-top: 0 !important;
        align-self: center !important;
    }
    
    .loading-dots {
        display: flex;
        gap: 0.5rem;
    }
    
    .loading-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: var(--primary-blue);
        animation: loadingBounce 1.4s infinite ease-in-out both;
    }
    
    .loading-dot:nth-child(1) { animation-delay: -0.32s; }
    .loading-dot:nth-child(2) { animation-delay: -0.16s; }
    .loading-dot:nth-child(3) { animation-delay: 0s; }
    
    @keyframes loadingBounce {
        0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% {
            transform: scale(1.2);
            opacity: 1;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize backend adapter
@st.cache_resource
def get_backend_adapter():
    return BackendAdapter()

backend_adapter = get_backend_adapter()

# Session state initialization
def init_session_state():
    """Initialize session state with default values"""
    defaults = {
        "messages": [],
        "query_history": [],
        "recent_queries": [],
        "current_data": None,
        "current_query": None,
        "current_query_id": None,
        "backend_status": {"status": "checking", "last_check": None},
        "current_filters": {},
        "performance_metrics": {
            "query_count": 0,
            "avg_response_time": 0,
            "last_query_time": None
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    # Default language
    if 'language' not in st.session_state:
        st.session_state['language'] = os.getenv('DEFAULT_LANGUAGE', 'en')
        if MULTILINGUAL_AVAILABLE:
            i18n.set_language(st.session_state['language'])

# UI Components
def render_header():
    """Render the main header with status"""
    backend_status = st.session_state.backend_status
    status_text = "Online" if backend_status.get("status") == "online" else "Offline"
    status_class = "status-online" if backend_status.get("status") == "online" else "status-offline"
    
    st.markdown(f"""
        <div class="header-container">
            <h1 class="header-title">🌊 FloatChat</h1>
            <p class="header-subtitle">AI-Powered ARGO Ocean Data Discovery & Visualization</p>
            <div style="margin-top: 1rem;">
                <span class="status-indicator {status_class} status-pulse">
                    {status_text}
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render enhanced sidebar with controls"""
    with st.sidebar:
        # Language selector
        if MULTILINGUAL_AVAILABLE:
            selected_language = language_selector()
            current_language = st.session_state.get('language', 'en')
            if selected_language != current_language:
                st.session_state['language'] = selected_language
                i18n.set_language(selected_language)
                # Don't call st.rerun() here to prevent reload loop
            
            st.markdown("### " + i18n.t("sidebar.data_statistics"))
        else:
            st.markdown("### Data Statistics")
        
        # Backend status check
        button_text = "Refresh Status"
        if st.button(button_text, use_container_width=True):
            with st.spinner("Checking backend..."):
                status = backend_adapter.health_check()
                st.session_state.backend_status = {
                    "status": "online" if status.get("backend_available") else "offline",
                    "details": status,
                    "last_check": datetime.datetime.now()
                }
            st.rerun()
        
        # Status display
        status = st.session_state.backend_status
        if status.get("last_check"):
            last_check = status["last_check"].strftime("%H:%M:%S")
            status_text = "Online" if status["status"] == "online" else "Offline"
            st.markdown(f"""
                <div class="metric-card">
                    <h4>Backend Status</h4>
                    <p style="color: {'#10b981' if status['status'] == 'online' else '#ef4444'};">
                        {status_text}
                    </p>
                    <small style="color: rgba(255,255,255,0.6);">Last check: {last_check}</small>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Export
        if st.session_state.current_data:
            st.markdown("### Export")
            export_format = st.selectbox(
                "Format",
                FrontendConfig.EXPORT_FORMATS,
                key="export_format"
            )
            
            if st.button("Export Data", use_container_width=True):
                if st.session_state.current_query:
                    with st.spinner("Preparing export..."):
                        try:
                            # Use the new export API
                            export_result = backend_adapter.export_data(
                                query=st.session_state.current_query,
                                export_format=export_format
                            )
                            
                            if export_result and export_result.get("export_id"):
                                # Get the actual file content
                                export_id = export_result["export_id"]
                                file_content = backend_adapter.download_export(export_id, export_format)
                                
                                if file_content:
                                    # Create download button with actual file content
                                    mime_types = {
                                        "csv": "text/csv",
                                        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        "json": "application/json",
                                        "png": "image/png",
                                        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    }
                                    
                                    st.download_button(
                                        "Download",
                                        data=file_content,
                                        file_name=f"floatchat_export.{export_format}",
                                        mime=mime_types.get(export_format, "application/octet-stream"),
                                        use_container_width=True
                                    )
                                    
                                    st.success(f"Export ready! {export_result.get('record_count', 0)} records exported.")
                                else:
                                    st.error("Failed to download export file")
                            else:
                                st.error("Export failed - no export ID returned")
                                
                        except Exception as e:
                            st.error(f"Export failed: {str(e)}")
                else:
                    st.warning("No query to export")
        
        return {}

def render_recent_queries():
    """Render recent queries in the sidebar"""
    recent_queries = st.session_state.get("recent_queries", [])
    
    if not recent_queries:
        return None
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔄 Recent Queries")
        
        # Show last 10 queries (most recent first)
        for i, query in enumerate(recent_queries[-10:][::-1]):
            # Truncate long queries for display
            display_query = query[:60] + "..." if len(query) > 60 else query
            
            if st.button(
                f"🔍 {display_query}",
                key=f"recent_query_{i}",
                use_container_width=True,
                help=f"Click to repeat: {query}"
            ):
                # Set the query in the chat input
                st.session_state.current_query = query
                st.rerun()
        
        # Clear recent queries button
        if st.button("🗑️ Clear Recent", use_container_width=True, key="clear_recent_queries"):
            st.session_state.recent_queries = []
            st.rerun()

def render_chat_interface():
    """Render the chat interface - completely clean version"""
    # Only render if there are messages
    if not st.session_state.messages:
        return
    
    # No chat container wrapper - just render messages directly
    for message in st.session_state.messages:
        role = "user" if message.get("role") == "user" else "assistant"
        
        # Use custom styling for messages
        if role == "user":
            # Escape HTML in user messages
            content = str(message.get("content", "")).replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(f"""
            <div class="user-message">
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Escape HTML in assistant messages - ULTRA aggressive sanitization
            content = str(message.get("content", ""))
            # Remove ALL HTML tags completely - multiple passes to be sure
            import re
            content = re.sub(r'<[^>]*>', '', content)  # Remove any HTML tags
            content = re.sub(r'</div>', '', content)   # Specifically remove </div> tags
            content = re.sub(r'<div[^>]*>', '', content)  # Remove opening div tags too
            content = re.sub(r'<[^>]+>', '', content)  # Final pass to catch anything else
            # Escape any remaining HTML entities
            content = content.replace("<", "&lt;").replace(">", "&gt;")
            # Clean up any extra whitespace
            content = content.strip()
            st.markdown(f"""
            <div class="assistant-message">
                {content}
            </div>
            """, unsafe_allow_html=True)
            
            # Render different visualization types
            if message.get("visualization") is not None:
                st.plotly_chart(message["visualization"], use_container_width=True, key=f"viz_{message.get('timestamp', 'unknown')}")
            
            if message.get("interactive_map") is not None:
                st.plotly_chart(message["interactive_map"], use_container_width=True, key=f"map_{message.get('timestamp', 'unknown')}")
            
            if message.get("bar_chart") is not None:
                st.markdown("#### 📊 Bar Chart Analysis")
                st.plotly_chart(message["bar_chart"], use_container_width=True, key=f"bar_chart_{message.get('timestamp', 'unknown')}")
            
            if message.get("data_table") is not None:
                st.markdown("#### 📋 Data Table")
                st.plotly_chart(message["data_table"], use_container_width=True, key=f"table_{message.get('timestamp', 'unknown')}")

def render_quick_queries():
    """Render professional quick query cards in a responsive grid"""
    st.markdown('<div class="section-title">Quick queries</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Frequently used prompts</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    queries = FrontendConfig.QUICK_QUERIES[:6]

    # 2-column layout for a more balanced look
    cols = st.columns(2)
    for i, query in enumerate(queries):
        col = cols[i % 2]
        with col:
            # Left-aligned neutral card-style buttons
            if st.button(query, key=f"quick_{i}"):
                handle_query(query)

def render_loading_animation(message: str = "Processing..."):
    """Render loading animation"""
    st.markdown(f"""
        <div class="loading-container">
            <div class="loading-dots">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
            <span style="color: rgba(255,255,255,0.8); font-weight: 500;">
                {message}
            </span>
        </div>
    """, unsafe_allow_html=True)

# Visualization functions
def create_visualization(viz_config: Dict) -> Optional[go.Figure]:
    """Create visualization from backend configuration"""
    try:
        viz_type = viz_config.get("type", "scatter")
        data = viz_config.get("data", [])
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        if viz_type == "map":
            return create_map_visualization(df, viz_config)
        elif viz_type == "profile":
            return create_profile_visualization(df, viz_config)
        elif viz_type == "timeseries":
            return create_timeseries_visualization(df, viz_config)
        elif viz_type == "bar_chart":
            return create_bar_chart_visualization(df, viz_config)
        elif viz_type == "data_table":
            return create_table_visualization(df, viz_config)
        else:
            return create_scatter_visualization(df, viz_config)
    
    except Exception as e:
        logger.error(f"Visualization creation failed: {e}")
        return None

def create_bar_chart_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
    """Create bar chart visualization"""
    try:
        # Get chart data from config or auto-detect
        chart_data = config.get("chart", {})
        
        # Check if this is a temperature vs salinity comparison query
        # Look for temperature and salinity columns in the data
        temp_cols = [col for col in df.columns if 'temperature' in col.lower() or 'temp' in col.lower()]
        sal_cols = [col for col in df.columns if 'salinity' in col.lower() or 'sal' in col.lower()]
        
        # Check if this is a comparison query (mentions multiple parameters)
        query_lower = config.get('user_query', '').lower() if isinstance(config, dict) else ''
        comparison_keywords = ['compare', 'comparison', 'vs', 'versus', 'and', 'both']
        is_comparison_query = any(keyword in query_lower for keyword in comparison_keywords)
        
        # If both temperature and salinity are available AND it's a comparison query
        if temp_cols and sal_cols and len(df) > 0 and is_comparison_query:
            return create_temperature_salinity_comparison_chart(df, temp_cols, sal_cols)
        
        # If only temperature is available OR it's not a comparison query
        elif temp_cols and len(df) > 0:
            return create_single_parameter_chart(df, temp_cols, 'Temperature')
        
        # If only salinity is available OR it's not a comparison query
        elif sal_cols and len(df) > 0:
            return create_single_parameter_chart(df, sal_cols, 'Salinity')
        
        if not chart_data:
            return create_generic_bar_chart(df)
        
        # Convert chart data to Plotly figure
        fig_dict = chart_data
        fig = go.Figure(fig_dict)
        
        # Update layout for better styling
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=500,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Bar chart creation failed: {e}")
        return create_generic_bar_chart(df)

def create_table_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
    """Create data table visualization"""
    try:
        # Get table data from config or auto-detect
        table_data = config.get("table", {})
        if not table_data:
            return create_generic_table(df)
        
        # Convert table data to Plotly figure
        fig_dict = table_data
        fig = go.Figure(fig_dict)
        
        # Force dark theme styling for all table elements
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=12),
            height=600,
            margin=dict(l=10, r=10, t=50, b=10),
            template="plotly_dark"
        )
        
        # Force dark styling on all table data
        for trace in fig.data:
            if hasattr(trace, 'header'):
                trace.header.fill.color = 'rgba(40, 40, 40, 0.95)'  # Dark header
                trace.header.font.color = 'white'  # White header text
                trace.header.line.color = 'rgba(255,255,255,0.3)'  # Light border
            if hasattr(trace, 'cells'):
                trace.cells.fill.color = 'rgba(25, 25, 25, 0.9)'  # Dark cell background
                trace.cells.font.color = 'white'  # White cell text
                trace.cells.line.color = 'rgba(255,255,255,0.2)'  # Light cell borders
        
        return fig
        
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        return create_generic_table(df)

def create_single_parameter_chart(df: pd.DataFrame, param_cols: list, param_name: str) -> go.Figure:
    """Create a bar chart showing data for a single parameter type"""
    try:
        # Calculate statistics for parameter columns
        param_data = []
        
        # Process parameter columns
        for param_col in param_cols:
            values = df[param_col].dropna()
            if len(values) > 0:
                # Handle both single values and arrays
                if values.iloc[0] is not None and isinstance(values.iloc[0], list):
                    # If it's an array, we'll skip it and use the surface/deep columns instead
                    continue
                else:
                    # Single values
                    param_data.append({
                        'parameter': param_col.replace('_', ' ').title(),
                        'mean': values.mean(),
                        'std': values.std(),
                        'min': values.min(),
                        'max': values.max(),
                        'count': len(values)
                    })
        
        if not param_data:
            return create_generic_bar_chart(df)
        
        # Create bar chart
        fig = go.Figure()
        
        # Add bars for each parameter
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        
        # Determine units based on parameter type
        units = '°C' if 'temperature' in param_name.lower() else 'PSU' if 'salinity' in param_name.lower() else ''
        
        for i, data in enumerate(param_data):
            fig.add_trace(go.Bar(
                name=data['parameter'],
                x=[data['parameter']],
                y=[data['mean']],
                error_y=dict(
                    type='data',
                    array=[data['std']],
                    visible=True
                ),
                marker_color=colors[i % len(colors)],
                text=[f"{data['mean']:.2f}{units}"],
                textposition='auto',
                hovertemplate=f"<b>{data['parameter']}</b><br>" +
                             f"Mean: {data['mean']:.2f}{units}<br>" +
                             f"Std: {data['std']:.2f}{units}<br>" +
                             f"Min: {data['min']:.2f}{units}<br>" +
                             f"Max: {data['max']:.2f}{units}<br>" +
                             f"Count: {data['count']}<br>" +
                             "<extra></extra>"
            ))
        
        # Update layout
        fig.update_layout(
            title=f'{param_name} Analysis',
            xaxis_title=f'{param_name} Parameters',
            yaxis_title=f'{param_name} ({units})',
            barmode='group',
            height=600,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Single parameter chart creation failed: {e}")
        return create_generic_bar_chart(df)

def create_temperature_salinity_comparison_chart(df: pd.DataFrame, temp_cols: list, sal_cols: list) -> go.Figure:
    """Create a bar chart comparing temperature and salinity parameters"""
    try:
        # Calculate statistics for temperature and salinity
        temp_data = []
        sal_data = []
        
        # Process temperature columns
        for temp_col in temp_cols:
            values = df[temp_col].dropna()
            if len(values) > 0:
                # Handle both single values and arrays
                if values.iloc[0] is not None and isinstance(values.iloc[0], list):
                    # If it's an array, we'll skip it and use the surface/deep columns instead
                    continue
                else:
                    # Single values
                    temp_data.append({
                        'parameter': temp_col.replace('_', ' ').title(),
                        'mean': values.mean(),
                        'std': values.std(),
                        'min': values.min(),
                        'max': values.max(),
                        'count': len(values)
                    })
        
        # Process salinity columns
        for sal_col in sal_cols:
            values = df[sal_col].dropna()
            if len(values) > 0:
                # Handle both single values and arrays
                if values.iloc[0] is not None and isinstance(values.iloc[0], list):
                    # If it's an array, we'll skip it and use the surface/deep columns instead
                    continue
                else:
                    # Single values
                    sal_data.append({
                        'parameter': sal_col.replace('_', ' ').title(),
                        'mean': values.mean(),
                        'std': values.std(),
                        'min': values.min(),
                        'max': values.max(),
                        'count': len(values)
                    })
        
        # Combine all data
        all_data = temp_data + sal_data
        
        if not all_data:
            return create_generic_bar_chart(df)
        
        # Create bar chart
        fig = go.Figure()
        
        # Add bars for each parameter
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        
        for i, data in enumerate(all_data):
            fig.add_trace(go.Bar(
                name=data['parameter'],
                x=[data['parameter']],
                y=[data['mean']],
                error_y=dict(
                    type='data',
                    array=[data['std']],
                    visible=True
                ),
                marker_color=colors[i % len(colors)],
                text=[f"{data['mean']:.2f}"],
                textposition='auto',
                hovertemplate=f"<b>{data['parameter']}</b><br>" +
                             f"Mean: {data['mean']:.2f}<br>" +
                             f"Std: {data['std']:.2f}<br>" +
                             f"Min: {data['min']:.2f}<br>" +
                             f"Max: {data['max']:.2f}<br>" +
                             f"Count: {data['count']}<br>" +
                             "<extra></extra>"
            ))
        
        # Update layout
        fig.update_layout(
            title='Temperature vs Salinity Comparison',
            xaxis_title='Oceanographic Parameters',
            yaxis_title='Values',
            barmode='group',
            height=600,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Temperature-salinity comparison chart creation failed: {e}")
        return create_generic_bar_chart(df)

def create_generic_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create a generic bar chart when no specific config is provided"""
    try:
        # Find the most suitable column for bar chart
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        if len(numeric_cols) == 0 and len(categorical_cols) == 0:
            return None
        
        # Use first categorical column for x-axis, first numeric for y-axis
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            
            # Group by categorical column and sum numeric column
            grouped = df.groupby(x_col)[y_col].sum().reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=grouped[x_col],
                y=grouped[y_col],
                marker_color='#06b6d4',
                text=grouped[y_col],
                textposition='auto'
            ))
            
            fig.update_layout(
                title=f'{y_col.title()} by {x_col.title()}',
                xaxis_title=x_col.title(),
                yaxis_title=y_col.title(),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=500
            )
            
            return fig
        
        return None
        
    except Exception as e:
        logger.error(f"Generic bar chart creation failed: {e}")
        return None

def create_generic_table(df: pd.DataFrame) -> go.Figure:
    """Create a generic table when no specific config is provided"""
    try:
        # Limit to first 20 rows and 8 columns for performance
        display_df = df.head(20)
        display_cols = display_df.columns[:8]
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=[col.replace('_', ' ').title() for col in display_cols],
                fill_color='rgba(40, 40, 40, 0.95)',  # Darker header
                font=dict(color='white', size=12),
                align='left',
                line=dict(color='rgba(255,255,255,0.3)', width=1)
            ),
            cells=dict(
                values=[display_df[col].astype(str) for col in display_cols],
                fill_color='rgba(25, 25, 25, 0.9)',  # Darker cell background
                align='left',
                font=dict(size=11, color='white'),
                line=dict(color='rgba(255,255,255,0.2)', width=1)
            )
        )])
        
        fig.update_layout(
            title=f'Data Table (Showing {len(display_df)} of {len(df)} records)',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=600,
            margin=dict(l=10, r=10, t=50, b=10),
            template="plotly_dark"
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Generic table creation failed: {e}")
        return None


def create_map_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
    """Create interactive map"""
    fig = go.Figure()
    
    if 'latitude' in df.columns and 'longitude' in df.columns:
        color_param = config.get("color_by", "temperature")
        
        # Try to find the best temperature column for coloring
        temp_col = None
        if color_param == "temperature":
            # Look for surface temperature column first
            if 'surface_temperature' in df.columns:
                temp_col = 'surface_temperature'
            elif 'temperature' in df.columns:
                # If raw temperature column exists, try to extract first value
                temp_col = 'temperature'
        
        if temp_col and temp_col in df.columns:
            # Handle array data by extracting first value if needed
            if temp_col == 'temperature' and df[temp_col].dtype == 'object':
                # Extract first value from temperature arrays
                temp_values = []
                for val in df[temp_col]:
                    if isinstance(val, list) and len(val) > 0:
                        temp_values.append(val[0])
                    elif pd.notna(val):
                        temp_values.append(val)
                    else:
                        temp_values.append(None)
                df_temp = pd.Series(temp_values)
            else:
                df_temp = df[temp_col]
            
            # Filter out NaN values for coloring
            valid_mask = pd.notna(df_temp)
            if valid_mask.any():
                fig.add_trace(go.Scattermapbox(
                    lat=df[valid_mask]['latitude'],
                    lon=df[valid_mask]['longitude'],
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=df_temp[valid_mask],
                        colorscale='RdYlBu_r',
                        showscale=True,
                        colorbar=dict(title=f"{color_param.title()} (°C)"),
                        opacity=0.8
                    ),
                    text=df[valid_mask].get('float_id', ''),
                    hovertemplate=(
                        "<b>Float:</b> %{text}<br>" +
                        "<b>Lat:</b> %{lat:.3f}°<br>" +
                        "<b>Lon:</b> %{lon:.3f}°<br>" +
                        f"<b>{color_param.title()}:</b> %{{marker.color:.2f}}°C<br>" +
                        "<extra></extra>"
                    ),
                    name="ARGO Floats"
                ))
            else:
                # Fallback if no valid temperature data
                fig.add_trace(go.Scattermapbox(
                    lat=df['latitude'],
                    lon=df['longitude'],
                    mode='markers',
                    marker=dict(size=9, color='#06b6d4', opacity=0.9),
                    text=df.get('float_id', ''),
                    hovertemplate=(
                        "<b>Float:</b> %{text}<br>" +
                        "<b>Lat:</b> %{lat:.3f}°<br>" +
                        "<b>Lon:</b> %{lon:.3f}°<br>" +
                        "<b>Temperature:</b> Data not available<br>" +
                        "<extra></extra>"
                    ),
                    name="ARGO Floats"
                ))
        else:
            fig.add_trace(go.Scattermapbox(
                lat=df['latitude'],
                lon=df['longitude'],
                mode='markers',
                marker=dict(size=9, color='#06b6d4', opacity=0.9),
                name="ARGO Floats"
            ))
    
    # Calculate dynamic map bounds based on data
    if 'latitude' in df and 'longitude' in df and not df.empty:
        min_lat, max_lat = df['latitude'].min(), df['latitude'].max()
        min_lon, max_lon = df['longitude'].min(), df['longitude'].max()
        
        # Calculate center
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Calculate appropriate zoom level based on data spread
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        max_range = max(lat_range, lon_range)
        
        # Dynamic zoom calculation
        if max_range > 100:
            zoom = 1
        elif max_range > 50:
            zoom = 2
        elif max_range > 20:
            zoom = 3
        elif max_range > 10:
            zoom = 4
        elif max_range > 5:
            zoom = 5
        else:
            zoom = 6
    else:
        center_lat, center_lon, zoom = 0, 0, 3
    
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        height=600,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        title=config.get("title", "ARGO Float Locations"),
        font=dict(color='white')
    )
    
    return fig

def create_profile_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
    """Create depth profile"""
    params = ['temperature', 'salinity', 'pressure', 'oxygen']
    available_params = [p for p in params if p in df.columns]
    
    if not available_params:
        return None
    
    n_params = min(len(available_params), 3)
    fig = make_subplots(
        rows=1, cols=n_params,
        shared_yaxes=True,
        subplot_titles=[p.title() for p in available_params[:n_params]]
    )
    
    depth_col = 'depth' if 'depth' in df else 'pressure'
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
    
    for i, param in enumerate(available_params[:n_params]):
        sorted_df = df.sort_values(depth_col)
        
        fig.add_trace(
            go.Scatter(
                x=sorted_df[param],
                y=sorted_df[depth_col],
                mode='lines+markers',
                name=param.title(),
                line=dict(color=colors[i], width=3),
                marker=dict(size=6),
                showlegend=False
            ),
            row=1, col=i+1
        )
        
        fig.update_xaxes(title_text=param.title(), row=1, col=i+1)
    
    fig.update_yaxes(
        title_text="Depth (m)",
        autorange='reversed',
        row=1, col=1
    )
    
    fig.update_layout(
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        title=config.get("title", "Ocean Parameter Profiles"),
        font=dict(color='white')
    )
    
    return fig

def create_timeseries_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
    """Create time series plot"""
    if 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'])
    else:
        return None
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    params = [col for col in numeric_cols if col not in ['depth', 'pressure', 'latitude', 'longitude']]
    
    if not params:
        return None
    
    fig = go.Figure()
    colors = FrontendConfig.COLOR_PALETTE
    
    for i, param in enumerate(params[:3]):  # Limit to 3 parameters
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df[param],
            mode='lines+markers',
            name=param.title(),
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title=config.get("title", "Parameter Time Series"),
        xaxis_title="Date",
        yaxis_title="Value",
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return fig

def create_scatter_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
    """Create scatter plot"""
    x_col = df.columns[0] if len(df.columns) > 0 else 'x'
    y_col = df.columns[1] if len(df.columns) > 1 else 'y'
    
    fig = px.scatter(
        df, x=x_col, y=y_col,
        title=config.get("title", f"{x_col.title()} vs {y_col.title()}"),
        color=df.columns[2] if len(df.columns) > 2 else None
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500
    )
    
    return fig

def create_streamlit_map(coordinates: List[List[float]], float_data: List[Dict[str, Any]] = None) -> go.Figure:
    """Create a Streamlit-compatible map using Plotly"""
    if not coordinates:
        return None
    
    # Extract coordinates
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    
    # Create markers data
    markers_data = []
    if float_data:
        for i, data in enumerate(float_data[:50]):  # Limit to 50 markers
            if i < len(coordinates):
                lat, lon = coordinates[i]
                float_id = data.get('float_id', f'Float {i+1}')
                date = data.get('profile_date', 'Unknown date')
                markers_data.append({
                    'lat': lat,
                    'lon': lon,
                    'float_id': float_id,
                    'date': date
                })
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Add trajectory line
    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='lines+markers',
        line=dict(color='#e74c3c', width=3),
        marker=dict(size=8, color='#2c3e50'),
        name='ARGO Trajectory',
        hovertemplate='<b>Position:</b> %{lat:.3f}°N, %{lon:.3f}°E<extra></extra>'
    ))
    
    # Add individual markers with popups
    if markers_data:
        for marker in markers_data:
            fig.add_trace(go.Scattermapbox(
                lat=[marker['lat']],
                lon=[marker['lon']],
                mode='markers',
                marker=dict(size=12, color='#06b6d4', symbol='circle'),
                name=marker['float_id'],
                hovertemplate=f'<b>Float:</b> {marker["float_id"]}<br><b>Date:</b> {marker["date"]}<br><b>Position:</b> {marker["lat"]:.3f}°N, {marker["lon"]:.3f}°E<extra></extra>',
                showlegend=False
            ))
    
    # Calculate map center and bounds
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Calculate zoom level based on data spread
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)
    max_range = max(lat_range, lon_range)
    
    if max_range > 100:
        zoom = 1
    elif max_range > 50:
        zoom = 2
    elif max_range > 20:
        zoom = 3
    elif max_range > 10:
        zoom = 4
    elif max_range > 5:
        zoom = 5
    else:
        zoom = 6
    
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        height=600,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        title="🗺️ Interactive ARGO Float Trajectory Map",
        font=dict(color='white'),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        )
    )
    
    return fig

# Query handling
def handle_query(query: str):
    """Handle user query"""
    start_time = time.time()
    print(f"DEBUG: handle_query called with: {query}")
    
    # Store current query for export functionality
    st.session_state.current_query = query
    
    # Add user message
    user_message = {
        "role": "user",
        "content": query,
        "timestamp": datetime.datetime.now()
    }
    st.session_state.messages.append(user_message)
    print(f"DEBUG: Added user message. Total messages: {len(st.session_state.messages)}")
    
    # =============================================================================
    # CONVERSATIONAL FEATURES - Early Detection (Zero Impact on Existing Logic)
    # =============================================================================
    
    # Handle greetings and casual conversation (immediate response, no backend call)
    query_lower = query.lower().strip()
    
    # Add to recent queries (skip greetings and casual conversation)
    if not any(phrase in query_lower for phrase in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "how are you", "how's it going", "how do you do", "thank you", "thanks", "thank you very much", "appreciate it", "bye", "goodbye", "see you later", "farewell"]):
        # Add to recent queries if not already present
        if query not in st.session_state.recent_queries:
            st.session_state.recent_queries.append(query)
            # Keep only last 20 queries
            if len(st.session_state.recent_queries) > 20:
                st.session_state.recent_queries = st.session_state.recent_queries[-20:]
    
    # Greeting responses
    if query_lower in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]:
        greeting_responses = [
            "Hello! I'm your ARGO ocean data assistant. I can help you explore temperature, salinity, and other oceanographic data from ARGO floats. What would you like to know about the oceans?",
            "Hi there! I'm here to help you discover insights about ocean data. I can analyze temperature profiles, salinity patterns, float trajectories, and much more. What interests you?",
            "Hello! Welcome to ARGO FloatChat. I can help you query oceanographic data, create visualizations, and find ARGO float information. How can I assist you today?"
        ]
        import random
        response = random.choice(greeting_responses)
        
        assistant_message = {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.datetime.now()
        }
        st.session_state.messages.append(assistant_message)
        st.rerun()
        return
    
    # Handle "how are you" type questions
    if any(phrase in query_lower for phrase in ["how are you", "how's it going", "how do you do"]):
        response = "I'm doing great! I'm ready to help you explore ocean data. I can analyze ARGO float measurements, create visualizations, and answer questions about oceanographic patterns. What would you like to explore?"
        
        assistant_message = {
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.datetime.now()
        }
        st.session_state.messages.append(assistant_message)
        st.rerun()
        return
    
    # Handle "thank you" responses
    if any(phrase in query_lower for phrase in ["thank you", "thanks", "thank you very much", "appreciate it"]):
        thank_you_responses = [
            "You're very welcome! I'm here whenever you need help exploring ocean data. Feel free to ask me anything about ARGO floats, temperature patterns, or oceanographic analysis!",
            "My pleasure! I love helping people discover insights about our oceans. What else would you like to explore?",
            "Happy to help! The ocean holds so many fascinating secrets - I'm excited to help you uncover them. What's your next question?"
        ]
        import random
        response = random.choice(thank_you_responses)
        
        assistant_message = {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.datetime.now()
        }
        st.session_state.messages.append(assistant_message)
        st.rerun()
        return
    
    # Handle "bye" or "goodbye" responses
    if any(phrase in query_lower for phrase in ["bye", "goodbye", "see you later", "farewell"]):
        goodbye_responses = [
            "Goodbye! It was great helping you explore ocean data today. Come back anytime to discover more about our amazing oceans!",
            "Farewell! I hope you found the ocean insights you were looking for. Feel free to return whenever you have more questions!",
            "See you later! The ocean data will always be here when you're ready to explore again. Take care!"
        ]
        import random
        response = random.choice(goodbye_responses)
        
        assistant_message = {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.datetime.now()
        }
        st.session_state.messages.append(assistant_message)
        st.rerun()
        return
    
    # Show loading
    loading_placeholder = st.empty()
    with loading_placeholder:
        render_loading_animation("Processing your query...")
    
    try:
        # Get current filters
        filters = st.session_state.get("current_filters", {})
        
        # Process query
        with loading_placeholder:
            render_loading_animation("Searching ocean data...")
        
        # Try backend first
        result = backend_adapter.process_natural_language_query(
            query,
            filters,
            language=st.session_state.get('language', 'en')
        )
        
        # Debug: Print result to identify the issue
        print(f"DEBUG - Result type: {type(result)}")
        print(f"DEBUG - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"DEBUG - Success value: {result.get('success') if isinstance(result, dict) else 'N/A'}")
        print(f"DEBUG - Visualization suggestions: {result.get('visualization_suggestions', 'None')}")
        print(f"DEBUG - Data records: {len(result.get('data', {}).get('records', [])) if result.get('data') else 'No data'}")
        print(f"DEBUG - SQL results: {len(result.get('retrieved_data', {}).get('sql_results', [])) if result.get('retrieved_data') else 'No retrieved_data'}")
        
        # Debug: Check if we have the right data structure
        if result.get('visualization_suggestions'):
            print(f"DEBUG - Viz suggestions type: {type(result['visualization_suggestions'])}")
            print(f"DEBUG - Viz suggestions keys: {list(result['visualization_suggestions'].keys()) if isinstance(result['visualization_suggestions'], dict) else 'Not a dict'}")
            if isinstance(result['visualization_suggestions'], dict) and 'suggestions' in result['visualization_suggestions']:
                print(f"DEBUG - Number of suggestions: {len(result['visualization_suggestions']['suggestions'])}")
                for i, suggestion in enumerate(result['visualization_suggestions']['suggestions']):
                    print(f"DEBUG - Suggestion {i}: {suggestion}")
        
        # Debug: Check visualizations array
        if result.get('visualizations'):
            print(f"DEBUG - Visualizations type: {type(result['visualizations'])}")
            print(f"DEBUG - Number of visualizations: {len(result['visualizations'])}")
            for i, viz in enumerate(result['visualizations']):
                print(f"DEBUG - Visualization {i}: {viz}")
        
        # If backend fails, show error message
        if not result.get("success"):
            logger.error("Backend query failed")
            result = {
                "success": False,
                "response": "Backend query failed. Please check your connection and try again.",
                "error": "Backend unavailable"
            }
        
        # Clear loading
        loading_placeholder.empty()
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Update performance metrics
        metrics = st.session_state.performance_metrics
        metrics["query_count"] += 1
        metrics["avg_response_time"] = (
            (metrics["avg_response_time"] * (metrics["query_count"] - 1) + response_time) /
            metrics["query_count"]
        )
        metrics["last_query_time"] = response_time
        
        if result.get("success"):
            # Get response content - handle both "response" and "answer" keys
            response_content = result.get("response") or result.get("answer") or "Query processed successfully"
            
            # Create assistant message
            message_data = {
                "role": "assistant",
                "content": response_content,
                "timestamp": datetime.datetime.now(),
                "response_time": response_time
            }
            
            # Handle old visualization logic but with HTML sanitization
            # Skip old visualization logic for summary/statistics queries
            is_summary_query = any(keyword in query.lower() for keyword in ["summary", "summarize", "overview", "statistics", "stats"])
            
            if not is_summary_query:
                viz_data = result.get("visualization") or result.get("visualizations")
                if viz_data:
                    # Handle both "visualization" and "visualizations"
                    if isinstance(viz_data, list) and viz_data:
                        viz_config = {
                            "type": viz_data[0].get("type", "map"),
                            "data": result.get("data", {}).get("records", []),
                            "title": viz_data[0].get("title", "ARGO Data Visualization"),
                            "color_by": viz_data[0].get("config", {}).get("color_by", "temperature")
                        }
                    else:
                        viz_config = viz_data
                    
                    # Check if this is a bar chart request - prioritize bar charts
                    if any(keyword in query.lower() for keyword in ["bar chart", "bar graph", "compare", "comparison"]):
                        # Skip map visualization for bar chart requests
                        pass
                    elif "coordinates" in viz_data and viz_data["coordinates"]:
                        # Create interactive map from coordinates
                        interactive_map = create_streamlit_map(
                            viz_data["coordinates"], 
                            result.get("data", {}).get("records", [])
                        )
                        if interactive_map:
                            message_data["interactive_map"] = interactive_map
                    else:
                        # Fallback to Plotly visualization
                        viz_fig = create_visualization(viz_config)
                        if viz_fig:
                            message_data["visualization"] = viz_fig
            
            # Handle visualization suggestions from backend - check multiple possible locations
            print("=== FRONTEND DEBUG START ===")
            print(f"DEBUG: API Response keys: {list(result.keys())}")
            print(f"DEBUG: Has visualization_suggestions: {'visualization_suggestions' in result}")
            print(f"DEBUG: Has visualizations: {'visualizations' in result}")
            print("=== FRONTEND DEBUG END ===")
            
            viz_suggestions = result.get("visualization_suggestions", {})
            print(f"DEBUG: Initial viz_suggestions: {viz_suggestions}")
            
            if not viz_suggestions or not viz_suggestions.get("suggestions"):
                # Try alternative location
                viz_suggestions = result.get("visualizations", [])
                print(f"DEBUG: Trying visualizations array: {viz_suggestions}")
                if viz_suggestions and isinstance(viz_suggestions, list):
                    # Convert list format to dict format
                    viz_suggestions = {"suggestions": viz_suggestions}
                    print(f"DEBUG: Converted to dict format: {viz_suggestions}")
            
            if viz_suggestions and viz_suggestions.get("suggestions"):
                suggestions = viz_suggestions["suggestions"]
                print(f"DEBUG: Found {len(suggestions)} visualization suggestions")
                
                # Smart prioritization for mixed visualization requests
                data_table_suggestions = [s for s in suggestions if s.get("type") == "data_table"]
                bar_chart_suggestions = [s for s in suggestions if s.get("type") == "bar_chart"]
                other_suggestions = [s for s in suggestions if s.get("type") not in ["data_table", "bar_chart"]]
                
                print(f"DEBUG: Found {len(data_table_suggestions)} data table suggestions")
                print(f"DEBUG: Found {len(bar_chart_suggestions)} bar chart suggestions")
                print(f"DEBUG: Found {len(other_suggestions)} other suggestions")
                
                # Check if user wants multiple visualization types
                wants_multiple = any(keyword in query.lower() for keyword in VisualizationConfig.MIXED_KEYWORDS)
                
                # Check for specific visualization type combinations
                has_data_table_request = any(keyword in query.lower() for keyword in VisualizationConfig.DATA_TABLE_KEYWORDS)
                has_bar_chart_request = any(keyword in query.lower() for keyword in VisualizationConfig.BAR_CHART_KEYWORDS)
                
                if wants_multiple and has_data_table_request and has_bar_chart_request and data_table_suggestions and bar_chart_suggestions:
                    # For mixed requests, take 1 of each type
                    prioritized_suggestions = data_table_suggestions[:1] + bar_chart_suggestions[:1]
                    print(f"DEBUG: Mixed request detected - using 1 data table + 1 bar chart")
                elif has_bar_chart_request and bar_chart_suggestions:
                    # For bar chart requests, take ONLY bar charts (up to limit)
                    prioritized_suggestions = bar_chart_suggestions
                    print(f"DEBUG: Bar chart request detected - using ONLY bar charts")
                elif has_data_table_request and data_table_suggestions:
                    # For data table requests, take ONLY data tables (up to limit)
                    prioritized_suggestions = data_table_suggestions
                    print(f"DEBUG: Data table request detected - using ONLY data tables")
                else:
                    # For other requests, use original prioritization
                    prioritized_suggestions = data_table_suggestions + bar_chart_suggestions + other_suggestions
                    print(f"DEBUG: Generic request - using default prioritization")
                
                # Use configuration for visualization limits
                max_visualizations = VisualizationConfig.MAX_VISUALIZATIONS
                
                # Only create visualizations if explicitly requested
                is_explicit_visualization_request = any(keyword in query.lower() for keyword in [
                    "bar chart", "bar graph", "data table", "table", "chart", "graph", "visualization", "plot",
                    "summary", "summarize", "overview", "statistics", "stats"
                ])
                
                if is_explicit_visualization_request:
                    # Try to create visualizations based on suggestions
                    for suggestion in prioritized_suggestions[:max_visualizations]:
                        suggestion_type = suggestion.get("type")
                        print(f"DEBUG: Processing suggestion type: {suggestion_type}")
                        print(f"DEBUG: Suggestion details: {suggestion}")
                        
                        if suggestion_type == "bar_chart":
                            # Get data from the right place - check multiple possible locations
                            data_records = []
                            if result.get("data", {}).get("records"):
                                data_records = result.get("data", {}).get("records", [])
                            elif result.get("retrieved_data", {}).get("sql_results"):
                                data_records = result.get("retrieved_data", {}).get("sql_results", [])
                            elif result.get("sql_results"):
                                data_records = result.get("sql_results", [])
                            
                            print(f"DEBUG: Found {len(data_records)} data records for bar chart")
                            
                            if data_records:
                                # Generate bar chart using backend data
                                chart_type = suggestion.get("chart_type", "auto")
                                bar_chart_result = backend_adapter.generate_bar_chart(
                                    data_records,
                                    chart_type,
                                    query
                                )
                                print(f"DEBUG: Bar chart result: {bar_chart_result.get('error', 'Success')}")
                                
                                if bar_chart_result and not bar_chart_result.get("error"):
                                    # Add user query to the config for better chart detection
                                    bar_chart_result['user_query'] = query
                                    bar_chart_fig = create_bar_chart_visualization(
                                        pd.DataFrame(data_records),
                                        bar_chart_result
                                    )
                                    if bar_chart_fig:
                                        message_data["bar_chart"] = bar_chart_fig
                                        print("DEBUG: Bar chart created successfully")
                    
                        elif suggestion_type == "data_table":
                            print(f"DEBUG: Processing data table suggestion: {suggestion}")
                            # Get data from the right place
                            data_records = []
                            if result.get("data", {}).get("records"):
                                data_records = result.get("data", {}).get("records", [])
                            elif result.get("retrieved_data", {}).get("sql_results"):
                                data_records = result.get("retrieved_data", {}).get("sql_results", [])
                            elif result.get("sql_results"):
                                data_records = result.get("sql_results", [])
                            
                            print(f"DEBUG: Found {len(data_records)} data records for data table")
                            
                            if data_records:
                                # Generate table using backend data
                                table_type = suggestion.get("table_type", "auto")
                                print(f"DEBUG: Generating data table with type: {table_type}")
                                table_result = backend_adapter.generate_data_table(
                                    data_records,
                                    table_type
                                )
                                print(f"DEBUG: Data table result: {table_result.get('error', 'Success')}")
                                if table_result and not table_result.get("error"):
                                    table_fig = create_table_visualization(
                                        pd.DataFrame(data_records),
                                        table_result
                                    )
                                    if table_fig:
                                        message_data["data_table"] = table_fig
                                        print("DEBUG: Data table created successfully")
                                        print(f"DEBUG: Message data keys after table: {list(message_data.keys())}")
                                    else:
                                        print("DEBUG: Failed to create table figure")
                                else:
                                    print(f"DEBUG: Data table generation failed: {table_result.get('error', 'Unknown error')}")
                            else:
                                print("DEBUG: No data records found for data table")
            
            # Store data for export
            if "data" in result:
                st.session_state.current_data = result["data"]
                st.session_state.current_query_id = result.get("query_id") or result.get("response_id")
            
            print(f"DEBUG: Final message data keys: {list(message_data.keys())}")
            print(f"DEBUG: Has data_table: {'data_table' in message_data}")
            print(f"DEBUG: Has bar_chart: {'bar_chart' in message_data}")
            st.session_state.messages.append(message_data)
            
            # Show success notification
            success_msg = f"Query processed in {response_time:.1f}s"
            st.success(success_msg)
        
        else:
            # Handle error - be more careful about accessing the response
            error_content = result.get("response") or result.get("error") or "Unknown error occurred"
            error_message = {
                "role": "assistant",
                "content": error_content,
                "error": True,
                "timestamp": datetime.datetime.now()
            }
            st.session_state.messages.append(error_message)
            st.error("Query failed")
    
    except Exception as e:
        loading_placeholder.empty()
        logger.error(f"Query handling failed: {e}")
        
        error_message = {
            "role": "assistant", 
            "content": f"I apologize, but I encountered an unexpected error: {str(e)}",
            "error": True,
            "timestamp": datetime.datetime.now()
        }
        st.session_state.messages.append(error_message)
        st.error(f"Unexpected error: {str(e)}")
    
    # Rerun to update UI
    st.rerun()

# Main application
def main():
    """Main application function - completely rewritten to avoid cached issues"""
    # Initialize session state
    init_session_state()
    
    # Periodic backend status check
    current_time = datetime.datetime.now()
    last_check = st.session_state.backend_status.get("last_check")
    
    if (not last_check or 
        (current_time - last_check).seconds > 60):
        status = backend_adapter.health_check()
        st.session_state.backend_status = {
            "status": "online" if status.get("backend_available") else "offline",
            "details": status,
            "last_check": current_time
        }
    
    # Render header
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">🌊 FloatChat</h1>
        <p class="header-subtitle">AI-Powered ARGO Ocean Data Discovery & Visualization</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    current_filters = render_sidebar()
    st.session_state.current_filters = current_filters
    
    # Recent queries in sidebar
    render_recent_queries()
    
    # Main content area
    col1, col2 = st.columns([2.5, 1.5])
    
    with col1:
        # Clean hero section - NO input fields here
        if not st.session_state.messages:
            st.markdown("""
                <div class="hero-prompt">
                    <h2 class="hero-title">Ask me anything about ocean data...</h2>
                </div>
            """, unsafe_allow_html=True)

        # Chat history only
        render_chat_interface()

        # ONLY chat input at the bottom
        user_query = st.chat_input("Ask me anything about ocean data...")
        if user_query:
            try:
                handle_query(user_query)
            except Exception as e:
                st.error(f"Error processing query: {e}")
        
        # Clear chat button below the input
        if st.button("🗑️ Clear Chat", key="clear_chat", help="Clear all conversation history", type="secondary"):
            st.session_state.messages = []
            st.session_state.current_data = None
            st.session_state.current_query_id = None
            st.rerun()
    
    with col2:
        # Quick queries section
        st.markdown("### 🚀 Quick Queries")
        queries = [
            "Show me temperature profiles in the Indian Ocean for the last month",
            "Compare salinity data near the equator between 2022 and 2023", 
            "Find the nearest ARGO floats to coordinates 20°N, 70°E",
            "Display BGC oxygen levels in the Arabian Sea",
            "Show float trajectories in the Bay of Bengal",
            "What's the temperature anomaly in the equatorial Pacific?"
        ]
        cols = st.columns(2)
        for i, query in enumerate(queries):
            with cols[i % 2]:
                if st.button(query, key=f"quick_{i}"):
                    handle_query(query)
        
        # Current data stats
        if st.session_state.current_data:
            st.markdown("### Current Dataset")
            data_records = st.session_state.current_data.get("records", [])
            if data_records:
                df = pd.DataFrame(data_records)
                st.markdown(f"""
                    <div class="metric-card">
                        <h4>Dataset Overview</h4>
                        <p><strong>Records:</strong> {len(df):,}</p>
                        <p><strong>Parameters:</strong> {len(df.select_dtypes(include=[np.number]).columns)}</p>
                        <p><strong>Floats:</strong> {df.get('float_id', pd.Series()).nunique()}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        # Performance metrics
        if st.session_state.performance_metrics["query_count"] > 0:
            metrics = st.session_state.performance_metrics
            st.markdown("### ⚡ Performance")
            st.markdown(f"""
                <div class="metric-card">
                    <p><strong>Queries:</strong> {metrics['query_count']}</p>
                    <p><strong>Avg Response:</strong> {metrics['avg_response_time']:.1f}s</p>
                </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
        <div style="text-align: center; color: rgba(255,255,255,0.6); padding: 2rem;">
            <p><strong>FloatChat</strong> - Democratizing Ocean Data Access through AI</p>
            <p>Backend: {'Connected' if st.session_state.backend_status['status'] == 'online' else 'Disconnected'} | 
               Session: {len(st.session_state.messages)} messages</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()