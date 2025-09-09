#!/usr/bin/env python3
"""
Test script for hybrid classification system
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intent_analysis.intent_classifier import IntentClassifier
from config.config_loader import config_loader


async def test_classification_modes():
    """Test different classification modes"""
    
    test_messages = [
        "I think someone stole my credit card information and made unauthorized transactions",
        "Can you help me check my account balance?",
        "I want to apply for a new loan",
        "There's a suspicious charge on my statement for $500",
        "How do I reset my password?"
    ]
    
    print("=== Hybrid Classification System Test ===\n")
    
    # Test configuration loading
    print("1. Testing configuration loading...")
    try:
        config = config_loader.load_classification_config()
        mode = config_loader.get_classification_mode()
        print(f"   [OK] Configuration loaded successfully")
        print(f"   [OK] Classification mode: {mode}")
        print(f"   [OK] LLM config: {config_loader.get_llm_config()}")
    except Exception as e:
        print(f"   [FAIL] Configuration failed: {e}")
        return
    
    print("\n2. Testing IntentClassifier initialization...")
    try:
        classifier = IntentClassifier()
        stats = classifier.get_classification_stats()
        print(f"   [OK] Classifier initialized successfully")
        print(f"   [OK] Available modes: {classifier.get_available_modes()}")
        print(f"   [OK] Current mode: {stats['classification_mode']}")
        print(f"   [OK] LLM available: {stats['llm_provider_available']}")
        print(f"   [OK] Pattern matcher available: {stats['pattern_matcher_available']}")
    except Exception as e:
        print(f"   [FAIL] Classifier initialization failed: {e}")
        return
    
    print("\n3. Testing classification with different messages...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n   Test {i}: '{message[:50]}...'")
        try:
            start_time = asyncio.get_event_loop().time()
            result = await classifier.classify_intent(message)
            end_time = asyncio.get_event_loop().time()
            
            print(f"      [OK] Intent: {result['intent_type']}")
            print(f"      [OK] Confidence: {result['confidence']:.2f}")
            print(f"      [OK] Method: {result.get('method_used', 'unknown')}")
            print(f"      [OK] Urgency: {result['urgency']}")
            print(f"      [OK] Processing time: {result.get('processing_time_ms', 0)}ms")
            print(f"      [OK] Fallback used: {result.get('fallback_used', False)}")
            
            # Show entities if any
            if result.get('entities'):
                print(f"      [OK] Entities: {result['entities']}")
            
            # Show LLM reasoning if available
            analysis_details = result.get('analysis_details', {})
            if analysis_details.get('llm_reasoning'):
                print(f"      [OK] LLM Reasoning: {analysis_details['llm_reasoning']}")
                
        except Exception as e:
            print(f"      [FAIL] Classification failed: {e}")
            print(f"         Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()

    print("\n4. Testing synchronous wrapper...")
    try:
        sync_result = classifier.classify_intent_sync(test_messages[0])
        print(f"   [OK] Sync classification works: {sync_result['intent_type']}")
    except Exception as e:
        print(f"   [FAIL] Sync classification failed: {e}")

    print("\n=== Test Complete ===")


async def test_mode_switching():
    """Test switching between different modes"""
    print("\n=== Mode Switching Test ===")
    
    # Test pattern mode
    print("\n1. Testing pattern mode...")
    os.environ['CLASSIFICATION_MODE'] = 'pattern'
    config_loader.clear_cache()  # Clear cache to reload config
    
    try:
        classifier = IntentClassifier()
        result = await classifier.classify_intent("I think someone hacked my account")
        print(f"   [OK] Pattern mode: {result['intent_type']} (confidence: {result['confidence']:.2f})")
        print(f"   [OK] Method used: {result.get('method_used', 'unknown')}")
    except Exception as e:
        print(f"   [FAIL] Pattern mode failed: {e}")
    
    # Test hybrid mode
    print("\n2. Testing hybrid mode...")
    os.environ['CLASSIFICATION_MODE'] = 'hybrid'
    config_loader.clear_cache()
    
    try:
        classifier = IntentClassifier()
        result = await classifier.classify_intent("I think someone hacked my account")
        print(f"   [OK] Hybrid mode: {result['intent_type']} (confidence: {result['confidence']:.2f})")
        print(f"   [OK] Method used: {result.get('method_used', 'unknown')}")
        print(f"   [OK] Fallback used: {result.get('fallback_used', False)}")
    except Exception as e:
        print(f"   [FAIL] Hybrid mode failed: {e}")
    
    # Test LLM mode
    print("\n3. Testing LLM mode...")
    os.environ['CLASSIFICATION_MODE'] = 'llm'
    config_loader.clear_cache()
    
    try:
        classifier = IntentClassifier()
        result = await classifier.classify_intent("I think someone hacked my account")
        print(f"   [OK] LLM mode: {result['intent_type']} (confidence: {result['confidence']:.2f})")
        print(f"   [OK] Method used: {result.get('method_used', 'unknown')}")
        
        # Show LLM-specific details
        analysis_details = result.get('analysis_details', {})
        if analysis_details.get('llm_reasoning'):
            print(f"   [OK] LLM Reasoning: {analysis_details['llm_reasoning']}")
    except Exception as e:
        print(f"   [FAIL] LLM mode failed: {e}")
    
    # Reset to default
    if 'CLASSIFICATION_MODE' in os.environ:
        del os.environ['CLASSIFICATION_MODE']
    config_loader.clear_cache()


if __name__ == "__main__":
    asyncio.run(test_classification_modes())
    asyncio.run(test_mode_switching())