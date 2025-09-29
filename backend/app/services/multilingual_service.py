#!/usr/bin/env python3
"""
multilingual_service.py
Multilingual support service for ARGO FloatChat backend
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()

class MultilingualService:
    """Service for handling multilingual responses and translations"""
    
    def __init__(self, locales_dir: str = "app/locales"):
        self.locales_dir = Path(locales_dir)
        self.translations = {}
        self.fallback_language = "en"
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files"""
        try:
            for lang_file in self.locales_dir.glob("*.json"):
                lang_code = lang_file.stem
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            logger.info("Loaded translations", languages=list(self.translations.keys()))
        except Exception as e:
            logger.error("Failed to load translations", error=str(e))
    
    def translate(self, key: str, language: str = "en", **kwargs) -> str:
        """Translate a key to the specified language"""
        try:
            # Try requested language
            if language in self.translations:
                translation = self.translations[language].get(key, key)
            else:
                # Fallback to English
                translation = self.translations.get(self.fallback_language, {}).get(key, key)
            
            # Format with kwargs if provided
            if kwargs:
                try:
                    return translation.format(**kwargs)
                except (KeyError, ValueError):
                    return translation
            
            return translation
        except Exception as e:
            logger.error("Translation failed", key=key, language=language, error=str(e))
            return key
    
    def translate_response(self, response_data: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        """Translate response data to specified language"""
        try:
            if language == "en" or language not in self.translations:
                return response_data
            
            # Translate common response fields
            translated_response = response_data.copy()
            
            # Translate response text
            if "response" in translated_response:
                translated_response["response"] = self._translate_response_text(
                    translated_response["response"], language
                )
            
            # Translate error messages
            if "error" in translated_response:
                error_key = f"errors.{translated_response['error']}"
                translated_response["error"] = self.translate(error_key, language)
            
            # Translate visualization titles
            if "visualization" in translated_response:
                viz = translated_response["visualization"]
                if isinstance(viz, dict) and "title" in viz:
                    viz["title"] = self._translate_visualization_title(viz["title"], language)
            
            return translated_response
        except Exception as e:
            logger.error("Response translation failed", error=str(e))
            return response_data
    
    def _translate_response_text(self, text: str, language: str) -> str:
        """Translate response text content"""
        # Common patterns to translate
        translations = {
            "en": {
                "temperature profiles": "temperature profiles",
                "salinity data": "salinity data",
                "oxygen levels": "oxygen levels",
                "found": "found",
                "records": "records",
                "profiles": "profiles",
                "data points": "data points"
            },
            "es": {
                "temperature profiles": "perfiles de temperatura",
                "salinity data": "datos de salinidad", 
                "oxygen levels": "niveles de oxígeno",
                "found": "encontrados",
                "records": "registros",
                "profiles": "perfiles",
                "data points": "puntos de datos"
            },
            "fr": {
                "temperature profiles": "profils de température",
                "salinity data": "données de salinité",
                "oxygen levels": "niveaux d'oxygène", 
                "found": "trouvés",
                "records": "enregistrements",
                "profiles": "profils",
                "data points": "points de données"
            },
            "hi": {
                "temperature profiles": "तापमान प्रोफाइल",
                "salinity data": "लवणता डेटा",
                "oxygen levels": "ऑक्सीजन स्तर",
                "found": "मिले",
                "records": "रिकॉर्ड",
                "profiles": "प्रोफाइल", 
                "data points": "डेटा बिंदु"
            }
        }
        
        if language in translations:
            for en_text, translated_text in translations[language].items():
                text = text.replace(en_text, translated_text)
        
        return text
    
    def _translate_visualization_title(self, title: str, language: str) -> str:
        """Translate visualization titles"""
        title_translations = {
            "en": {
                "ARGO Data Visualization": "ARGO Data Visualization",
                "Temperature Profile": "Temperature Profile",
                "Salinity Distribution": "Salinity Distribution",
                "Map View": "Map View"
            },
            "es": {
                "ARGO Data Visualization": "Visualización de Datos ARGO",
                "Temperature Profile": "Perfil de Temperatura", 
                "Salinity Distribution": "Distribución de Salinidad",
                "Map View": "Vista de Mapa"
            },
            "fr": {
                "ARGO Data Visualization": "Visualisation des Données ARGO",
                "Temperature Profile": "Profil de Température",
                "Salinity Distribution": "Distribution de Salinité", 
                "Map View": "Vue Carte"
            },
            "hi": {
                "ARGO Data Visualization": "ARGO डेटा विजुअलाइजेशन",
                "Temperature Profile": "तापमान प्रोफाइल",
                "Salinity Distribution": "लवणता वितरण",
                "Map View": "मानचित्र दृश्य"
            }
        }
        
        if language in title_translations:
            return title_translations[language].get(title, title)
        
        return title
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages with their display names"""
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
    
    def format_multilingual_message(self, message_key: str, language: str, **kwargs) -> str:
        """Format a multilingual message"""
        try:
            # Try to get the message from translations
            if language in self.translations:
                message = self.translations[language].get(message_key, message_key)
            else:
                # Fallback to English
                message = self.translations.get(self.fallback_language, {}).get(message_key, message_key)
            
            # Format with provided kwargs
            if kwargs:
                try:
                    return message.format(**kwargs)
                except (KeyError, ValueError):
                    return message
            
            return message
        except Exception as e:
            logger.error("Message formatting failed", message_key=message_key, language=language, error=str(e))
            return message_key

# Global multilingual service instance
multilingual_service = MultilingualService()
