import spacy
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging


class SemanticAnalyzer:
    """
    Semantic analyzer using spaCy for natural language processing
    Extracts entities, patterns, and intent indicators from user messages
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        self.logger = logging.getLogger(__name__)
        try:
            self.nlp = spacy.load(model_name)
            self.logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            self.logger.error(f"Could not load spaCy model: {model_name}")
            self.logger.info("Please install with: python -m spacy download en_core_web_sm")
            raise
        
        # Add custom patterns and rules
        self._setup_custom_patterns()
    
    def _setup_custom_patterns(self):
        """Set up custom entity recognition patterns"""
        
        # Phone number patterns
        self.phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
            r'\+\d{1,3}[-.\s]?\d{1,14}\b',      # International
            r'\b\d{10,15}\b'                    # Generic long numbers
        ]
        
        # Amount/money patterns
        self.money_patterns = [
            r'\$[\d,]+\.?\d*',                  # $1,000.00
            r'USD\s*[\d,]+\.?\d*',              # USD 1000
            r'\b\d+[\s]?(?:dollars?|USD|euros?|EUR|pounds?|GBP)\b',
            r'\b(?:dollars?|USD|euros?|EUR|pounds?|GBP)\s*\d+\b'
        ]
        
        # Account/ID patterns
        self.id_patterns = [
            r'\b(?:customer|user|account)[\s]*(?:id|ID|number)?[\s]*:?[\s]*([A-Za-z0-9]+)\b',
            r'\b([A-Za-z0-9]{6,20})\b(?=\s*(?:account|customer|user))',
            r'\b\d{8,16}\b'  # Generic ID numbers
        ]
        
        # Transaction type keywords
        self.transaction_keywords = {
            'transfer': ['transfer', 'send', 'wire', 'move', 'pay'],
            'withdrawal': ['withdraw', 'cash', 'atm', 'take out'],
            'deposit': ['deposit', 'add', 'put in', 'credit'],
            'purchase': ['buy', 'purchase', 'order', 'shopping'],
            'fraud_indicators': ['suspicious', 'unusual', 'strange', 'fraud', 'scam', 'hack']
        }
        
        # Location indicators
        self.location_keywords = [
            'location', 'country', 'city', 'address', 'where', 'place',
            'abroad', 'overseas', 'international', 'domestic'
        ]
        
        # Urgency indicators
        self.urgency_keywords = [
            'urgent', 'immediate', 'quickly', 'asap', 'emergency',
            'now', 'right away', 'critical', 'priority'
        ]
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Main analysis function that processes text and extracts semantic information
        """
        self.logger.debug(f"Analyzing text: {text[:100]}...")
        
        # Process with spaCy
        doc = self.nlp(text)
        
        # Extract various types of information
        analysis = {
            'original_text': text,
            'processed_tokens': self._extract_tokens(doc),
            'entities': self._extract_entities(doc),
            'custom_entities': self._extract_custom_entities(text),
            'intent_indicators': self._identify_intent_indicators(text, doc),
            'sentiment': self._analyze_sentiment(doc),
            'confidence_scores': {},
            'suggested_intent_type': None,
            'extracted_parameters': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Determine overall intent type and confidence
        analysis['suggested_intent_type'], analysis['confidence_scores'] = self._determine_intent_type(analysis)
        
        # Extract structured parameters for intent creation
        analysis['extracted_parameters'] = self._extract_parameters(analysis)
        
        return analysis
    
    def _extract_tokens(self, doc) -> List[Dict[str, str]]:
        """Extract token information"""
        tokens = []
        for token in doc:
            if not token.is_stop and not token.is_punct and len(token.text) > 2:
                tokens.append({
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'tag': token.tag_,
                    'is_alpha': token.is_alpha
                })
        return tokens
    
    def _extract_entities(self, doc) -> List[Dict[str, str]]:
        """Extract named entities using spaCy's NER"""
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_),
                'start': ent.start_char,
                'end': ent.end_char
            })
        return entities
    
    def _extract_custom_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract custom entities using regex patterns"""
        custom_entities = {
            'phone_numbers': [],
            'amounts': [],
            'ids': [],
            'locations': [],
            'dates_times': []
        }
        
        # Phone numbers
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            custom_entities['phone_numbers'].extend(matches)
        
        # Money amounts
        for pattern in self.money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            custom_entities['amounts'].extend(matches)
        
        # IDs
        for pattern in self.id_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if isinstance(matches, list) and matches:
                custom_entities['ids'].extend([m if isinstance(m, str) else m[0] for m in matches])
        
        return custom_entities
    
    def _identify_intent_indicators(self, text: str, doc) -> Dict[str, Any]:
        """Identify indicators that suggest specific intent types"""
        text_lower = text.lower()
        
        indicators = {
            'fraud_detection': 0,
            'transaction_monitoring': 0,
            'customer_verification': 0,
            'service_assurance': 0,
            'network_optimization': 0
        }
        
        # Fraud detection indicators
        fraud_words = ['fraud', 'suspicious', 'scam', 'hack', 'unauthorized', 'strange', 'unusual']
        for word in fraud_words:
            if word in text_lower:
                indicators['fraud_detection'] += 1
        
        # Transaction monitoring indicators
        transaction_words = ['transaction', 'transfer', 'payment', 'money', 'amount', 'withdraw']
        for word in transaction_words:
            if word in text_lower:
                indicators['transaction_monitoring'] += 1
        
        # Customer verification indicators
        verification_words = ['verify', 'check', 'identity', 'kyc', 'customer', 'account']
        for word in verification_words:
            if word in text_lower:
                indicators['customer_verification'] += 1
        
        # Service assurance indicators
        service_words = ['service', 'network', 'performance', 'quality', 'outage', 'downtime']
        for word in service_words:
            if word in text_lower:
                indicators['service_assurance'] += 1
        
        # Network optimization indicators
        network_words = ['optimize', 'bandwidth', 'latency', 'throughput', 'capacity', 'coverage']
        for word in network_words:
            if word in text_lower:
                indicators['network_optimization'] += 1
        
        return indicators
    
    def _analyze_sentiment(self, doc) -> Dict[str, float]:
        """Basic sentiment analysis"""
        # Simple rule-based sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'fine', 'okay', 'yes', 'sure']
        negative_words = ['bad', 'terrible', 'awful', 'wrong', 'no', 'never', 'problem', 'issue']
        urgent_words = ['urgent', 'emergency', 'critical', 'important', 'asap']
        
        text_lower = doc.text.lower()
        
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        urgent_score = sum(1 for word in urgent_words if word in text_lower)
        
        total_words = len([token for token in doc if not token.is_stop and token.is_alpha])
        
        return {
            'positive': positive_score / max(total_words, 1),
            'negative': negative_score / max(total_words, 1),
            'urgency': urgent_score / max(total_words, 1),
            'neutral': max(0, 1 - (positive_score + negative_score) / max(total_words, 1))
        }
    
    def _determine_intent_type(self, analysis: Dict[str, Any]) -> Tuple[str, Dict[str, float]]:
        """Determine the most likely intent type based on analysis"""
        indicators = analysis['intent_indicators']
        custom_entities = analysis['custom_entities']
        sentiment = analysis['sentiment']
        
        # Calculate confidence scores
        confidence_scores = {}
        
        # Fraud detection confidence
        fraud_score = indicators.get('fraud_detection', 0)
        if custom_entities.get('phone_numbers') or custom_entities.get('amounts'):
            fraud_score += 1
        if sentiment.get('negative', 0) > 0.1 or sentiment.get('urgency', 0) > 0.1:
            fraud_score += 1
        confidence_scores['fraud_detection'] = min(fraud_score / 5.0, 1.0)
        
        # Transaction monitoring confidence
        trans_score = indicators.get('transaction_monitoring', 0)
        if custom_entities.get('amounts') or custom_entities.get('ids'):
            trans_score += 1
        confidence_scores['transaction_monitoring'] = min(trans_score / 4.0, 1.0)
        
        # Customer verification confidence
        verify_score = indicators.get('customer_verification', 0)
        if custom_entities.get('ids'):
            verify_score += 1
        confidence_scores['customer_verification'] = min(verify_score / 3.0, 1.0)
        
        # Service assurance confidence
        service_score = indicators.get('service_assurance', 0)
        confidence_scores['service_assurance'] = min(service_score / 3.0, 1.0)
        
        # Network optimization confidence
        network_score = indicators.get('network_optimization', 0)
        confidence_scores['network_optimization'] = min(network_score / 3.0, 1.0)
        
        # Determine the most likely intent type
        if not confidence_scores:
            return 'general_inquiry', {'general_inquiry': 0.5}
        
        best_intent = max(confidence_scores, key=confidence_scores.get)
        
        # Require minimum confidence threshold
        if confidence_scores[best_intent] < 0.3:
            return 'general_inquiry', confidence_scores
        
        return best_intent, confidence_scores
    
    def _extract_parameters(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured parameters for intent creation"""
        parameters = {}
        
        # Extract customer/account IDs
        if analysis['custom_entities'].get('ids'):
            parameters['customer_id'] = analysis['custom_entities']['ids'][0]
        
        # Extract amounts
        if analysis['custom_entities'].get('amounts'):
            parameters['amount'] = analysis['custom_entities']['amounts'][0]
        
        # Extract phone numbers
        if analysis['custom_entities'].get('phone_numbers'):
            parameters['phone_number'] = analysis['custom_entities']['phone_numbers'][0]
        
        # Extract locations from entities
        locations = [ent['text'] for ent in analysis['entities'] if ent['label'] in ['GPE', 'LOC']]
        if locations:
            parameters['location'] = locations[0]
        
        # Extract urgency level
        urgency_score = analysis['sentiment'].get('urgency', 0)
        if urgency_score > 0.2:
            parameters['priority'] = 'high'
        elif urgency_score > 0.1:
            parameters['priority'] = 'medium'
        else:
            parameters['priority'] = 'normal'
        
        # Extract intent description based on analysis
        intent_type = analysis.get('suggested_intent_type', 'general_inquiry')
        parameters['intent_description'] = self._generate_intent_description(intent_type, parameters)
        
        return parameters
    
    def _generate_intent_description(self, intent_type: str, parameters: Dict[str, Any]) -> str:
        """Generate a human-readable intent description"""
        descriptions = {
            'fraud_detection': f"Detect potential fraud for customer {parameters.get('customer_id', 'unknown')}",
            'transaction_monitoring': f"Monitor transactions for customer {parameters.get('customer_id', 'unknown')}",
            'customer_verification': f"Verify identity for customer {parameters.get('customer_id', 'unknown')}",
            'service_assurance': "Ensure service quality and performance",
            'network_optimization': "Optimize network performance and capacity",
            'general_inquiry': "General customer inquiry or request"
        }
        
        base_description = descriptions.get(intent_type, "Process customer request")
        
        # Add priority information
        priority = parameters.get('priority', 'normal')
        if priority == 'high':
            base_description += " (HIGH PRIORITY)"
        
        return base_description
    
    def extract_entities_for_intent(self, text: str) -> Dict[str, Any]:
        """
        Simplified method to extract entities specifically for intent creation
        """
        analysis = self.analyze(text)
        
        return {
            'intent_type': analysis['suggested_intent_type'],
            'confidence': max(analysis['confidence_scores'].values()) if analysis['confidence_scores'] else 0.5,
            'parameters': analysis['extracted_parameters'],
            'entities': analysis['custom_entities'],
            'sentiment': analysis['sentiment']
        }