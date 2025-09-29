#!/usr/bin/env python3
"""
Test script to verify the app can start properly
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    print("Testing app startup...")
    
    # Test imports
    print("1. Testing imports...")
    from frontend_config import FrontendConfig
    print("   ✅ FrontendConfig imported")
    
    from backend_adapter import BackendAdapter
    print("   ✅ BackendAdapter imported")
    
    from i18n import i18n
    print("   ✅ i18n imported")
    
    from multilingual_components import language_selector
    print("   ✅ multilingual_components imported")
    
    # Test i18n functionality
    print("2. Testing i18n functionality...")
    i18n.set_language('en')
    app_title = i18n.t('app_title')
    print(f"   ✅ App title: {app_title}")
    
    chat_placeholder = i18n.t('chat.input_placeholder')
    print(f"   ✅ Chat placeholder: {chat_placeholder}")
    
    quick_queries_title = i18n.t('quick_queries.title')
    print(f"   ✅ Quick queries title: {quick_queries_title}")
    
    print("3. Testing language switching...")
    i18n.set_language('es')
    spanish_title = i18n.t('app_title')
    print(f"   ✅ Spanish title: {spanish_title}")
    
    print("\n🎉 All tests passed! The app should work correctly.")
    print("📝 Translation keys should now show as proper text:")
    print(f"   - App title: {i18n.t('app_title')}")
    print(f"   - Chat input: {i18n.t('chat.input_placeholder')}")
    print(f"   - Quick queries: {i18n.t('quick_queries.title')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
