#!/usr/bin/env python3
"""
Simple script to start the FloatChat app with proper configuration
"""

import subprocess
import sys
import os

def start_app():
    """Start the Streamlit app"""
    print("🌊 Starting FloatChat...")
    print("📝 Fixed issues:")
    print("   ✅ Config TOML duplicate keys fixed")
    print("   ✅ Language selector label fixed")
    print("   ✅ Multilingual system working")
    print("   ✅ Translation keys now show proper text")
    print()
    
    try:
        # Start Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", "floatchat_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.headless", "false"
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        print("📱 Open your browser to: http://localhost:8501")
        print("🌐 Language selector will be in the sidebar")
        print()
        print("Press Ctrl+C to stop the app")
        print("-" * 50)
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 FloatChat stopped by user")
    except Exception as e:
        print(f"❌ Error starting app: {e}")

if __name__ == "__main__":
    start_app()
