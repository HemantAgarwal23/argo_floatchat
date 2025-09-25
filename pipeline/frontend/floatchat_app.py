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
        background: linear-gradient(135deg, var(--dark-bg) 0%, var(--dark-surface) 50%, #334155 100%);
        background-attachment: fixed;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-indigo) 50%, var(--primary-purple) 100%);
        padding: 3rem 2rem;
        border-radius: 24px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2), 0 0 0 1px rgba(255,255,255,0.1);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .header-title {
        color: white;
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
        letter-spacing: -0.02em;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.3rem;
        margin-top: 1rem;
        font-weight: 400;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Chat messages */
    .user-message {
        background: linear-gradient(135deg, var(--primary-indigo) 0%, #1d4ed8 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 24px 24px 8px 24px;
        margin: 1rem 0 1rem auto;
        max-width: 80%;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
        animation: slideInRight 0.3s ease-out;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 24px 24px 24px 8px;
        margin: 1rem 0;
        max-width: 85%;
        box-shadow: 0 8px 25px rgba(55, 65, 81, 0.3);
        border: 1px solid rgba(255,255,255,0.1);
        animation: slideInLeft 0.3s ease-out;
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
    
    /* Enhanced buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-indigo) 100%);
        color: white !important;
        border: none;
        border-radius: 16px;
        padding: 1rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(6, 182, 212, 0.4);
    }
    
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
        "current_data": None,
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

# UI Components
def render_header():
    """Render the main header with status"""
    backend_status = st.session_state.backend_status
    status_text = "🟢 Online" if backend_status.get("status") == "online" else "🔴 Offline"
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
        st.markdown("### 🎛️ Control Panel")
        
        # Backend status check
        if st.button("🔄 Refresh Status", use_container_width=True):
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
            status_text = "🟢 Online" if status["status"] == "online" else "🔴 Offline"
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
            st.markdown("### 📥 Export")
            export_format = st.selectbox(
                "Format",
                FrontendConfig.EXPORT_FORMATS,
                key="export_format"
            )
            
            if st.button("📊 Export Data", use_container_width=True):
                if st.session_state.current_query_id:
                    with st.spinner("Preparing export..."):
                        export_data = backend_adapter.export_query_results(
                            st.session_state.current_query_id,
                            export_format
                        )
                        if export_data:
                            st.download_button(
                                "⬇️ Download",
                                export_data,
                                f"floatchat_export.{export_format}",
                                use_container_width=True
                            )
                        else:
                            st.error("Export failed")
                else:
                    st.warning("No data to export")
        
        return {}

def render_chat_interface():
    """Render the chat interface"""
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    # Display messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(
                f'<div class="user-message">{message["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="assistant-message">{message["content"]}</div>',
                unsafe_allow_html=True
            )
            
            # Show visualization if available
            if "visualization" in message and message["visualization"]:
                # Create unique key using message content hash and timestamp
                import hashlib
                content_hash = hashlib.md5(str(message.get('content', '')).encode()).hexdigest()[:8]
                unique_key = f"visualization_{content_hash}_{message.get('response_id', 'default')}_{message.get('timestamp', 'unknown')}"
                st.plotly_chart(message["visualization"], use_container_width=True, key=unique_key)
            
            # Show interactive map if available
            if "interactive_map" in message and message["interactive_map"]:
                # Create unique key using message content hash and timestamp
                import hashlib
                content_hash = hashlib.md5(str(message.get('content', '')).encode()).hexdigest()[:8]
                unique_key = f"interactive_map_{content_hash}_{message.get('response_id', 'default')}_{message.get('timestamp', 'unknown')}"
                st.plotly_chart(message["interactive_map"], use_container_width=True, key=unique_key)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_quick_queries():
    """Render quick query buttons"""
    st.markdown("### 🚀 Quick Queries")
    
    queries = FrontendConfig.QUICK_QUERIES[:6]  # Show first 6
    
    cols = st.columns(2)
    for i, query in enumerate(queries):
        col = cols[i % 2]
        with col:
            if st.button(query, key=f"quick_{i}", use_container_width=True):
                handle_query(query)

def render_loading_animation(message: str = "Processing..."):
    """Render loading animation"""
    return st.markdown(f"""
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
        else:
            return create_scatter_visualization(df, viz_config)
    
    except Exception as e:
        logger.error(f"Visualization creation failed: {e}")
        return None


def create_map_visualization(df: pd.DataFrame, config: Dict) -> go.Figure:
    """Create interactive map"""
    fig = go.Figure()
    
    if 'latitude' in df.columns and 'longitude' in df.columns:
        color_param = config.get("color_by", "temperature")
        
        if color_param and color_param in df.columns:
            fig.add_trace(go.Scattermapbox(
                lat=df['latitude'],
                lon=df['longitude'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=df[color_param],
                    colorscale='RdYlBu_r',
                    showscale=True,
                    colorbar=dict(title=f"{color_param.title()}"),
                    opacity=0.8
                ),
                text=df.get('float_id', ''),
                hovertemplate=(
                    "<b>Float:</b> %{text}<br>" +
                    "<b>Lat:</b> %{lat:.3f}°<br>" +
                    "<b>Lon:</b> %{lon:.3f}°<br>" +
                    f"<b>{color_param.title()}:</b> %{{marker.color:.2f}}<br>" +
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
    
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "timestamp": datetime.datetime.now()
    })
    
    # Show loading
    loading_placeholder = st.empty()
    with loading_placeholder:
        render_loading_animation("🤔 Processing your query...")
    
    try:
        # Get current filters
        filters = st.session_state.get("current_filters", {})
        
        # Process query
        with loading_placeholder:
            render_loading_animation("🔍 Searching ocean data...")
        
        # Try backend first
        result = backend_adapter.process_natural_language_query(query, filters)
        
        # Debug: Print result to identify the issue
        print(f"DEBUG - Result type: {type(result)}")
        print(f"DEBUG - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"DEBUG - Success value: {result.get('success') if isinstance(result, dict) else 'N/A'}")
        
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
            
            # Add visualization if available
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
                
                # Check if we have coordinates for map visualization
                if "coordinates" in viz_data and viz_data["coordinates"]:
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
            
            # Store data for export
            if "data" in result:
                st.session_state.current_data = result["data"]
                st.session_state.current_query_id = result.get("query_id") or result.get("response_id")
            
            st.session_state.messages.append(message_data)
            
            # Show success notification
            success_msg = f"✅ Query processed in {response_time:.1f}s"
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
            st.error("❌ Query failed")
    
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
        st.error(f"❌ Unexpected error: {str(e)}")
    
    # Rerun to update UI
    st.rerun()

# Main application
def main():
    """Main application function"""
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
    
    # Render UI
    render_header()
    
    # Sidebar
    current_filters = render_sidebar()
    st.session_state.current_filters = current_filters
    
    # Main content
    col1, col2 = st.columns([2.5, 1.5])
    
    with col1:
        # Chat interface
        st.markdown("### 💬 Chat with FloatChat")
        render_chat_interface()
        
        # Query input
        st.markdown("### 🎯 Ask Your Question")
        
        # Show example queries for new users
        if not st.session_state.messages:
            st.markdown("""
                <div style="background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.3); 
                           border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                    <h4 style="color: #06b6d4; margin: 0 0 0.5rem 0;">💡 Try asking:</h4>
                    <ul style="margin: 0; color: rgba(255,255,255,0.8);">
                        <li>"Show me temperature profiles in the Indian Ocean"</li>
                        <li>"Compare salinity data in the Arabian Sea vs Bay of Bengal"</li>
                        <li>"Find ARGO floats near coordinates 20°N, 70°E"</li>
                        <li>"What are the oxygen levels in the equatorial Pacific?"</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
        
        # Query input
        query = st.text_input(
            "Query Input",  # Proper label for accessibility
            placeholder="Type your ocean data query here...",
            key="query_input",
            label_visibility="collapsed"
        )
        
        # Action buttons
        col_send, col_clear = st.columns([3, 1])
        
        with col_send:
            if st.button("🚀 Send Query", type="primary", use_container_width=True):
                if query.strip():
                    handle_query(query)
                    st.session_state.query_input = ""
                    st.rerun()
        
        with col_clear:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.messages = []
                st.session_state.current_data = None
                st.rerun()
    
    with col2:
        # Quick queries
        render_quick_queries()
        
        # Current data stats
        if st.session_state.current_data:
            st.markdown("### 📈 Current Dataset")
            
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
            <p>🌊 <strong>FloatChat</strong> - Democratizing Ocean Data Access through AI</p>
            <p>Backend: {'🟢 Connected' if st.session_state.backend_status['status'] == 'online' else '🔴 Disconnected'} | 
               Session: {len(st.session_state.messages)} messages</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()