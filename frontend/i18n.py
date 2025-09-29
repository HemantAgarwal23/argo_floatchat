#!/usr/bin/env python3
"""
i18n.py
Internationalization (i18n) support for FloatChat
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class I18nManager:
    """Manages internationalization for the FloatChat application"""
    
    def __init__(self, locales_dir: str = "locales"):
        self.locales_dir = Path(locales_dir)
        self.current_language = "en"  # Default to English
        self.translations = {}
        self.fallback_language = "en"
        
        # Create locales directory if it doesn't exist
        self.locales_dir.mkdir(exist_ok=True)
        
        # Load translations
        self._load_translations()
    
    def set_language(self, language_code: str) -> bool:
        """Set the current language"""
        if language_code in self.translations:
            self.current_language = language_code
            return True
        return False
    
    def get_language(self) -> str:
        """Get the current language code"""
        return self.current_language
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages with their display names"""
        return {
            "en": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "it": "Italiano",
            "pt": "Português",
            "ru": "Русский",
            "zh": "中文",
            "ja": "日本語",
            "ko": "한국어",
            "ar": "العربية",
            "hi": "हिन्दी"
        }
    
    def translate(self, key: str, **kwargs) -> str:
        """Translate a key to the current language"""
        translation = self._get_translation(key)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError):
                return translation
        
        return translation
    
    def t(self, key: str, **kwargs) -> str:
        """Short alias for translate"""
        return self.translate(key, **kwargs)
    
    def _get_translation(self, key: str) -> str:
        """Get translation for a key with fallback"""
        # Try current language
        if self.current_language in self.translations:
            current_translations = self.translations[self.current_language]
            # Handle nested keys like "chat.input_placeholder"
            value = self._get_nested_value(current_translations, key)
            if value is not None:
                return value
        
        # Try fallback language
        if self.fallback_language in self.translations:
            fallback_translations = self.translations[self.fallback_language]
            value = self._get_nested_value(fallback_translations, key)
            if value is not None:
                return value
        
        # Return key if no translation found
        return key
    
    def _get_nested_value(self, data: dict, key: str):
        """Get nested value from dictionary using dot notation"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def _load_translations(self):
        """Load all translation files"""
        for lang_code in self.get_available_languages().keys():
            lang_file = self.locales_dir / f"{lang_code}.json"
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading translations for {lang_code}: {e}")
    
    def create_translation_file(self, language_code: str, translations: Dict[str, str]):
        """Create or update a translation file"""
        lang_file = self.locales_dir / f"{language_code}.json"
        
        # Load existing translations if file exists
        existing_translations = {}
        if lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    existing_translations = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Merge with new translations
        existing_translations.update(translations)
        
        # Save translations
        try:
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(existing_translations, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving translations for {language_code}: {e}")
            return False

# Global i18n manager instance
i18n = I18nManager()
