"""
Base LLM Provider Interface
===========================

Abstract base class for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import time
from ..models import LLMResponse


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('model', '')
        self.timeout = config.get('timeout', 10)
        self.max_tokens = config.get('max_tokens', 200)
        self.temperature = config.get('temperature', 0.1)
    
    @abstractmethod
    async def classify_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """
        Classify intent using LLM
        
        Args:
            text: The user message to classify
            context: Optional context information
            
        Returns:
            LLMResponse with classification result
            
        Raises:
            LLMProviderError: If classification fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM provider is available
        
        Returns:
            True if provider is available, False otherwise
        """
        pass
    
    async def classify_with_timeout(self, text: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """
        Classify intent with timeout protection
        
        Args:
            text: The user message to classify
            context: Optional context information
            
        Returns:
            LLMResponse with classification result
            
        Raises:
            asyncio.TimeoutError: If operation times out
            LLMProviderError: If classification fails
        """
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self.classify_intent(text, context),
                timeout=self.timeout
            )
            
            # Add processing time
            processing_time = int((time.time() - start_time) * 1000)
            return result
            
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"LLM request timed out after {self.timeout} seconds")


class LLMProviderError(Exception):
    """Exception raised by LLM providers"""
    
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.error_code = error_code
    
    def __str__(self):
        return f"LLMProviderError [{self.provider}]: {self.message}"