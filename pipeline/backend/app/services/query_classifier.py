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
            'exact', 'specific', 'precise', 'data', 'values', 'measurements'
        ]
        
        self.vector_keywords = [
            'summarize', 'describe', 'explain', 'patterns', 'trends',
            'characteristics', 'overview', 'general', 'typical', 'average',
            'variations', 'changes', 'analysis', 'insights', 'understand'
        ]
        
        self.hybrid_keywords = [
            'compare', 'analyze', 'relationship', 'correlation', 'impact',
            'influence', 'effect', 'difference', 'similar', 'contrast'
        ]
        
        # Geographic patterns
        self.location_patterns = [
            r'near\s+(?:the\s+)?equator',
            r'in\s+the\s+(\w+\s+\w+|\w+)\s+(?:ocean|sea)',
            r'around\s+(\d+\.?\d*)[°\s]*[NS]\s*,?\s*(\d+\.?\d*)[°\s]*[EW]',
            r'latitude\s+(\d+\.?\d*)',
            r'longitude\s+(\d+\.?\d*)',
            r'arabian\s+sea', r'bay\s+of\s+bengal', r'indian\s+ocean',
            r'pacific\s+ocean', r'atlantic\s+ocean', r'southern\s+ocean'
        ]
        
        # Date patterns
        self.date_patterns = [
            r'in\s+(\w+\s+\d{4})',  # March 2023
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2023-03-15
            r'last\s+(\d+)\s+(days?|weeks?|months?|years?)',
            r'past\s+(\d+)\s+(days?|weeks?|months?|years?)',
            r'since\s+(\w+\s+\d{4}|\d{4})',
            r'between\s+(\w+\s+\d{4})\s+and\s+(\w+\s+\d{4})'
        ]
        
        # Parameter patterns
        self.parameter_patterns = {
            'temperature': r'temperature|temp|thermal',
            'salinity': r'salinity|salt|halocline',
            'dissolved_oxygen': r'dissolved\s+oxygen|oxygen|o2|do',
            'ph': r'ph|acidity|alkalinity',
            'nitrate': r'nitrate|nitrogen|no3',
            'chlorophyll': r'chlorophyll|chl|phytoplankton|algae',
            'pressure': r'pressure|depth|deep',
            'bgc': r'bgc|biogeochemical|biochemical|bio'
        }
    
    def classify_query(self, user_query: str) -> Dict[str, Any]:
        if self._detect_geographic_sql_query(user_query):
            return {
                "query_type": "sql_retrieval",
                "confidence": 0.9,
                "reasoning": "Geographic coordinate query detected",
                "extracted_entities": self._extract_entities(user_query)
            }
        """Main classification method"""
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
            
            logger.info("Query classified", 
                       query=user_query, 
                       type=final_result['query_type'],
                       confidence=final_result['confidence'])
            
            return final_result
            
        except Exception as e:
            logger.error("Query classification failed", query=user_query, error=str(e))
            # Fallback classification
            return {
                "query_type": QueryTypes.VECTOR_RETRIEVAL,
                "confidence": 0.3,
                "reasoning": f"Classification failed: {str(e)}",
                "extracted_entities": {},
                "preprocessing_suggestions": []
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
            r'find\s+profiles?\s+near',
            r'around\s+\d+[°\s]*[NS]',
            r'latitude.*longitude',
            r'\d+[°\s]*[NS].*\d+[°\s]*[EW]'
        ]
        
        return any(re.search(pattern, query_lower) for pattern in geographic_indicators)


# Global query classifier instance
query_classifier = QueryClassifier()