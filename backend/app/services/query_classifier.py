"""
query_classifier.py
Query classification service to determine retrieval strategy for ARGO queries
"""
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime
import structlog
from app.core.multi_llm_client import multi_llm_client
from app.config import settings, QueryTypes

logger = structlog.get_logger()


class QueryClassifier:
    """Classifies user queries to determine optimal retrieval strategy"""
    
    def __init__(self):
        self.sql_keywords = [
            'show', 'get', 'find', 'retrieve', 'extract', 'list', 'count',
            'filter', 'where', 'between', 'greater than', 'less than',
            'exact', 'specific', 'precise', 'data', 'values', 'measurements',
            # Hindi keywords
            'दिखाएं', 'खोजें', 'प्राप्त', 'प्राप्त', 'निकालें', 'सूची', 'गिनती',
            'फ़िल्टर', 'कहाँ', 'के बीच', 'से अधिक', 'से कम',
            'सटीक', 'विशिष्ट', 'सटीक', 'डेटा', 'मूल्य', 'माप'
        ]
        
        self.vector_keywords = [
            'describe', 'explain', 'patterns', 'trends',
            'characteristics', 'general', 'typical', 'average',
            'variations', 'changes', 'insights', 'understand'
        ]
        
        self.hybrid_keywords = [
            'compare', 'analyze', 'relationship', 'correlation', 'impact',
            'influence', 'effect', 'difference', 'similar', 'contrast',
            'summarize', 'overview', 'statistics', 'stats', 'summary',
            # Hindi keywords
            'तुलना', 'विश्लेषण', 'संबंध', 'प्रभाव', 'अंतर', 'समान', 'विरोध',
            'तुलना करें', 'विश्लेषण करें', 'तुलना कर', 'विश्लेषण कर'
        ]
        
        # Visualization type patterns
        self.bar_chart_keywords = [
            'bar chart', 'bar graph', 'comparison chart', 'histogram', 'bar plot',
            'compare', 'comparison', 'distribution', 'statistics', 'count',
            'बार चार्ट', 'बार ग्राफ', 'तुलना चार्ट', 'तुलना', 'वितरण', 'सांख्यिकी'
        ]
        
        self.table_keywords = [
            'table', 'data table', 'records table', 'detailed data', 'tabular',
            'list', 'summary table', 'comparison table', 'statistics table',
            'टेबल', 'डेटा टेबल', 'रिकॉर्ड्स टेबल', 'विस्तृत डेटा', 'सारणी', 'सूची'
        ]
        
        self.chart_type_patterns = {
            'parameter_comparison': [
                r'compare.*temperature.*salinity', r'compare.*parameters',
                r'temperature.*vs.*salinity', r'parameter.*comparison'
            ],
            'temporal_distribution': [
                r'time.*distribution', r'over.*time', r'temporal.*analysis',
                r'data.*by.*month', r'data.*by.*year', r'time.*series'
            ],
            'regional_comparison': [
                r'regional.*comparison', r'by.*region', r'ocean.*region',
                r'arabian.*sea.*vs.*bay.*bengal', r'region.*analysis'
            ],
            'depth_analysis': [
                r'depth.*analysis', r'by.*depth', r'surface.*vs.*deep',
                r'pressure.*analysis', r'depth.*distribution'
            ],
            'float_statistics': [
                r'float.*statistics', r'by.*float', r'float.*comparison',
                r'profile.*count.*by.*float', r'float.*analysis'
            ]
        }
        
        # Geographic patterns
        self.location_patterns = [
            r'near\s+(?:the\s+)?equator',
            r'in\s+the\s+(\w+\s+\w+|\w+)\s+(?:ocean|sea)',
            r'around\s+(\d+\.?\d*)[°\s]*[NS]\s*,?\s*(\d+\.?\d*)[°\s]*[EW]',
            r'latitude\s+(\d+\.?\d*)',
            r'longitude\s+(\d+\.?\d*)',
            r'arabian\s+sea', r'bay\s+of\s+bengal', r'indian\s+ocean',
            r'pacific\s+ocean', r'atlantic\s+ocean', r'southern\s+ocean',
            # Hindi patterns
            r'हिंद\s+महासागर', r'भारतीय\s+महासागर', r'अरब\s+सागर',
            r'बंगाल\s+की\s+खाड़ी', r'प्रशांत\s+महासागर', r'अटलांटिक\s+महासागर',
            r'में\s+(\w+)\s+महासागर', r'में\s+(\w+)\s+सागर',
            r'हिंद\s+महासागर\s+में', r'भारतीय\s+महासागर\s+में', r'अरब\s+सागर\s+में',
            r'बंगाल\s+की\s+खाड़ी\s+में', r'प्रशांत\s+महासागर\s+में'
        ]
        
        # Date patterns
        self.date_patterns = [
            r'in\s+(\w+\s+\d{4})',  # March 2023
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2023-03-15
            r'last\s+(\d+)\s+(days?|weeks?|months?|years?)',
            r'past\s+(\d+)\s+(days?|weeks?|months?|years?)',
            r'since\s+(\w+\s+\d{4}|\d{4})',
            r'between\s+(\w+\s+\d{4})\s+and\s+(\w+\s+\d{4})',
            # Hindi patterns
            r'पिछले\s+(\d+)\s+(दिन|सप्ताह|महीने|साल)',
            r'पिछले\s+(\w+)',  # पिछले महीने
            r'(\d{4})\s+में',  # 2023 में
            r'(\w+\s+\d{4})\s+से\s+(\w+\s+\d{4})\s+तक',  # March 2023 से June 2023 तक
            r'पिछले\s+महीने', r'पिछले\s+साल', r'पिछले\s+दिन',
            r'महीने\s+में', r'साल\s+में', r'दिन\s+में'
        ]
        
        # Parameter patterns
        self.parameter_patterns = {
            'temperature': r'temperature|temp|thermal|तापमान|गर्मी',
            'salinity': r'salinity|salt|halocline|लवणता|नमक',
            'dissolved_oxygen': r'dissolved\s+oxygen|oxygen|o2|do|ऑक्सीजन|ऑक्सीजन|ऑक्सीजन',
            'ph': r'ph|acidity|alkalinity|अम्लता|क्षारता',
            'nitrate': r'nitrate|nitrogen|no3|नाइट्रेट|नाइट्रोजन',
            'chlorophyll': r'chlorophyll|chl|phytoplankton|algae|क्लोरोफिल|शैवाल',
            'pressure': r'pressure|depth|deep|दबाव|गहराई|गहरे',
            'bgc': r'bgc|biogeochemical|biochemical|bio|जैवरासायनिक|जैविक'
        }
    
    def classify_query(self, user_query: str) -> Dict[str, Any]:
        """Main classification method with enhanced visualization detection"""
        try:
            # Clean query
            query_lower = user_query.lower().strip()

            if self._is_geographic_query(query_lower):
                return {
                    "query_type": "sql_retrieval",
                    "confidence": 0.95,
                    "reasoning": "Geographic coordinate query detected - requires SQL database query",
                    "extracted_entities": self._extract_entities(query_lower),
                    "preprocessing_suggestions": []
                }
            
            # Rule-based pre-classification
            rule_based_result = self._rule_based_classification(query_lower)
            
            # LLM-based classification for validation and entity extraction
            llm_result = multi_llm_client.classify_query_type(user_query)
            
            # Combine results
            final_result = self._combine_classifications(rule_based_result, llm_result, user_query)
            
            # Add visualization type detection
            visualization_info = self._detect_visualization_type(user_query)
            final_result['visualization'] = visualization_info
            
            logger.info("Query classified", 
                       query=user_query, 
                       type=final_result['query_type'],
                       confidence=final_result['confidence'],
                       visualization=visualization_info.get('preferred_type', 'none'))
            
            return final_result
            
        except Exception as e:
            logger.error("Query classification failed", query=user_query, error=str(e))
            # Fallback classification
            return {
                "query_type": QueryTypes.VECTOR_RETRIEVAL,
                "confidence": 0.3,
                "reasoning": f"Classification failed: {str(e)}",
                "extracted_entities": {},
                "preprocessing_suggestions": [],
                "visualization": {"preferred_type": "none", "confidence": 0.0}
            }
    
    def _rule_based_classification(self, query: str) -> Dict[str, Any]:
        """Rule-based classification using keyword patterns"""
        
        sql_score = 0
        vector_score = 0
        hybrid_score = 0
        
        # Count keyword matches
        for keyword in self.sql_keywords:
            if keyword in query:
                sql_score += 1
        
        for keyword in self.vector_keywords:
            if keyword in query:
                vector_score += 1
        
        for keyword in self.hybrid_keywords:
            if keyword in query:
                hybrid_score += 1
        
        # Specific patterns that strongly indicate SQL
        if any(pattern in query for pattern in ['show me', 'get me', 'find all', 'list all']):
            sql_score += 2
        
        if re.search(r'\b\d+\b', query):  # Contains numbers
            sql_score += 1
        
        if any(re.search(pattern, query) for pattern in self.location_patterns):
            sql_score += 1
        
        if any(re.search(pattern, query) for pattern in self.date_patterns):
            sql_score += 1
        
        # Determine classification
        max_score = max(sql_score, vector_score, hybrid_score)
        
        if max_score == 0:
            query_type = QueryTypes.VECTOR_RETRIEVAL
            confidence = 0.5
        elif sql_score == max_score:
            query_type = QueryTypes.SQL_RETRIEVAL
            confidence = min(0.9, 0.6 + (sql_score * 0.1))
        elif hybrid_score == max_score:
            query_type = QueryTypes.HYBRID_RETRIEVAL
            confidence = min(0.9, 0.6 + (hybrid_score * 0.1))
        else:
            query_type = QueryTypes.VECTOR_RETRIEVAL
            confidence = min(0.9, 0.6 + (vector_score * 0.1))
        
        return {
            "query_type": query_type,
            "confidence": confidence,
            "scores": {
                "sql": sql_score,
                "vector": vector_score,
                "hybrid": hybrid_score
            }
        }
    
    def _combine_classifications(self, rule_result: Dict[str, Any], 
                               llm_result: Dict[str, Any], 
                               original_query: str) -> Dict[str, Any]:
        """Combine rule-based and LLM classifications"""
        
        # Extract entities from both sources
        entities = self._extract_entities(original_query)
        llm_entities = llm_result.get('extracted_entities', {})
        
        # Merge entities
        for key, value in llm_entities.items():
            if key not in entities and value:
                entities[key] = value
        
        # Determine final classification
        rule_type = rule_result['query_type']
        llm_type = llm_result.get('query_type', QueryTypes.VECTOR_RETRIEVAL)
        
        # If both agree, use higher confidence
        if rule_type == llm_type:
            final_type = rule_type
            final_confidence = max(rule_result['confidence'], llm_result.get('confidence', 0.5))
        else:
            # If they disagree, prefer LLM result but lower confidence
            final_type = llm_type
            final_confidence = min(0.7, llm_result.get('confidence', 0.5))
        
        # Generate preprocessing suggestions
        suggestions = self._generate_preprocessing_suggestions(entities, final_type)
        
        return {
            "query_type": final_type,
            "confidence": final_confidence,
            "reasoning": llm_result.get('reasoning', 'Combined rule-based and LLM classification'),
            "extracted_entities": entities,
            "preprocessing_suggestions": suggestions,
            "classification_details": {
                "rule_based": rule_result,
                "llm_based": llm_result
            }
        }
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns"""
        entities = {
            "parameters": [],
            "locations": [],
            "dates": [],
            "float_ids": [],
            "profile_ids": [],
            "regions": [],
            "numeric_values": [],
            "operators": []
        }
        
        query_lower = query.lower()
        
        # FIXED: Enhanced ID extraction
        # Extract profile IDs (like "profile 1902681", "profile number 1902681")
        profile_id_pattern = r'\b(?:profile|profile\s+number)\s+(\d{7})\b'
        profile_ids = re.findall(profile_id_pattern, query_lower)
        entities["profile_ids"] = profile_ids
        
        # Extract float IDs (like "float 1902681")  
        float_id_pattern = r'\bfloat\s+(\d{7})\b'
        float_ids = re.findall(float_id_pattern, query_lower)
        entities["float_ids"] = float_ids
        
        # If no specific "profile" or "float" keyword, check for standalone 7-digit numbers
        if not profile_ids and not float_ids:
            standalone_id_pattern = r'\b(\d{7})\b'
            standalone_ids = re.findall(standalone_id_pattern, query)
            if standalone_ids:
                # Check context to determine if it's profile or float
                if 'profile' in query_lower:
                    entities["profile_ids"] = standalone_ids
                else:
                    entities["float_ids"] = standalone_ids  # Default to float
        
        # Extract parameters
        for param, pattern in self.parameter_patterns.items():
            if re.search(pattern, query_lower):
                entities["parameters"].append(param)
        
        # Extract locations
        for pattern in self.location_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                entities["locations"].extend([match if isinstance(match, str) else ' '.join(match) for match in matches])
        
        # Extract dates
        for pattern in self.date_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                entities["dates"].extend([match if isinstance(match, str) else ' '.join(match) for match in matches])
        
        # Extract numeric values and operators
        numeric_pattern = r'([><=]+)\s*(\d+\.?\d*)'
        numeric_matches = re.findall(numeric_pattern, query)
        for operator, value in numeric_matches:
            entities["operators"].append(operator)
            entities["numeric_values"].append(float(value))
        
        # Clean empty lists
        entities = {k: v for k, v in entities.items() if v}
        
        return entities
    
    def _generate_preprocessing_suggestions(self, entities: Dict[str, Any], 
                                          query_type: str) -> List[str]:
        """Generate suggestions for query preprocessing"""
        suggestions = []
        
        if query_type == QueryTypes.SQL_RETRIEVAL:
            if not entities.get("parameters"):
                suggestions.append("Consider specifying oceanographic parameters (temperature, salinity, etc.)")
            
            if not entities.get("locations") and not entities.get("dates"):
                suggestions.append("Adding location or date constraints will improve query performance")
        
        elif query_type == QueryTypes.VECTOR_RETRIEVAL:
            if len(entities.get("parameters", [])) > 3:
                suggestions.append("Consider breaking down into simpler questions for better semantic search")
        
        elif query_type == QueryTypes.HYBRID_RETRIEVAL:
            suggestions.append("This complex query will use both structured and semantic search")
        
        return suggestions
    
    def suggest_query_improvements(self, query: str, classification: Dict[str, Any]) -> List[str]:
        """Suggest improvements to user queries"""
        suggestions = []
        
        query_type = classification['query_type']
        entities = classification.get('extracted_entities', {})
        
        # General suggestions
        if len(query.split()) < 5:
            suggestions.append("Try providing more context for better results")
        
        # Type-specific suggestions
        if query_type == QueryTypes.SQL_RETRIEVAL:
            if not entities.get('dates'):
                suggestions.append("Adding a time range (e.g., 'in 2023' or 'last 6 months') will help find relevant data")
            
            if not entities.get('locations'):
                suggestions.append("Specifying a location or region will narrow down the search")
        
        elif query_type == QueryTypes.VECTOR_RETRIEVAL:
            if 'what' not in query.lower() and 'how' not in query.lower():
                suggestions.append("Starting with 'What' or 'How' often leads to better explanatory responses")
        
        return suggestions
    
    def _detect_geographic_sql_query(self, query: str) -> bool:
        """Detect queries that should use SQL for geographic data"""
        coordinate_patterns = [
            r'near\s+coordinates?\s+\d+[°\s]*[NS]',
            r'profiles?\s+near\s+\d+',
            r'find\s+profiles?\s+near',
            r'latitude\s+between',
            r'longitude\s+between'
        ]
        return any(re.search(pattern, query.lower()) for pattern in coordinate_patterns)
    
    def _is_geographic_query(self, query: str) -> bool:
        """Detect geographic queries that should use SQL"""
        query_lower = query.lower()
        
        geographic_indicators = [
            r'near\s+coordinates?',
            r'coordinates?\s+\d+[°\s]*[NS]',
            r'profiles?\s+near\s+\d+',
            r'find\s+(?:profiles?|floats?)\s+near',
            r'around\s+\d+[°\s]*[NS]',
            r'latitude.*longitude',
            r'\d+[°\s]*[NS].*\d+[°\s]*[EW]',
            r'nearest\s+(?:profiles?|floats?)\s+to\s+coordinates?',
            r'find\s+the\s+nearest\s+(?:profiles?|floats?)\s+to\s+coordinates?',
            r'coordinates?\s+\d+[°\s]*[NS]\s*,\s*\d+[°\s]*[EW]',
            r'nearest.*floats.*coordinates',
            r'find.*nearest.*floats.*coordinates'
        ]
        
        return any(re.search(pattern, query_lower) for pattern in geographic_indicators)
    
    def _detect_visualization_type(self, user_query: str) -> Dict[str, Any]:
        """Detect preferred visualization type from user query"""
        try:
            query_lower = user_query.lower().strip()
            
            # Check for explicit visualization requests
            bar_chart_score = sum(1 for keyword in self.bar_chart_keywords if keyword in query_lower)
            table_score = sum(1 for keyword in self.table_keywords if keyword in query_lower)
            
            # Detect specific chart types
            detected_chart_type = "auto"
            chart_confidence = 0.0
            
            for chart_type, patterns in self.chart_type_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, query_lower):
                        detected_chart_type = chart_type
                        chart_confidence = 0.8
                        break
                if chart_confidence > 0:
                    break
            
            # Determine preferred visualization type
            if bar_chart_score > table_score and bar_chart_score > 0:
                preferred_type = "bar_chart"
                confidence = min(0.9, 0.5 + (bar_chart_score * 0.1))
            elif table_score > bar_chart_score and table_score > 0:
                preferred_type = "data_table"
                confidence = min(0.9, 0.5 + (table_score * 0.1))
            elif chart_confidence > 0:
                preferred_type = "bar_chart"
                confidence = chart_confidence
            else:
                # Auto-detect based on query characteristics
                if any(word in query_lower for word in ['compare', 'comparison', 'vs', 'versus', 'statistics']):
                    preferred_type = "bar_chart"
                    confidence = 0.6
                elif any(word in query_lower for word in ['list', 'show', 'display', 'table', 'detailed']):
                    preferred_type = "data_table"
                    confidence = 0.6
                else:
                    preferred_type = "auto"
                    confidence = 0.3
            
            return {
                "preferred_type": preferred_type,
                "chart_type": detected_chart_type,
                "confidence": confidence,
                "scores": {
                    "bar_chart": bar_chart_score,
                    "table": table_score,
                    "chart_type": chart_confidence
                }
            }
            
        except Exception as e:
            logger.error("Error detecting visualization type", error=str(e))
            return {
                "preferred_type": "auto",
                "chart_type": "auto",
                "confidence": 0.0,
                "scores": {"bar_chart": 0, "table": 0, "chart_type": 0}
            }


# Global query classifier instance
query_classifier = QueryClassifier()