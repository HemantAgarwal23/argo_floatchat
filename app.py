"""
Vercel entry point for ARGO FloatChat Frontend
"""
import sys
import os

# Add the frontend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))

# Import and run the Streamlit app
from floatchat_app import main

if __name__ == "__main__":
    main()
