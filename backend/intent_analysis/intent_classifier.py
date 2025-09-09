from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import json

from .analyzers.semantic_analyzer import SemanticAnalyzer
from .patterns.pattern_matcher import PatternMatcher


class IntentClassifier:
    """
    Comprehensive intent classification engine that combines:
    - Semantic analysis using spaCy NLP
    - Pattern-based matching using YAML rules
    - Confidence scoring and validation
    - TMF 921A compliant output generation
    """
    
    def __init__(self, spacy_model: str = "en_core_web_sm", 
                 patterns_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        try:
            self.semantic_analyzer = SemanticAnalyzer(spacy_model)
            self.pattern_matcher = PatternMatcher(patterns_file)
            self.logger.info("Intent classifier initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize intent classifier: {e}")
            raise
        
        # Classification thresholds
        self.confidence_thresholds = {
            'minimum': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        
        # Weight factors for combining different analysis methods
        self.weights = {
            'semantic_analysis': 0.6,
            'pattern_matching': 0.4
        }
    
    def classify_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main classification method that combines semantic and pattern analysis
        
        Args:
            text: Input text to classify
            context: Optional context information (user history, session data, etc.)
            
        Returns:
            Comprehensive classification result with intent type, confidence, and extracted data
        """
        self.logger.info(f"Classifying intent for text: {text[:100]}...")
        
        try:
            # Perform semantic analysis
            semantic_result = self.semantic_analyzer.analyze(text)
            
            # Perform pattern matching
            pattern_result = self.pattern_matcher.match_intent(text)
            
            # Extract entities using both methods
            semantic_entities = semantic_result.get('custom_entities', {})
            pattern_entities = self.pattern_matcher.extract_entities(text)
            
            # Combine and score results
            combined_result = self._combine_results(semantic_result, pattern_result)
            
            # Merge entity extractions
            merged_entities = self._merge_entities(semantic_entities, pattern_entities)
            
            # Generate final classification
            classification = self._generate_classification(
                combined_result, merged_entities, text, context
            )
            
            self.logger.info(f"Classification complete: {classification.get('intent_type')} "
                           f"(confidence: {classification.get('confidence', 0):.2f})")
            
            return classification
            
        except Exception as e:
            self.logger.error(f"Error during classification: {e}")
            return self._fallback_classification(text)
    
    def _combine_results(self, semantic_result: Dict[str, Any], 
                        pattern_result: Dict[str, Any]) -> Dict[str, Any]:
        """Combine semantic analysis and pattern matching results"""
        
        # Get confidence scores from semantic analysis
        semantic_scores = semantic_result.get('confidence_scores', {})
        semantic_intent = semantic_result.get('suggested_intent_type')
        
        # Get confidence scores from pattern matching
        pattern_matches = pattern_result.get('matches', {})
        
        # Combine confidence scores
        combined_scores = {}
        all_intents = set(semantic_scores.keys()) | set(pattern_matches.keys())
        
        for intent_type in all_intents:
            semantic_confidence = semantic_scores.get(intent_type, 0)
            pattern_confidence = pattern_matches.get(intent_type, {}).get('confidence', 0)
            
            # Weighted combination
            combined_confidence = (
                semantic_confidence * self.weights['semantic_analysis'] +
                pattern_confidence * self.weights['pattern_matching']
            )
            
            combined_scores[intent_type] = {
                'confidence': combined_confidence,
                'semantic_confidence': semantic_confidence,
                'pattern_confidence': pattern_confidence,
                'priority': pattern_matches.get(intent_type, {}).get('priority', 'medium')
            }
        
        # Find best match
        if combined_scores:
            best_intent = max(combined_scores.keys(), key=lambda x: combined_scores[x]['confidence'])
            best_confidence = combined_scores[best_intent]['confidence']
        else:
            best_intent = 'general_inquiry'
            best_confidence = 0.5
        
        return {
            'intent_type': best_intent,
            'confidence': best_confidence,
            'all_scores': combined_scores,
            'semantic_suggestion': semantic_intent,
            'pattern_best': pattern_result.get('best_match')
        }
    
    def _merge_entities(self, semantic_entities: Dict[str, List[str]], 
                       pattern_entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Merge entity extractions from different methods"""
        merged = {}
        
        # Get all entity types
        all_entity_types = set(semantic_entities.keys()) | set(pattern_entities.keys())
        
        for entity_type in all_entity_types:
            semantic_values = semantic_entities.get(entity_type, [])
            pattern_values = pattern_entities.get(entity_type, [])
            
            # Combine and deduplicate
            all_values = semantic_values + pattern_values
            unique_values = list(dict.fromkeys(all_values))  # Preserve order while deduplicating
            
            if unique_values:
                merged[entity_type] = unique_values
        
        return merged
    
    def _generate_classification(self, combined_result: Dict[str, Any], 
                               entities: Dict[str, List[str]], 
                               original_text: str,
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate final classification result"""
        
        intent_type = combined_result['intent_type']
        confidence = combined_result['confidence']
        
        # Determine confidence level
        confidence_level = self._get_confidence_level(confidence)
        
        # Get urgency level
        urgency = self.pattern_matcher.get_urgency_level(original_text)
        
        # Generate TMF 921A expression
        tmf_expression = self.pattern_matcher.generate_tmf_expression(
            intent_type, entities, urgency
        )
        
        # Extract parameters for intent creation
        parameters = self._extract_intent_parameters(
            intent_type, entities, urgency, original_text
        )
        
        # Build comprehensive result
        classification = {
            'intent_type': intent_type,
            'confidence': confidence,
            'confidence_level': confidence_level,
            'urgency': urgency,
            'entities': entities,
            'parameters': parameters,
            'tmf_expression': tmf_expression,
            'analysis_details': {
                'semantic_scores': combined_result.get('all_scores', {}),
                'pattern_matches': combined_result.get('pattern_best'),
                'original_text': original_text
            },
            'recommendations': self._generate_recommendations(intent_type, confidence, entities),
            'timestamp': datetime.utcnow().isoformat(),
            'classifier_version': '1.0'
        }
        
        # Add context if provided
        if context:
            classification['context'] = context
        
        return classification
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Map confidence score to level"""
        if confidence >= self.confidence_thresholds['high']:
            return 'high'
        elif confidence >= self.confidence_thresholds['medium']:
            return 'medium'
        elif confidence >= self.confidence_thresholds['minimum']:
            return 'low'
        else:
            return 'very_low'
    
    def _extract_intent_parameters(self, intent_type: str, entities: Dict[str, List[str]], 
                                 urgency: str, original_text: str) -> Dict[str, Any]:
        """Extract parameters for TMF 921A intent creation"""
        parameters = {
            'name': f"{intent_type.replace('_', ' ').title()} Intent",
            'description': f"Auto-generated intent for {intent_type}",
            'lifecycleStatus': 'created',
            'priority': self._map_urgency_to_priority(urgency),
            'source': 'chat_interface',
            'original_request': original_text
        }
        
        # Add entity-specific parameters
        if entities.get('customer_id'):
            parameters['customer_id'] = entities['customer_id'][0]
        
        if entities.get('phone_numbers'):
            parameters['phone_number'] = entities['phone_numbers'][0]
        
        if entities.get('amounts'):
            parameters['amount'] = entities['amounts'][0]
        
        if entities.get('ids'):
            parameters['reference_id'] = entities['ids'][0]
        
        # Intent-specific parameters
        if intent_type == 'fraud_detection':
            parameters['detection_threshold'] = 0.8
            parameters['analysis_scope'] = 'comprehensive'
        elif intent_type == 'transaction_monitoring':
            parameters['monitoring_period'] = '24h'
            parameters['alert_threshold'] = 'medium'
        elif intent_type == 'customer_verification':
            parameters['verification_level'] = 'standard'
            parameters['required_documents'] = ['id', 'proof_of_address']
        
        return parameters
    
    def _map_urgency_to_priority(self, urgency: str) -> str:
        """Map urgency level to TMF 921A priority"""
        mapping = {
            'high': '1-critical',
            'medium': '2-high',
            'low': '3-medium',
            'normal': '4-low'
        }
        return mapping.get(urgency, '4-low')
    
    def _generate_recommendations(self, intent_type: str, confidence: float, 
                                entities: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on classification"""
        recommendations = []
        
        # Confidence-based recommendations
        if confidence < self.confidence_thresholds['minimum']:
            recommendations.append({
                'type': 'clarification_needed',
                'message': 'Intent classification confidence is low. Consider asking for clarification.',
                'action': 'request_clarification'
            })
        
        # Intent-specific recommendations
        if intent_type == 'fraud_detection':
            recommendations.append({
                'type': 'security_alert',
                'message': 'Potential fraud detected. Initiate security protocols.',
                'action': 'escalate_security_team'
            })
            
            if not entities.get('customer_id'):
                recommendations.append({
                    'type': 'missing_data',
                    'message': 'Customer ID not found. Request customer identification.',
                    'action': 'request_customer_id'
                })
        
        elif intent_type == 'transaction_monitoring':
            if entities.get('amounts'):
                recommendations.append({
                    'type': 'transaction_review',
                    'message': f"Review transaction of {entities['amounts'][0]}",
                    'action': 'review_transaction'
                })
        
        # Entity-based recommendations
        if entities.get('phone_numbers'):
            recommendations.append({
                'type': 'device_check',
                'message': 'Phone number detected. Consider device verification.',
                'action': 'verify_device'
            })
        
        return recommendations
    
    def _fallback_classification(self, text: str) -> Dict[str, Any]:
        """Fallback classification when main process fails"""
        return {
            'intent_type': 'general_inquiry',
            'confidence': 0.5,
            'confidence_level': 'medium',
            'urgency': 'normal',
            'entities': {},
            'parameters': {
                'name': 'General Inquiry Intent',
                'description': 'Fallback intent for unclassified requests',
                'lifecycleStatus': 'created',
                'priority': '4-low',
                'source': 'chat_interface',
                'original_request': text
            },
            'tmf_expression': {
                'expressionLanguage': 'JSON-LD',
                '@type': 'JsonLdExpression',
                'expressionValue': '{"@type": "tio:general_inquiry_intent"}',
                'iri': 'urn:tmf:intent:general_inquiry_intent'
            },
            'analysis_details': {
                'error': 'Classification failed, using fallback',
                'original_text': text
            },
            'recommendations': [{
                'type': 'manual_review',
                'message': 'Automatic classification failed. Manual review recommended.',
                'action': 'escalate_human_agent'
            }],
            'timestamp': datetime.utcnow().isoformat(),
            'classifier_version': '1.0'
        }
    
    def validate_classification(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance classification result"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check required fields
        required_fields = ['intent_type', 'confidence', 'entities', 'parameters']
        for field in required_fields:
            if field not in classification:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Check confidence bounds
        confidence = classification.get('confidence', 0)
        if not 0 <= confidence <= 1:
            validation_result['errors'].append(f"Invalid confidence value: {confidence}")
            validation_result['is_valid'] = False
        
        # Check for low confidence
        if confidence < self.confidence_thresholds['minimum']:
            validation_result['warnings'].append("Low confidence classification")
        
        # Intent-specific validations
        intent_type = classification.get('intent_type')
        entities = classification.get('entities', {})
        
        if intent_type == 'fraud_detection' and not entities.get('customer_id'):
            validation_result['warnings'].append("Fraud detection without customer ID")
        
        classification['validation'] = validation_result
        return classification
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classifier statistics and health information"""
        return {
            'semantic_analyzer_available': hasattr(self, 'semantic_analyzer'),
            'pattern_matcher_available': hasattr(self, 'pattern_matcher'),
            'confidence_thresholds': self.confidence_thresholds,
            'weights': self.weights,
            'timestamp': datetime.utcnow().isoformat()
        }