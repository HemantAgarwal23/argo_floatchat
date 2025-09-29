#!/usr/bin/env python3
"""
multilingual_components.py
Multilingual components for Streamlit FloatChat application
"""

import streamlit as st
from typing import Dict, Any, Optional
from i18n import i18n

def language_selector() -> str:
    """Create a language selector component in the sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🌐 " + i18n.t("sidebar.language"))
        
        # Get available languages
        available_languages = i18n.get_available_languages()
        current_language = i18n.get_language()
        
        # Create language selection
        selected_language = st.selectbox(
            "Select Language",
            options=list(available_languages.keys()),
            format_func=lambda x: f"{available_languages[x]}",
            index=list(available_languages.keys()).index(current_language),
            key="language_selector"
        )
        
        # Update language if changed
        if selected_language != current_language:
            i18n.set_language(selected_language)
            # Use a session state flag to trigger rerun only when needed
            if 'language_changed' not in st.session_state:
                st.session_state['language_changed'] = True
        
        return selected_language

def render_header():
    """Render the multilingual header"""
    st.markdown(f"""
    <div class="header-container">
        <h1 class="header-title">{i18n.t("app_title")}</h1>
        <p class="header-subtitle">{i18n.t("app_subtitle")}</p>
    </div>
    """, unsafe_allow_html=True)

def render_quick_queries():
    """Render multilingual quick queries section"""
    st.markdown(f"### 🚀 {i18n.t('quick_queries.title')}")
    
    # Quick query buttons with translations
    queries = [
        ("temperature_profiles", i18n.t("quick_queries.temperature_profiles")),
        ("salinity_comparison", i18n.t("quick_queries.salinity_comparison")),
        ("nearest_floats", i18n.t("quick_queries.nearest_floats")),
        ("bgc_oxygen", i18n.t("quick_queries.bgc_oxygen")),
        ("float_trajectories", i18n.t("quick_queries.float_trajectories")),
        ("temperature_anomaly", i18n.t("quick_queries.temperature_anomaly")),
        ("chlorophyll_comparison", i18n.t("quick_queries.chlorophyll_comparison")),
        ("deep_water_trends", i18n.t("quick_queries.deep_water_trends"))
    ]
    
    # Create columns for better layout
    cols = st.columns(2)
    for i, (query_key, query_text) in enumerate(queries):
        with cols[i % 2]:
            if st.button(query_text, key=f"quick_query_{query_key}"):
                print(f"DEBUG: Quick query button clicked: {query_text}")
                return query_text
    
    return None

def render_data_statistics(stats: Dict[str, Any]):
    """Render multilingual data statistics"""
    st.markdown(f"### 📊 {i18n.t('data_stats.geographic_coverage')}")
    
    # Create metrics columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            i18n.t("data_stats.total_floats"),
            stats.get("total_floats", 0)
        )
    
    with col2:
        st.metric(
            i18n.t("data_stats.total_profiles"),
            stats.get("total_profiles", 0)
        )
    
    with col3:
        date_range = stats.get("date_range", {})
        if date_range:
            st.metric(
                i18n.t("data_stats.date_range"),
                f"{date_range.get('min_date', 'N/A')} - {date_range.get('max_date', 'N/A')}"
            )
    
    with col4:
        st.metric(
            i18n.t("data_stats.profiles_with_bgc"),
            stats.get("profiles_with_bgc", 0)
        )

def render_navigation():
    """Render multilingual navigation"""
    nav_items = [
        ("home", i18n.t("navigation.home"), "🏠"),
        ("chat", i18n.t("navigation.chat"), "💬"),
        ("data_explorer", i18n.t("navigation.data_explorer"), "🔍"),
        ("visualizations", i18n.t("navigation.visualizations"), "📈"),
        ("settings", i18n.t("navigation.settings"), "⚙️"),
        ("help", i18n.t("navigation.help"), "❓")
    ]
    
    # Create navigation tabs
    selected_tab = st.radio(
        "Navigation",
        options=[item[0] for item in nav_items],
        format_func=lambda x: next(f"{item[2]} {item[1]}" for item in nav_items if item[0] == x),
        horizontal=True,
        key="main_navigation"
    )
    
    return selected_tab

def render_chat_interface():
    """Render multilingual chat interface - DEPRECATED"""
    # This function is no longer used to prevent duplicate chat inputs
    # The main chat interface is handled in floatchat_app.py
    pass

def render_status_indicator(status: str):
    """Render multilingual status indicator"""
    status_config = {
        "online": ("🟢", i18n.t("status.online"), "status-online"),
        "offline": ("🔴", i18n.t("status.offline"), "status-offline"),
        "connecting": ("🟡", i18n.t("status.connecting"), "status-pulse"),
        "connected": ("🟢", i18n.t("status.connected"), "status-online"),
        "disconnected": ("🔴", i18n.t("status.disconnected"), "status-offline")
    }
    
    if status in status_config:
        icon, text, css_class = status_config[status]
        st.markdown(f"""
        <div class="status-indicator {css_class}">
            <span>{icon}</span>
            <span>{text}</span>
        </div>
        """, unsafe_allow_html=True)

def render_error_message(error_key: str, **kwargs):
    """Render multilingual error messages"""
    error_message = i18n.t(f"errors.{error_key}", **kwargs)
    st.error(f"❌ {error_message}")

def render_success_message(message_key: str, **kwargs):
    """Render multilingual success messages"""
    success_message = i18n.t(message_key, **kwargs)
    st.success(f"✅ {success_message}")

def render_loading_message():
    """Render multilingual loading message"""
    st.markdown(f"""
    <div class="loading-container">
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
        <span>{i18n.t('chat.thinking')}</span>
    </div>
    """, unsafe_allow_html=True)

def render_export_options():
    """Render multilingual export options"""
    st.markdown(f"### 📥 {i18n.t('export.download_data')}")
    
    export_formats = i18n.t("export.formats")
    selected_format = st.selectbox(
        i18n.t("export.download_data"),
        options=list(export_formats.keys()),
        format_func=lambda x: export_formats[x],
        key="export_format"
    )
    
    return selected_format

def render_region_selector():
    """Render multilingual region selector"""
    regions = {
        "indian_ocean": i18n.t("regions.indian_ocean"),
        "arabian_sea": i18n.t("regions.arabian_sea"),
        "bay_of_bengal": i18n.t("regions.bay_of_bengal"),
        "equatorial_pacific": i18n.t("regions.equatorial_pacific"),
        "north_atlantic": i18n.t("regions.north_atlantic"),
        "southern_ocean": i18n.t("regions.southern_ocean")
    }
    
    selected_region = st.selectbox(
        "Select Region",
        options=list(regions.keys()),
        format_func=lambda x: regions[x],
        key="region_selector"
    )
    
    return selected_region

def render_parameter_selector():
    """Render multilingual parameter selector"""
    parameters = {
        "temperature": i18n.t("parameters.temperature"),
        "salinity": i18n.t("parameters.salinity"),
        "pressure": i18n.t("parameters.pressure"),
        "depth": i18n.t("parameters.depth"),
        "dissolved_oxygen": i18n.t("parameters.dissolved_oxygen"),
        "ph": i18n.t("parameters.ph"),
        "nitrate": i18n.t("parameters.nitrate"),
        "chlorophyll": i18n.t("parameters.chlorophyll")
    }
    
    selected_params = st.multiselect(
        "Select Parameters",
        options=list(parameters.keys()),
        format_func=lambda x: parameters[x],
        key="parameter_selector"
    )
    
    return selected_params
