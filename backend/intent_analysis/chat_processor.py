"""
Chat Message to Intent Processing Engine
========================================

Processes raw chat messages into TMF 921A compliant intents with analysis and workflow triggering.
"""

import uuid
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import logging
from .intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)


class ChatMessageProcessor:
    """Processes chat messages into structured intents with analysis"""
    
    def __init__(self):
        # Initialize the hybrid IntentClassifier
        self.intent_classifier = IntentClassifier()
        
        self.fraud_indicators = [
            'scam', 'fraud', 'suspicious', 'bank', 'verify', 'urgent', 'immediately',
            'account', 'security', 'identity', 'confirm', 'authorize', 'password',
            'ssn', 'social security', 'credit card', 'pin', 'suspicious activity',
            'unusual activity', 'locked account', 'verify identity'
        ]
        
        # Keep legacy patterns as fallback
        self.intent_patterns = {
            'fraud_detection': {
                'keywords': ['fraud', 'scam', 'suspicious', 'fake', 'imposter', 'phishing'],
                'confidence_threshold': 0.7
            },
            'security_concern': {
                'keywords': ['security', 'breach', 'hacked', 'compromised', 'protect'],
                'confidence_threshold': 0.6
            },
            'identity_verification': {
                'keywords': ['verify', 'confirm', 'identity', 'authenticate', 'validation'],
                'confidence_threshold': 0.6
            },
            'transaction_inquiry': {
                'keywords': ['transaction', 'payment', 'transfer', 'charge', 'withdrawal'],
                'confidence_threshold': 0.5
            },
            'general_inquiry': {
                'keywords': ['help', 'support', 'question', 'information', 'assistance'],
                'confidence_threshold': 0.3
            }
        }
    
    async def process_chat_message(self, chat_message: str, user_id: str = "User") -> Dict[str, Any]:
        """
        Process raw chat message into TMF 921A intent with analysis
        
        Args:
            chat_message: Raw user chat message
            user_id: User identifier
            
        Returns:
            Complete processing result with intent, analysis, and workflow info
        """
        try:
            # Step 1: Create TMF 921A intent from chat message
            intent = await self.create_intent_from_chat(chat_message, user_id)
            
            # Step 2: Analyze the chat message for patterns and entities
            analysis = await self.analyze_chat_content(chat_message)
            
            # Step 3: Update intent with analysis results
            enriched_intent = await self.enrich_intent_with_analysis(intent, analysis)
            
            # Step 4: Determine workflow and processing steps
            workflow_plan = await self.plan_workflow_execution(enriched_intent, analysis)
            
            return {
                "status": "success",
                "intent": enriched_intent,
                "analysis": analysis,
                "workflow": workflow_plan,
                "processing_steps": [
                    {"step": "intent_created", "status": "completed", "timestamp": datetime.utcnow().isoformat()},
                    {"step": "content_analyzed", "status": "completed", "timestamp": datetime.utcnow().isoformat()},
                    {"step": "workflow_planned", "status": "completed", "timestamp": datetime.utcnow().isoformat()},
                    {"step": "ready_for_execution", "status": "pending", "timestamp": datetime.utcnow().isoformat()}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def create_intent_from_chat(self, chat_message: str, user_id: str) -> Dict[str, Any]:
        """Create TMF 921A compliant intent from chat message"""
        
        intent_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Extract basic info from chat message for intent naming
        intent_name = await self.generate_intent_name(chat_message)
        description = await self.generate_intent_description(chat_message)
        
        # Create expression with chat message as expressionValue
        expression_value = {
            "rawInput": chat_message,
            "inputType": "natural_language",
            "timestamp": timestamp,
            "userId": user_id,
            "processingRequired": True
        }
        
        intent = {
            "id": intent_id,
            "href": f"/tmf-api/intent/v4/intent/{intent_id}",
            "name": intent_name,
            "description": description,
            "creation_date": timestamp,
            "last_update": timestamp,
            "status_change_date": timestamp,
            "lifecycle_status": "analyzing",
            "version": "1.0",
            "expression": {
                "expressionLanguage": "JSON-LD",
                "expressionValue": json.dumps(expression_value)
            },
            "category": "chat_originated",
            "priority": 1,
            "validFor": {
                "startDateTime": timestamp
            }
        }
        
        return intent
    
    async def analyze_chat_content(self, chat_message: str) -> Dict[str, Any]:
        """Analyze chat message content for patterns, entities, and intent classification"""
        
        analysis = {
            "intent_classification": await self.classify_intent(chat_message),
            "entities": await self.extract_entities(chat_message),
            "fraud_indicators": await self.detect_fraud_indicators(chat_message),
            "urgency_level": await self.assess_urgency(chat_message),
            "confidence_score": 0.0,
            "processing_notes": []
        }
        
        # Calculate overall confidence based on all factors
        analysis["confidence_score"] = await self.calculate_confidence(analysis)
        
        return analysis
    
    async def classify_intent(self, chat_message: str) -> Dict[str, Any]:
        """Classify the intent type using the hybrid IntentClassifier"""
        
        try:
            # Use the hybrid IntentClassifier
            classification_result = await self.intent_classifier.classify_intent(chat_message)
            
            return {
                "primary_intent": classification_result["intent_type"],
                "confidence": classification_result["confidence"],
                "urgency": classification_result["urgency"],
                "entities": classification_result["entities"],
                "method_used": classification_result.get("method_used", "unknown"),
                "fallback_used": classification_result.get("fallback_used", False),
                "processing_time_ms": classification_result.get("processing_time_ms", 0),
                "llm_reasoning": classification_result.get("analysis_details", {}).get("llm_reasoning"),
                "full_classification": classification_result
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid classification, falling back to simple pattern matching: {e}")
            # Fallback to simple pattern matching
            return await self._classify_intent_fallback(chat_message)
    
    async def _classify_intent_fallback(self, chat_message: str) -> Dict[str, Any]:
        """Fallback classification using simple pattern matching"""
        
        message_lower = chat_message.lower()
        scores = {}
        
        for intent_type, config in self.intent_patterns.items():
            score = 0.0
            keywords_found = []
            
            for keyword in config['keywords']:
                if keyword in message_lower:
                    score += 1.0 / len(config['keywords'])
                    keywords_found.append(keyword)
            
            scores[intent_type] = {
                "score": score,
                "keywords_found": keywords_found,
                "meets_threshold": score >= config['confidence_threshold']
            }
        
        # Find the highest scoring intent type
        best_match = max(scores.items(), key=lambda x: x[1]["score"])
        
        return {
            "primary_intent": best_match[0],
            "confidence": best_match[1]["score"],
            "keywords_matched": best_match[1]["keywords_found"],
            "all_scores": scores,
            "method_used": "fallback_pattern",
            "fallback_used": True
        }
    
    async def extract_entities(self, chat_message: str) -> Dict[str, List[str]]:
        """Extract entities like phone numbers, amounts, dates from chat message"""
        
        entities = {
            "phone_numbers": [],
            "amounts": [],
            "dates": [],
            "urls": [],
            "emails": [],
            "account_numbers": []
        }
        
        # Phone numbers
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        entities["phone_numbers"] = re.findall(phone_pattern, chat_message)
        
        # Dollar amounts
        amount_pattern = r'\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        entities["amounts"] = re.findall(amount_pattern, chat_message)
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities["emails"] = re.findall(email_pattern, chat_message)
        
        # URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        entities["urls"] = re.findall(url_pattern, chat_message)
        
        return entities
    
    async def detect_fraud_indicators(self, chat_message: str) -> Dict[str, Any]:
        """Detect fraud/scam indicators in the message"""
        
        message_lower = chat_message.lower()
        indicators_found = []
        
        for indicator in self.fraud_indicators:
            if indicator in message_lower:
                indicators_found.append(indicator)
        
        # Additional fraud patterns
        fraud_patterns = {
            "urgency_language": ["urgent", "immediately", "right now", "expire", "within", "minutes"],
            "authority_impersonation": ["bank", "government", "IRS", "police", "security department"],
            "information_requests": ["verify", "confirm", "provide", "give me", "tell me", "what is"],
            "threat_language": ["suspend", "close", "locked", "frozen", "cancelled"]
        }
        
        pattern_matches = {}
        for pattern_name, keywords in fraud_patterns.items():
            matches = [kw for kw in keywords if kw in message_lower]
            if matches:
                pattern_matches[pattern_name] = matches
        
        risk_score = len(indicators_found) * 0.2 + len(pattern_matches) * 0.15
        risk_level = "low"
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        
        return {
            "indicators_found": indicators_found,
            "pattern_matches": pattern_matches,
            "risk_score": min(risk_score, 1.0),
            "risk_level": risk_level
        }
    
    async def assess_urgency(self, chat_message: str) -> Dict[str, Any]:
        """Assess urgency level of the message"""
        
        urgency_keywords = {
            "high": ["urgent", "emergency", "immediately", "now", "asap", "critical"],
            "medium": ["soon", "quickly", "fast", "important", "priority"],
            "low": ["when possible", "sometime", "eventually", "convenient"]
        }
        
        message_lower = chat_message.lower()
        urgency_score = 0
        level = "low"
        
        for level_name, keywords in urgency_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    if level_name == "high":
                        urgency_score = max(urgency_score, 3)
                        level = "high"
                    elif level_name == "medium":
                        urgency_score = max(urgency_score, 2)
                        if level != "high":
                            level = "medium"
        
        return {
            "level": level,
            "score": urgency_score,
            "indicators": [kw for level_kws in urgency_keywords.values() for kw in level_kws if kw in message_lower]
        }
    
    async def calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the analysis"""
        
        intent_confidence = analysis["intent_classification"]["confidence"]
        entity_bonus = 0.1 * len([v for v in analysis["entities"].values() if v])
        fraud_factor = analysis["fraud_indicators"]["risk_score"]
        
        confidence = (intent_confidence + entity_bonus + fraud_factor * 0.3) / 2
        return min(confidence, 1.0)
    
    async def enrich_intent_with_analysis(self, intent: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich the intent with analysis results"""
        
        # Update intent based on analysis
        intent["lifecycle_status"] = "classified"
        intent["last_update"] = datetime.utcnow().isoformat()
        
        # Add analysis metadata
        if "metadata" not in intent:
            intent["metadata"] = {}
        
        intent["metadata"]["analysis"] = {
            "primary_intent": analysis["intent_classification"]["primary_intent"],
            "confidence_score": analysis["confidence_score"],
            "entities_found": analysis["entities"],
            "fraud_risk_level": analysis["fraud_indicators"]["risk_level"],
            "urgency_level": analysis["urgency_level"]["level"]
        }
        
        return intent
    
    async def plan_workflow_execution(self, intent: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Plan workflow execution based on intent and analysis"""
        
        primary_intent = analysis["intent_classification"]["primary_intent"]
        risk_level = analysis["fraud_indicators"]["risk_level"]
        
        workflow_plan = {
            "workflow_type": primary_intent,
            "execution_priority": "normal",
            "required_agents": [],
            "estimated_duration": "2-5 minutes",
            "steps": []
        }
        
        # Determine agents and steps based on intent type
        if primary_intent == "fraud_detection":
            workflow_plan["required_agents"] = ["fraud_detection", "sim_swap", "kyc_match", "scam_signal"]
            workflow_plan["steps"] = [
                {"step": "sim_swap_check", "agent": "sim_swap", "status": "pending"},
                {"step": "device_location_analysis", "agent": "location", "status": "pending"},
                {"step": "identity_verification", "agent": "kyc_match", "status": "pending"},
                {"step": "communication_analysis", "agent": "scam_signal", "status": "pending"},
                {"step": "risk_assessment", "agent": "fraud_detection", "status": "pending"}
            ]
            
        elif primary_intent == "security_concern":
            workflow_plan["required_agents"] = ["fraud_detection", "kyc_match"]
            workflow_plan["steps"] = [
                {"step": "security_assessment", "agent": "fraud_detection", "status": "pending"},
                {"step": "identity_verification", "agent": "kyc_match", "status": "pending"}
            ]
        
        # Adjust priority based on risk level
        if risk_level == "high":
            workflow_plan["execution_priority"] = "high"
            workflow_plan["estimated_duration"] = "1-3 minutes"
        
        return workflow_plan
    
    async def generate_intent_name(self, chat_message: str) -> str:
        """Generate a descriptive intent name from chat message"""
        
        # Truncate and clean message for name
        clean_message = re.sub(r'[^\w\s]', '', chat_message).strip()
        words = clean_message.split()
        
        if len(words) <= 5:
            name_base = ' '.join(words)
        else:
            name_base = ' '.join(words[:5])
        
        return f"Chat Intent: {name_base.title()}"
    
    async def generate_intent_description(self, chat_message: str) -> str:
        """Generate intent description from chat message"""
        
        return f"Intent created from user chat message: '{chat_message[:100]}{'...' if len(chat_message) > 100 else ''}'"