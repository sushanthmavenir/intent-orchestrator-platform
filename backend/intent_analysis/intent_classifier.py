from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import json
import time
import asyncio

from .analyzers.semantic_analyzer import SemanticAnalyzer
from .patterns.pattern_matcher import PatternMatcher
from .llm.models import ClassificationResult, ClassificationMethod, UrgencyLevel
from .llm.providers.groq_provider import GroqProvider
from .llm.providers.base_provider import LLMProviderError
from config.config_loader import config_loader


class IntentClassifier:
    """
    Hybrid intent classification engine that supports:
    - LLM-based classification using Groq API
    - Pattern-based matching using YAML rules
    - Semantic analysis using spaCy NLP (legacy support)
    - Hybrid mode with intelligent fallback
    - TMF 921A compliant output generation
    """
    
    def __init__(self, spacy_model: str = "en_core_web_sm", 
                 patterns_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = config_loader.load_classification_config()
        self.classification_mode = config_loader.get_classification_mode()
        
        # Initialize components based on mode
        try:
            self._init_components(spacy_model, patterns_file)
            self.logger.info(f"Intent classifier initialized successfully in {self.classification_mode} mode")
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
    
    def _init_components(self, spacy_model: str, patterns_file: Optional[str]):
        """Initialize classification components based on configuration"""
        
        # Always initialize pattern matcher as fallback
        self.pattern_matcher = PatternMatcher(patterns_file)
        
        # Initialize semantic analyzer if needed (for legacy pattern mode)
        if self.classification_mode in ['pattern', 'hybrid']:
            try:
                self.semantic_analyzer = SemanticAnalyzer(spacy_model)
            except Exception as e:
                self.logger.warning(f"Failed to initialize semantic analyzer: {e}")
                self.semantic_analyzer = None
        
        # Initialize LLM provider if needed
        if self.classification_mode in ['llm', 'hybrid']:
            try:
                llm_config = config_loader.get_llm_config()
                self.llm_provider = GroqProvider(llm_config)
                
                if not self.llm_provider.is_available():
                    self.logger.warning("LLM provider not available, falling back to pattern mode")
                    self.classification_mode = 'pattern'
            except Exception as e:
                self.logger.warning(f"Failed to initialize LLM provider: {e}")
                self.llm_provider = None
                if self.classification_mode == 'llm':
                    self.classification_mode = 'pattern'
        else:
            self.llm_provider = None
    
    async def classify_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main classification method with hybrid LLM/pattern support
        
        Args:
            text: Input text to classify
            context: Optional context information (user history, session data, etc.)
            
        Returns:
            Comprehensive classification result with intent type, confidence, and extracted data
        """
        self.logger.info(f"Classifying intent ({self.classification_mode} mode) for text: {text[:100]}...")
        start_time = time.time()
        
        try:
            if self.classification_mode == 'llm':
                result = await self._classify_with_llm(text, context)
            elif self.classification_mode == 'hybrid':
                result = await self._classify_hybrid(text, context)
            else:  # pattern mode
                result = self._classify_with_pattern(text, context)
            
            # Add processing time
            result['processing_time_ms'] = int((time.time() - start_time) * 1000)
            
            self.logger.info(f"Classification complete: {result.get('intent_type')} "
                           f"(confidence: {result.get('confidence', 0):.2f}) "
                           f"in {result['processing_time_ms']}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during classification: {e}")
            return self._fallback_classification(text)
    
    async def _classify_with_llm(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify using LLM only"""
        try:
            llm_response = await self.llm_provider.classify_intent(text, context)
            
            # Extract entities using pattern matcher as well for completeness
            pattern_entities = self.pattern_matcher.extract_entities(text)
            
            # Merge LLM entities with pattern entities
            merged_entities = self._merge_entities(llm_response.entities, pattern_entities)
            
            # Generate TMF 921A compliant result
            return self._generate_classification_from_llm_response(
                llm_response, merged_entities, text, context, ClassificationMethod.LLM
            )
            
        except LLMProviderError as e:
            self.logger.warning(f"LLM classification failed: {e}")
            # Fallback to pattern classification
            return self._classify_with_pattern(text, context, fallback_used=True)
    
    async def _classify_hybrid(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify using hybrid approach (LLM primary, pattern fallback)"""
        hybrid_config = config_loader.get_hybrid_config()
        primary_method = hybrid_config.get('primary', 'llm')
        fallback_method = hybrid_config.get('fallback', 'pattern')
        confidence_threshold = hybrid_config.get('confidence_threshold', 0.7)
        
        try:
            # Try primary method first
            if primary_method == 'llm' and self.llm_provider and self.llm_provider.is_available():
                llm_response = await self.llm_provider.classify_intent(text, context)
                self.logger.info(f"LLM primary classification returned intent: {llm_response.intent_type} with confidence: {llm_response.confidence:.2f}")
                # Check if LLM confidence is sufficient
                if llm_response.confidence >= confidence_threshold:
                    pattern_entities = self.pattern_matcher.extract_entities(text)
                    merged_entities = self._merge_entities(llm_response.entities, pattern_entities)
                    
                    return self._generate_classification_from_llm_response(
                        llm_response, merged_entities, text, context, ClassificationMethod.HYBRID
                    )
                else:
                    self.logger.info(f"LLM confidence {llm_response.confidence:.2f} below threshold {confidence_threshold}, using fallback")
            
            # Use fallback method
            if fallback_method == 'pattern':
                return self._classify_with_pattern(text, context, fallback_used=True)
            else:
                # This shouldn't happen with current config, but handle gracefully
                return self._classify_with_pattern(text, context, fallback_used=True)
                
        except LLMProviderError as e:
            self.logger.warning(f"LLM classification failed in hybrid mode: {e}")
            return self._classify_with_pattern(text, context, fallback_used=True)
    
    def _classify_with_pattern(self, text: str, context: Optional[Dict[str, Any]] = None, fallback_used: bool = False) -> Dict[str, Any]:
        """Classify using pattern matching (with optional semantic analysis)"""
        
        # Perform pattern matching
        pattern_result = self.pattern_matcher.match_intent(text)
        pattern_entities = self.pattern_matcher.extract_entities(text)
        
        # Perform semantic analysis if available
        semantic_entities = {}
        if self.semantic_analyzer:
            try:
                semantic_result = self.semantic_analyzer.analyze(text)
                semantic_entities = semantic_result.get('custom_entities', {})
                
                # Combine pattern and semantic results (legacy behavior)
                combined_result = self._combine_results(semantic_result, pattern_result)
            except Exception as e:
                self.logger.warning(f"Semantic analysis failed: {e}")
                combined_result = self._pattern_only_result(pattern_result)
        else:
            combined_result = self._pattern_only_result(pattern_result)
        
        # Merge entity extractions
        merged_entities = self._merge_entities(semantic_entities, pattern_entities)
        
        # Generate final classification
        classification = self._generate_classification(
            combined_result, merged_entities, text, context
        )
        
        # Mark method used and fallback status
        classification['method_used'] = ClassificationMethod.HYBRID.value if fallback_used else ClassificationMethod.PATTERN.value
        classification['fallback_used'] = fallback_used
        
        return classification
    
    def _pattern_only_result(self, pattern_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate result from pattern matching only"""
        pattern_matches = pattern_result.get('matches', {})
        
        if pattern_matches:
            # Find best pattern match
            best_intent = max(pattern_matches.keys(), key=lambda x: pattern_matches[x].get('confidence', 0))
            best_confidence = pattern_matches[best_intent].get('confidence', 0)
        else:
            best_intent = 'general_inquiry'
            best_confidence = 0.5
        
        return {
            'intent_type': best_intent,
            'confidence': best_confidence,
            'all_scores': {best_intent: {'confidence': best_confidence}},
            'semantic_suggestion': None,
            'pattern_best': pattern_result.get('best_match')
        }
    
    def _generate_classification_from_llm_response(self, llm_response, entities: Dict[str, List[str]], 
                                                 original_text: str, context: Optional[Dict[str, Any]], 
                                                 method: ClassificationMethod) -> Dict[str, Any]:
        """Generate classification from LLM response"""
        
        # Map LLM urgency to our urgency levels
        urgency_mapping = {
            'low': 'normal',
            'medium': 'medium', 
            'high': 'high'
        }
        urgency = urgency_mapping.get(llm_response.urgency, 'normal')
        
        # Generate TMF 921A expression
        tmf_expression = self.pattern_matcher.generate_tmf_expression(
            llm_response.intent_type, entities, urgency
        )
        
        # Extract parameters for intent creation
        parameters = self._extract_intent_parameters(
            llm_response.intent_type, entities, urgency, original_text
        )
        
        # Build comprehensive result
        classification = {
            'intent_type': llm_response.intent_type,
            'confidence': llm_response.confidence,
            'confidence_level': self._get_confidence_level(llm_response.confidence),
            'urgency': urgency,
            'entities': entities,
            'parameters': parameters,
            'tmf_expression': tmf_expression,
            'analysis_details': {
                'llm_reasoning': llm_response.reasoning,
                'method_used': method.value,
                'original_text': original_text,
                'requires_human': llm_response.requires_human
            },
            'recommendations': self._generate_recommendations(
                llm_response.intent_type, llm_response.confidence, entities
            ),
            'timestamp': datetime.utcnow().isoformat(),
            'classifier_version': '2.0',
            'method_used': method.value,
            'fallback_used': False
        }
        
        # Add context if provided
        if context:
            classification['context'] = context
        
        return classification
    
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

        # Handle name entities for KYC
        if entities.get('names'):
            full_name = entities['names'][0]
            name_parts = full_name.split(' ', 1)
            parameters['given_name'] = name_parts[0]
            if len(name_parts) > 1:
                parameters['family_name'] = name_parts[1]
            else:
                parameters['family_name'] = ""
            parameters['full_name'] = full_name # Keep full name for general use
        
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
    
    def classify_intent_sync(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synchronous wrapper for classify_intent for backward compatibility"""
        return asyncio.run(self.classify_intent(text, context))
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classifier statistics and health information"""
        stats = {
            'classification_mode': self.classification_mode,
            'semantic_analyzer_available': hasattr(self, 'semantic_analyzer') and self.semantic_analyzer is not None,
            'pattern_matcher_available': hasattr(self, 'pattern_matcher') and self.pattern_matcher is not None,
            'llm_provider_available': hasattr(self, 'llm_provider') and self.llm_provider is not None and self.llm_provider.is_available(),
            'confidence_thresholds': self.confidence_thresholds,
            'weights': self.weights,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add LLM provider details if available
        if hasattr(self, 'llm_provider') and self.llm_provider:
            stats['llm_provider_type'] = 'groq'
            stats['llm_model'] = getattr(self.llm_provider, 'model', 'unknown')
        
        return stats
    
    def get_available_modes(self) -> List[str]:
        """Get list of available classification modes based on initialized components"""
        modes = ['pattern']  # Always available
        
        if hasattr(self, 'llm_provider') and self.llm_provider and self.llm_provider.is_available():
            modes.extend(['llm', 'hybrid'])
        
        return modes