#!/usr/bin/env python3
"""
Simple test to verify i18n system works
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from i18n import i18n
    print("✅ i18n module imported successfully")
    
    # Test basic functionality
    print(f"Current language: {i18n.get_language()}")
    
    # Test translation
    test_key = "app_title"
    translation = i18n.t(test_key)
    print(f"Translation for '{test_key}': {translation}")
    
    # Test language switching
    i18n.set_language('es')
    print(f"Switched to Spanish: {i18n.get_language()}")
    spanish_translation = i18n.t(test_key)
    print(f"Spanish translation: {spanish_translation}")
    
    # Test available languages
    languages = i18n.get_available_languages()
    print(f"Available languages: {list(languages.keys())}")
    
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
