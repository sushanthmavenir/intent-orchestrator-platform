"""
Groq LLM Provider
=================

Free-tier LLM provider using Groq API for intent classification.
"""

import aiohttp
import json
import logging
from typing import Dict, Any, Optional

from .base_provider import BaseLLMProvider, LLMProviderError
from ..models import LLMResponse
from ..prompts import IntentClassificationPrompts


class GroqProvider(BaseLLMProvider):
    """Groq API provider for intent classification"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.groq.com/openai/v1')
        self.model = config.get('model', 'llama-3.1-8b-instant')
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            self.logger.warning("Groq API key not provided - provider will be unavailable")
    
    async def classify_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """
        Classify intent using Groq API
        
        Args:
            text: User message to classify
            context: Optional context information
            
        Returns:
            LLMResponse with classification result
            
        Raises:
            LLMProviderError: If API call fails
        """
        if not self.api_key:
            raise LLMProviderError("Groq API key not configured", "groq", "no_api_key")
        
        try:
            # Prepare messages
            system_prompt = IntentClassificationPrompts.get_system_prompt()
            user_prompt = IntentClassificationPrompts.get_classification_prompt(text, context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "response_format": {"type": "json_object"}
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Groq API error {response.status}: {error_text}")
                        raise LLMProviderError(
                            f"Groq API returned {response.status}: {error_text}",
                            "groq",
                            str(response.status)
                        )
                    
                    result = await response.json()
                    return self._parse_groq_response(result, text)
        
        except aiohttp.ClientError as e:
            self.logger.error(f"Groq API client error: {e}")
            raise LLMProviderError(f"Network error: {e}", "groq", "network_error")
        
        except Exception as e:
            self.logger.error(f"Unexpected error in Groq provider: {e}")
            raise LLMProviderError(f"Unexpected error: {e}", "groq", "unexpected_error")
    
    def _parse_groq_response(self, response: Dict[str, Any], original_text: str) -> LLMResponse:
        """
        Parse Groq API response into LLMResponse
        
        Args:
            response: Raw Groq API response
            original_text: Original user text for fallback
            
        Returns:
            LLMResponse object
        """
        try:
            # Extract content from response
            choices = response.get('choices', [])
            if not choices:
                raise LLMProviderError("No choices in Groq response", "groq", "invalid_response")
            
            content = choices[0].get('message', {}).get('content', '')
            if not content:
                raise LLMProviderError("Empty content in Groq response", "groq", "empty_response")
            
            # Parse the JSON content
            parsed = IntentClassificationPrompts.parse_llm_response(content)
            
            # Create LLMResponse
            return LLMResponse(
                intent_type=parsed['intent_type'],
                confidence=parsed['confidence'],
                reasoning=parsed['reasoning'],
                entities=parsed['entities'],
                urgency=parsed['urgency'],
                requires_human=parsed['requires_human'],
                raw_response=content
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing Groq response: {e}")
            # Return fallback response
            return self._create_fallback_response(original_text)
    
    def _create_fallback_response(self, text: str) -> LLMResponse:
        """
        Create fallback response when parsing fails
        
        Args:
            text: Original user text
            
        Returns:
            Fallback LLMResponse
        """
        # Simple keyword-based fallback
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['fraud', 'scam', 'suspicious', 'hack', 'unauthorized']):
            intent_type = 'fraud_detection'
            urgency = 'high'
            confidence = 0.6
        elif any(keyword in text_lower for keyword in ['balance', 'account', 'transaction']):
            intent_type = 'account_inquiry'
            urgency = 'medium'
            confidence = 0.5
        else:
            intent_type = 'general_inquiry'
            urgency = 'low'
            confidence = 0.4
        
        return LLMResponse(
            intent_type=intent_type,
            confidence=confidence,
            reasoning="Fallback classification due to parsing error",
            entities={"phone_numbers": [], "amounts": [], "dates": [], "suspicious_indicators": []},
            urgency=urgency,
            requires_human=urgency == 'high',
            raw_response="FALLBACK_RESPONSE"
        )
    
    def is_available(self) -> bool:
        """
        Check if Groq provider is available
        
        Returns:
            True if API key is configured
        """
        return self.api_key is not None and len(self.api_key.strip()) > 0