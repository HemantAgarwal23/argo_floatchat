#!/usr/bin/env python3
"""
test_multilingual.py
Test script for multilingual functionality
"""

from i18n import i18n

def test_translations():
    """Test the translation system"""
    print("🌐 Testing Multilingual Functionality")
    print("=" * 50)
    
    # Test different languages
    languages = ["en", "es", "fr", "hi"]
    
    for lang in languages:
        print(f"\n📝 Testing {lang.upper()}:")
        i18n.set_language(lang)
        
        # Test various translation keys
        test_keys = [
            "app_title",
            "chat.input_placeholder", 
            "quick_queries.title",
            "data_stats.total_floats",
            "errors.connection_failed"
        ]
        
        for key in test_keys:
            translation = i18n.translate(key)
            print(f"  {key}: {translation}")
    
    print("\n✅ Translation test completed!")

def test_language_switching():
    """Test language switching functionality"""
    print("\n🔄 Testing Language Switching")
    print("=" * 50)
    
    # Test switching between languages
    original_lang = i18n.get_language()
    
    for lang in ["en", "es", "fr", "hi"]:
        i18n.set_language(lang)
        current_lang = i18n.get_language()
        app_title = i18n.translate("app_title")
        print(f"Switched to {current_lang}: {app_title}")
    
    # Restore original language
    i18n.set_language(original_lang)
    print(f"Restored to original language: {original_lang}")
    
    print("✅ Language switching test completed!")

def test_available_languages():
    """Test available languages"""
    print("\n🌍 Available Languages")
    print("=" * 50)
    
    available = i18n.get_available_languages()
    for code, name in available.items():
        print(f"  {code}: {name}")
    
    print(f"\nTotal supported languages: {len(available)}")

if __name__ == "__main__":
    test_translations()
    test_language_switching() 
    test_available_languages()
    
    print("\n🎉 All multilingual tests completed successfully!")
    print("\nTo use in your Streamlit app:")
    print("1. Import: from i18n import i18n")
    print("2. Set language: i18n.set_language('es')")
    print("3. Translate: i18n.t('your.key')")
