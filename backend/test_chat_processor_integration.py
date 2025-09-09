#!/usr/bin/env python3
"""
Test script for ChatMessageProcessor integration with hybrid classification
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intent_analysis.chat_processor import ChatMessageProcessor


async def test_chat_processor_integration():
    """Test ChatMessageProcessor with hybrid classification"""
    
    test_messages = [
        "I think someone stole my credit card information and made unauthorized transactions",
        "Can you help me check my account balance?", 
        "There's a suspicious charge on my statement for $500",
        "How do I reset my password?"
    ]
    
    print("=== ChatMessageProcessor Hybrid Integration Test ===\n")
    
    print("1. Testing ChatMessageProcessor initialization...")
    try:
        processor = ChatMessageProcessor()
        print(f"   [OK] ChatMessageProcessor initialized successfully")
        
        # Check if IntentClassifier is initialized
        if hasattr(processor, 'intent_classifier'):
            stats = processor.intent_classifier.get_classification_stats()
            print(f"   [OK] Hybrid IntentClassifier integrated")
            print(f"   [OK] Classification mode: {stats['classification_mode']}")
            print(f"   [OK] LLM available: {stats['llm_provider_available']}")
        else:
            print(f"   [FAIL] IntentClassifier not found in processor")
            return
            
    except Exception as e:
        print(f"   [FAIL] ChatMessageProcessor initialization failed: {e}")
        return
    
    print("\n2. Testing full chat message processing...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n   Test {i}: '{message[:50]}...'")
        try:
            start_time = asyncio.get_event_loop().time()
            result = await processor.process_chat_message(message, f"test_user_{i}")
            end_time = asyncio.get_event_loop().time()
            
            if result["status"] == "success":
                intent = result["intent"]
                analysis = result["analysis"]
                
                print(f"      [OK] Processing successful")
                print(f"      [OK] Intent ID: {intent['id']}")
                print(f"      [OK] Intent lifecycle: {intent['lifecycle_status']}")
                
                # Show classification results
                classification = analysis["intent_classification"]
                print(f"      [OK] Primary Intent: {classification['primary_intent']}")
                print(f"      [OK] Confidence: {classification['confidence']:.2f}")
                
                # Show hybrid-specific details
                if 'method_used' in classification:
                    print(f"      [OK] Method Used: {classification['method_used']}")
                    print(f"      [OK] Fallback Used: {classification.get('fallback_used', 'N/A')}")
                    print(f"      [OK] Processing Time: {classification.get('processing_time_ms', 0)}ms")
                
                # Show LLM reasoning if available
                if classification.get('llm_reasoning'):
                    print(f"      [OK] LLM Reasoning: {classification['llm_reasoning']}")
                
                # Show entities
                if classification.get('entities'):
                    print(f"      [OK] Entities Found: {list(classification['entities'].keys())}")
                
                # Show urgency
                urgency = analysis.get("urgency_level", {}).get("level", "unknown")
                print(f"      [OK] Urgency Level: {urgency}")
                
                # Show workflow plan
                workflow = result["workflow"]
                print(f"      [OK] Workflow Type: {workflow['workflow_type']}")
                print(f"      [OK] Required Agents: {len(workflow['required_agents'])}")
                
                total_time = (end_time - start_time) * 1000
                print(f"      [OK] Total Processing Time: {total_time:.0f}ms")
                
            else:
                print(f"      [FAIL] Processing failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"      [FAIL] Chat processing failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n3. Testing intent classification directly...")
    
    try:
        test_message = "I think there's fraud on my account"
        classification = await processor.classify_intent(test_message)
        
        print(f"   [OK] Direct classification successful")
        print(f"   [OK] Intent: {classification['primary_intent']}")
        print(f"   [OK] Confidence: {classification['confidence']:.2f}")
        print(f"   [OK] Method: {classification.get('method_used', 'unknown')}")
        
        if classification.get('llm_reasoning'):
            print(f"   [OK] LLM Reasoning: {classification['llm_reasoning']}")
            
    except Exception as e:
        print(f"   [FAIL] Direct classification failed: {e}")
    
    print("\n=== Integration Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_chat_processor_integration())