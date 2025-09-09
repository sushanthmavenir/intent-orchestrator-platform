#!/usr/bin/env python3
"""
Intent Orchestration Platform - Integration Test Suite
======================================================

Comprehensive integration tests to verify all platform components
work together correctly before final deployment.
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


class IntegrationTestSuite:
    """
    Comprehensive integration test suite for the Intent Orchestration Platform
    """
    
    def __init__(self):
        self.base_url = "http://localhost:8002"
        self.camara_url = "http://localhost:8003"
        self.test_results = []
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def run_all_tests(self):
        """Run all integration tests"""
        print("Intent Orchestration Platform - Integration Test Suite")
        print("=" * 60)
        print()
        
        tests = [
            ("Health Checks", self.test_health_checks),
            ("TMF 921A API", self.test_tmf921_api),
            ("CAMARA APIs", self.test_camara_apis),
            ("Intent Classification", self.test_intent_classification),
            ("Agent Framework", self.test_agent_framework),
            ("Workflow Orchestration", self.test_workflow_orchestration),
            ("WebSocket Chat", self.test_websocket_chat),
            ("Fraud Detection Flow", self.test_fraud_detection_flow),
            ("Performance Tests", self.test_performance),
        ]
        
        for test_name, test_func in tests:
            print(f"Running {test_name} tests...")
            try:
                await test_func()
                self._log_result(test_name, "PASS", "All tests passed")
                print(f"PASS {test_name}: PASSED\n")
            except Exception as e:
                self._log_result(test_name, "FAIL", str(e))
                print(f"FAIL {test_name}: FAILED - {e}\n")
                
        # Generate test report
        await self._generate_test_report()
        
    async def test_health_checks(self):
        """Test health endpoints for all services"""
        # Test main application health
        async with self.session.get(f"{self.base_url}/health") as resp:
            assert resp.status == 200
            health_data = await resp.json()
            assert health_data.get("status") == "healthy"
            
        # Test CAMARA APIs health  
        async with self.session.get(f"{self.camara_url}/health") as resp:
            assert resp.status == 200
            
    async def test_tmf921_api(self):
        """Test TMF 921A Intent Management API compliance"""
        # Test intent creation
        intent_data = {
            "name": "Test Integration Intent",
            "description": "Integration test intent for verification",
            "expression": "test integration functionality",
            "category": "test",
            "priority": 1
        }
        
        async with self.session.post(f"{self.base_url}/tmf921/intent", json=intent_data) as resp:
            assert resp.status == 201
            created_intent = await resp.json()
            intent_id = created_intent["id"]
            
        # Test intent retrieval
        async with self.session.get(f"{self.base_url}/tmf921/intent/{intent_id}") as resp:
            assert resp.status == 200
            retrieved_intent = await resp.json()
            assert retrieved_intent["name"] == intent_data["name"]
            
        # Test intent listing
        async with self.session.get(f"{self.base_url}/tmf921/intent") as resp:
            assert resp.status == 200
            intents = await resp.json()
            assert len(intents) > 0
            
        # Test intent update
        update_data = {"description": "Updated integration test intent"}
        async with self.session.patch(f"{self.base_url}/tmf921/intent/{intent_id}", json=update_data) as resp:
            assert resp.status == 200
            updated_intent = await resp.json()
            assert updated_intent["description"] == update_data["description"]
            
        # Test intent deletion
        async with self.session.delete(f"{self.base_url}/tmf921/intent/{intent_id}") as resp:
            assert resp.status == 204
            
    async def test_camara_apis(self):
        """Test CAMARA API mock implementations"""
        test_phone = "+1-555-0123"
        
        # Test SIM Swap API
        sim_swap_data = {"phone_number": test_phone, "max_age": 240}
        async with self.session.post(f"{self.camara_url}/camara/sim-swap/v1/check", json=sim_swap_data) as resp:
            assert resp.status == 200
            sim_result = await resp.json()
            assert "swapped" in sim_result
            
        # Test Device Location API
        location_data = {"device": {"phone_number": test_phone}}
        async with self.session.post(f"{self.camara_url}/camara/location/v1/retrieve", json=location_data) as resp:
            assert resp.status == 200
            location_result = await resp.json()
            assert "location" in location_result
            
        # Test KYC Match API
        kyc_data = {"phone_number": test_phone, "name": "Test User"}
        async with self.session.post(f"{self.camara_url}/camara/kyc-match/v1/verify", json=kyc_data) as resp:
            assert resp.status == 200
            kyc_result = await resp.json()
            assert "overall_match" in kyc_result
            
        # Test Scam Signal API
        scam_data = {"phone_number": test_phone, "communication_content": "test"}
        async with self.session.post(f"{self.camara_url}/camara/scam-signal/v1/analyze", json=scam_data) as resp:
            assert resp.status == 200
            scam_result = await resp.json()
            assert "overall_scam_score" in scam_result
            
    async def test_intent_classification(self):
        """Test intent classification engine"""
        test_messages = [
            "I think someone is trying to scam me with fake bank calls",
            "Can you help verify my account security?",
            "I received suspicious messages asking for my password"
        ]
        
        for message in test_messages:
            classification_data = {"text": message}
            async with self.session.post(f"{self.base_url}/api/analyze/intent", json=classification_data) as resp:
                assert resp.status == 200
                result = await resp.json()
                assert "primary_intent" in result
                assert "confidence" in result
                assert result["confidence"] > 0
                
    async def test_agent_framework(self):
        """Test specialized agent framework"""
        # Test agent health checks
        async with self.session.get(f"{self.base_url}/api/agents/health") as resp:
            assert resp.status == 200
            health_data = await resp.json()
            assert len(health_data) > 0
            
        # Test agent capabilities
        async with self.session.get(f"{self.base_url}/api/agents/capabilities") as resp:
            assert resp.status == 200
            capabilities = await resp.json()
            assert len(capabilities) > 0
            
        # Test fraud detection agent
        fraud_data = {
            "customer_phone": "+1-555-0123",
            "caller_phone": "+1-555-9999",
            "communication_content": "This is a test fraud detection scenario"
        }
        async with self.session.post(f"{self.base_url}/api/agents/fraud-detection/analyze", json=fraud_data) as resp:
            assert resp.status == 200
            result = await resp.json()
            assert "risk_score" in result
            
    async def test_workflow_orchestration(self):
        """Test LangGraph workflow orchestration"""
        workflow_data = {
            "workflow_type": "fraud_detection",
            "input_data": {
                "customer_phone": "+1-555-0123",
                "scenario": "social_engineering_test"
            }
        }
        
        async with self.session.post(f"{self.base_url}/api/workflows/execute", json=workflow_data) as resp:
            assert resp.status == 200
            result = await resp.json()
            assert "workflow_id" in result
            assert "status" in result
            
    async def test_websocket_chat(self):
        """Test WebSocket chat functionality"""
        # This is a simplified test - full WebSocket testing would require different setup
        # Test chat message processing endpoint instead
        chat_data = {
            "message": "I think I'm being scammed",
            "user_id": "test_user"
        }
        
        async with self.session.post(f"{self.base_url}/api/chat/process", json=chat_data) as resp:
            assert resp.status == 200
            result = await resp.json()
            assert "response" in result
            
    async def test_fraud_detection_flow(self):
        """Test end-to-end fraud detection flow"""
        # Simulate a complete fraud detection scenario
        scenario_data = {
            "customer_phone": "+1-555-0123",
            "caller_phone": "+1-555-9999",
            "communication_content": """
            Hello, this is Michael from your bank security department. 
            We've detected unusual activity on your account and need to verify 
            your identity immediately. Please provide your account number and 
            the last four digits of your SSN to secure your account.
            """,
            "context": {
                "communication_type": "phone_call",
                "urgency_claimed": True,
                "authority_impersonation": True
            }
        }
        
        # Test comprehensive fraud detection
        async with self.session.post(f"{self.base_url}/api/fraud/analyze-comprehensive", json=scenario_data) as resp:
            assert resp.status == 200
            result = await resp.json()
            assert "overall_risk_score" in result
            assert "recommendations" in result
            assert result["overall_risk_score"] > 0.5  # Should detect this as high risk
            
    async def test_performance(self):
        """Test system performance under load"""
        # Simple performance test with concurrent requests
        async def make_request():
            async with self.session.get(f"{self.base_url}/health") as resp:
                return resp.status == 200
                
        # Test with 10 concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All requests should succeed
        assert all(results)
        
        # Should complete within reasonable time (5 seconds)
        duration = end_time - start_time
        assert duration < 5.0, f"Performance test took {duration:.2f}s (should be < 5s)"
        
    def _log_result(self, test_name: str, status: str, details: str):
        """Log test result"""
        self.test_results.append({
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    async def _generate_test_report(self):
        """Generate comprehensive test report"""
        print("INTEGRATION TEST RESULTS")
        print("=" * 40)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        if failed > 0:
            print("FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   - {result['test_name']}: {result['details']}")
            print()
            
        # Save detailed report
        report_data = {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "success_rate": (passed/total)*100,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": self.test_results
        }
        
        with open("test_results.json", "w") as f:
            json.dump(report_data, f, indent=2)
            
        print("Detailed test report saved to test_results.json")
        
        if failed == 0:
            print("ALL INTEGRATION TESTS PASSED!")
            print("Platform is ready for deployment")
        else:
            print("Some tests failed - please review before deployment")
            
        return failed == 0


async def main():
    """Main test execution function"""
    print("Starting Intent Orchestration Platform Integration Tests")
    print()
    print("Prerequisites:")
    print("- Backend services running on localhost:8002")
    print("- CAMARA APIs running on localhost:8003")
    print("- All agents initialized and healthy")
    print()
    
    input("Press Enter to start tests (Ctrl+C to cancel)...")
    print()
    
    async with IntegrationTestSuite() as test_suite:
        success = await test_suite.run_all_tests()
        
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        sys.exit(1)