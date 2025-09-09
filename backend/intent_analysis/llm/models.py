"""
LLM Classification Models
========================

Data models for LLM-based intent classification.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class UrgencyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ClassificationMethod(Enum):
    PATTERN = "pattern"
    LLM = "llm"
    HYBRID = "hybrid"


@dataclass
class ClassificationResult:
    """Enhanced classification result with LLM capabilities"""
    
    intent_type: str
    confidence: float
    reasoning: Optional[str] = None
    entities: Dict[str, List[Any]] = field(default_factory=dict)
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    requires_human: bool = False
    processing_time_ms: int = 0
    method_used: ClassificationMethod = ClassificationMethod.PATTERN
    fallback_used: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "intent_type": self.intent_type,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "entities": self.entities,
            "urgency": self.urgency.value if isinstance(self.urgency, UrgencyLevel) else self.urgency,
            "requires_human": self.requires_human,
            "processing_time_ms": self.processing_time_ms,
            "method_used": self.method_used.value if isinstance(self.method_used, ClassificationMethod) else self.method_used,
            "fallback_used": self.fallback_used
        }


@dataclass 
class LLMResponse:
    """Raw response from LLM provider"""
    
    intent_type: str
    confidence: float
    reasoning: str
    entities: Dict[str, List[Any]]
    urgency: str
    requires_human: bool
    raw_response: Optional[str] = None
    
    def to_classification_result(self, processing_time_ms: int) -> ClassificationResult:
        """Convert to ClassificationResult"""
        return ClassificationResult(
            intent_type=self.intent_type,
            confidence=self.confidence,
            reasoning=self.reasoning,
            entities=self.entities,
            urgency=UrgencyLevel(self.urgency) if self.urgency in [e.value for e in UrgencyLevel] else UrgencyLevel.MEDIUM,
            requires_human=self.requires_human,
            processing_time_ms=processing_time_ms,
            method_used=ClassificationMethod.LLM
        )