"""
LLM Classification Prompts
==========================

Prompt templates for intent classification using LLMs.
"""

import json
from typing import Dict, Any, Optional


class IntentClassificationPrompts:
    """Prompt templates for intent classification"""
    
    SYSTEM_PROMPT = """You are an expert intent classifier for a fraud detection and customer service system.

Your task is to classify customer messages into specific intent categories:

INTENT CATEGORIES:
1. fraud_detection - Customer reports suspected fraud, scams, or security concerns
2. account_inquiry - General account questions, balance checks, transaction history  
3. technical_support - App issues, login problems, technical difficulties
4. service_request - Request for services, account changes, feature requests
5. complaint - Complaints about service, fees, or experiences
6. general_inquiry - General questions not fitting other categories

FRAUD DETECTION INDICATORS:
- Keywords: "scam", "fraud", "suspicious", "unauthorized", "hacked", "stolen", "phishing"
- Contexts: Unexpected charges, suspicious calls/texts, account compromise, identity theft
- Phrases: "someone called pretending", "received suspicious", "unauthorized transaction"

URGENCY LEVELS:
- high: Immediate security threats, active fraud, account compromise
- medium: Suspicious activity, potential fraud, service issues
- low: General inquiries, routine requests

ENTITY EXTRACTION:
- phone_numbers: Extract any phone numbers mentioned
- amounts: Extract monetary amounts (e.g., "$100", "50 dollars")
- dates: Extract dates and times mentioned
- suspicious_indicators: Extract fraud-related keywords found

OUTPUT FORMAT:
Return ONLY valid JSON with this exact structure:
{
  "intent_type": "category_name",
  "confidence": 0.85,
  "reasoning": "brief explanation of classification decision",
  "entities": {
    "phone_numbers": [],
    "amounts": [],
    "dates": [],
    "suspicious_indicators": []
  },
  "urgency": "low|medium|high",
  "requires_human": true|false
}

IMPORTANT RULES:
- Return ONLY the JSON object, no extra text
- confidence must be between 0.0 and 1.0
- Use exactly the intent categories listed above
- requires_human should be true for high urgency or complex cases
- Keep reasoning concise (max 100 characters)"""

    @staticmethod
    def get_classification_prompt(text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate classification prompt for given text
        
        Args:
            text: User message to classify
            context: Optional context information
            
        Returns:
            Complete prompt for LLM
        """
        prompt = f"""CUSTOMER MESSAGE: "{text}"

CONTEXT: {json.dumps(context or {}, indent=2)}

Classify this message and extract relevant entities. Return only JSON."""
        
        return prompt

    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt"""
        return IntentClassificationPrompts.SYSTEM_PROMPT

    @staticmethod
    def parse_llm_response(response: str) -> Dict[str, Any]:
        """
        Parse LLM response and validate structure
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed and validated response dictionary
            
        Raises:
            ValueError: If response is invalid
        """
        try:
            # Clean response - remove any markdown formatting
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            parsed = json.loads(cleaned_response)
            
            # Validate required fields
            required_fields = ['intent_type', 'confidence', 'reasoning', 'entities', 'urgency', 'requires_human']
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate intent type
            valid_intents = ['fraud_detection', 'account_inquiry', 'technical_support', 
                           'service_request', 'complaint', 'general_inquiry']
            if parsed['intent_type'] not in valid_intents:
                # Default to general_inquiry for unknown types
                parsed['intent_type'] = 'general_inquiry'
            
            # Validate confidence range
            confidence = float(parsed['confidence'])
            if not (0.0 <= confidence <= 1.0):
                parsed['confidence'] = max(0.0, min(1.0, confidence))
            
            # Validate urgency
            valid_urgency = ['low', 'medium', 'high']
            if parsed['urgency'] not in valid_urgency:
                parsed['urgency'] = 'medium'
            
            # Ensure entities is a dict with required keys
            if not isinstance(parsed['entities'], dict):
                parsed['entities'] = {}
            
            entity_keys = ['phone_numbers', 'amounts', 'dates', 'suspicious_indicators']
            for key in entity_keys:
                if key not in parsed['entities']:
                    parsed['entities'][key] = []
                elif not isinstance(parsed['entities'][key], list):
                    parsed['entities'][key] = []
            
            # Ensure boolean fields
            parsed['requires_human'] = bool(parsed['requires_human'])
            
            return parsed
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing LLM response: {e}")