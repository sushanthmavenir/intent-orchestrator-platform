import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging


class PatternMatcher:
    """
    Pattern-based intent matching system using YAML configuration
    Combines rule-based patterns with semantic similarity
    """
    
    def __init__(self, patterns_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        if patterns_file is None:
            patterns_file = Path(__file__).parent / "intent_patterns.yaml"
        
        self.patterns_file = patterns_file
        self.patterns = self._load_patterns()
        
        self.logger.info(f"Loaded patterns from: {patterns_file}")
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load patterns from YAML file"""
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as file:
                patterns = yaml.safe_load(file)
                self.logger.info(f"Loaded {len(patterns.get('intent_patterns', {}))} intent patterns")
                return patterns
        except FileNotFoundError:
            self.logger.error(f"Pattern file not found: {self.patterns_file}")
            return self._get_default_patterns()
        except Exception as e:
            self.logger.error(f"Error loading patterns: {e}")
            return self._get_default_patterns()
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """Fallback patterns if file loading fails"""
        return {
            'intent_patterns': {
                'fraud_detection': {
                    'keywords': ['fraud', 'suspicious', 'scam'],
                    'patterns': ['check.*fraud', 'suspicious.*activity'],
                    'confidence_boost': 0.3,
                    'priority': 'high'
                }
            },
            'entity_patterns': {},
            'confidence_thresholds': {'minimum': 0.3, 'medium': 0.6, 'high': 0.8}
        }
    
    def match_intent(self, text: str) -> Dict[str, Any]:
        """
        Match text against intent patterns
        Returns intent matches with confidence scores
        """
        text_lower = text.lower()
        matches = {}
        
        intent_patterns = self.patterns.get('intent_patterns', {})
        
        for intent_type, pattern_config in intent_patterns.items():
            score = self._calculate_intent_score(text_lower, pattern_config)
            
            if score > 0:
                matches[intent_type] = {
                    'confidence': score,
                    'priority': pattern_config.get('priority', 'medium'),
                    'matched_keywords': self._get_matched_keywords(text_lower, pattern_config),
                    'matched_patterns': self._get_matched_patterns(text_lower, pattern_config)
                }
        
        # Sort by confidence
        sorted_matches = dict(sorted(matches.items(), key=lambda x: x[1]['confidence'], reverse=True))
        
        return {
            'matches': sorted_matches,
            'best_match': self._get_best_match(sorted_matches),
            'confidence_threshold_met': self._check_confidence_threshold(sorted_matches)
        }
    
    def _calculate_intent_score(self, text: str, pattern_config: Dict[str, Any]) -> float:
        """Calculate confidence score for an intent pattern"""
        score = 0.0
        
        # Keyword matching
        keywords = pattern_config.get('keywords', [])
        keyword_matches = sum(1 for keyword in keywords if keyword in text)
        keyword_score = (keyword_matches / len(keywords)) if keywords else 0
        
        # Pattern matching (regex)
        patterns = pattern_config.get('patterns', [])
        pattern_matches = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_matches += 1
        pattern_score = (pattern_matches / len(patterns)) if patterns else 0
        
        # Combine scores
        base_score = (keyword_score * 0.6 + pattern_score * 0.4)
        
        # Apply confidence boost
        confidence_boost = pattern_config.get('confidence_boost', 0)
        score = min(base_score + confidence_boost, 1.0)
        
        return score
    
    def _get_matched_keywords(self, text: str, pattern_config: Dict[str, Any]) -> List[str]:
        """Get list of matched keywords"""
        keywords = pattern_config.get('keywords', [])
        return [keyword for keyword in keywords if keyword in text]
    
    def _get_matched_patterns(self, text: str, pattern_config: Dict[str, Any]) -> List[str]:
        """Get list of matched regex patterns"""
        patterns = pattern_config.get('patterns', [])
        matched = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matched.append(pattern)
        return matched
    
    def _get_best_match(self, matches: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the best intent match"""
        if not matches:
            return None
        
        best_intent = next(iter(matches))
        best_score = matches[best_intent]['confidence']
        
        thresholds = self.patterns.get('confidence_thresholds', {})
        min_threshold = thresholds.get('minimum', 0.3)
        
        if best_score >= min_threshold:
            return {
                'intent_type': best_intent,
                'confidence': best_score,
                'priority': matches[best_intent]['priority'],
                'details': matches[best_intent]
            }
        
        return None
    
    def _check_confidence_threshold(self, matches: Dict[str, Any]) -> Dict[str, bool]:
        """Check which confidence thresholds are met"""
        thresholds = self.patterns.get('confidence_thresholds', {})
        
        if not matches:
            return {level: False for level in thresholds.keys()}
        
        best_score = next(iter(matches.values()))['confidence']
        
        return {
            level: best_score >= threshold
            for level, threshold in thresholds.items()
        }
    
    def extract_entities(self, text: str, intent_type: Optional[str] = None) -> Dict[str, List[str]]:
        """Extract entities from text using pattern matching"""
        entity_patterns = self.patterns.get('entity_patterns', {})
        extracted = {}
        
        # If intent type is specified, focus on relevant entities
        relevant_entities = self._get_relevant_entities(intent_type) if intent_type else entity_patterns.keys()
        
        for entity_name in relevant_entities:
            if entity_name not in entity_patterns:
                continue
                
            entity_config = entity_patterns[entity_name]
            patterns = entity_config.get('patterns', [])
            matches = []
            
            for pattern in patterns:
                regex_matches = re.findall(pattern, text, re.IGNORECASE)
                if regex_matches:
                    # Handle both group and non-group matches
                    for match in regex_matches:
                        if isinstance(match, tuple):
                            matches.extend([m for m in match if m])
                        else:
                            matches.append(match)
            
            # Validate extracted entities
            validated_matches = self._validate_entities(matches, entity_config)
            if validated_matches:
                extracted[entity_name] = validated_matches
        
        return extracted
    
    def _get_relevant_entities(self, intent_type: str) -> List[str]:
        """Get entities relevant to a specific intent type"""
        intent_mapping = self.patterns.get('intent_mapping', {})
        
        if intent_type not in intent_mapping:
            return []
        
        mapping = intent_mapping[intent_type]
        required = mapping.get('required_entities', [])
        optional = mapping.get('optional_entities', [])
        
        return required + optional
    
    def _validate_entities(self, matches: List[str], entity_config: Dict[str, Any]) -> List[str]:
        """Validate extracted entities against configuration rules"""
        validation = entity_config.get('validation', {})
        validated = []
        
        for match in matches:
            valid = True
            
            # Check length constraints
            min_length = validation.get('min_length')
            max_length = validation.get('max_length')
            
            if min_length and len(match) < min_length:
                valid = False
            if max_length and len(match) > max_length:
                valid = False
            
            # Check value constraints
            min_value = validation.get('min_value')
            if min_value is not None:
                try:
                    value = float(re.sub(r'[^0-9.]', '', match))
                    if value < min_value:
                        valid = False
                except ValueError:
                    pass
            
            if valid:
                validated.append(match)
        
        return validated
    
    def get_urgency_level(self, text: str) -> str:
        """Determine urgency level from text"""
        text_lower = text.lower()
        urgency_indicators = self.patterns.get('urgency_indicators', {})
        
        for level in ['high', 'medium', 'low']:
            indicators = urgency_indicators.get(level, [])
            if any(indicator in text_lower for indicator in indicators):
                return level
        
        return 'normal'
    
    def generate_tmf_expression(self, intent_type: str, entities: Dict[str, List[str]], 
                              urgency: str = 'normal') -> Dict[str, Any]:
        """Generate TMF 921A compliant expression from intent and entities"""
        intent_mapping = self.patterns.get('intent_mapping', {})
        
        if intent_type not in intent_mapping:
            expression_type = 'generic_intent'
        else:
            expression_type = intent_mapping[intent_type]['expression_type']
        
        # Build JSON-LD expression
        expression = {
            "@context": {
                "tio": "https://tmforum.org/ontology/",
                "camara": "https://camara-project.org/ontology/"
            },
            "@type": f"tio:{expression_type}",
            "tio:priority": urgency,
            "tio:timestamp": "{{current_timestamp}}",
            "tio:entities": {}
        }
        
        # Add extracted entities
        for entity_name, values in entities.items():
            if values:
                key = f"tio:{entity_name}"
                expression["tio:entities"][key] = values[0] if len(values) == 1 else values
        
        return {
            "expressionLanguage": "JSON-LD",
            "@type": "JsonLdExpression",
            "expressionValue": yaml.dump(expression, default_flow_style=False),
            "iri": f"urn:tmf:intent:{expression_type}"
        }
    
    def reload_patterns(self) -> bool:
        """Reload patterns from file"""
        try:
            self.patterns = self._load_patterns()
            self.logger.info("Patterns reloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload patterns: {e}")
            return False