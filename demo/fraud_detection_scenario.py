"""
Fraud Detection Demo Scenario
=============================

This demo showcases the Intent Orchestration Platform's fraud detection capabilities
using a realistic social engineering attack scenario involving Sarah, a bank customer.

The demo demonstrates:
1. Real-time intent detection and classification
2. Multi-agent fraud analysis using CAMARA APIs
3. Workflow orchestration with LangGraph
4. Comprehensive risk assessment and recommendations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Import platform components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from agents.agent_factory import agent_factory
from workflow.engines.langgraph_orchestrator import LangGraphOrchestrator
from intent_analysis.intent_classifier import IntentClassifier
from mcp.registry.resource_registry import ResourceRegistry


class FraudDetectionDemo:
    """
    Comprehensive fraud detection demonstration
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.orchestrator = None
        self.intent_classifier = None
        self.resource_registry = None
        self.agents = {}
        
    async def initialize(self):
        """Initialize demo components"""
        print("🚀 Initializing Fraud Detection Demo...")
        
        # Initialize components
        self.orchestrator = LangGraphOrchestrator()
        self.intent_classifier = IntentClassifier()
        self.resource_registry = ResourceRegistry()
        
        # Create all specialized agents
        self.agents = await agent_factory.create_all_agents()
        
        print(f"✅ Initialized {len(self.agents)} specialized agents")
        print("📋 Demo ready to begin\n")
        
    async def run_sarah_scenario(self):
        """
        Run the complete Sarah fraud detection scenario
        """
        print("=" * 80)
        print("🎭 FRAUD DETECTION DEMO: Sarah's Social Engineering Attack")
        print("=" * 80)
        print()
        
        # Phase 1: Initial suspicious contact
        await self._phase_1_initial_contact()
        
        # Phase 2: Intent detection and classification
        await self._phase_2_intent_analysis()
        
        # Phase 3: Multi-agent fraud analysis
        await self._phase_3_fraud_analysis()
        
        # Phase 4: Workflow orchestration
        await self._phase_4_workflow_execution()
        
        # Phase 5: Risk assessment and recommendations
        await self._phase_5_risk_assessment()
        
        print("=" * 80)
        print("✅ Fraud Detection Demo Complete")
        print("=" * 80)
        
    async def _phase_1_initial_contact(self):
        """Phase 1: Sarah receives a suspicious phone call"""
        print("📞 PHASE 1: Initial Suspicious Contact")
        print("-" * 40)
        
        # Scenario setup
        scenario = {
            "customer": {
                "name": "Sarah Johnson",
                "phone_number": "+1-555-0123",
                "account_id": "ACC-789012",
                "customer_since": "2019-03-15",
                "usual_location": "Seattle, WA"
            },
            "suspicious_call": {
                "caller_number": "+1-555-9999",
                "timestamp": datetime.now().isoformat(),
                "caller_claimed_identity": "Bank Security Department",
                "call_content": """
                Hello Ms. Johnson, this is Michael from the security department at your bank.
                We've detected some unusual activity on your account and need to verify your 
                identity immediately to prevent unauthorized access. There have been multiple 
                login attempts from a foreign IP address in the last hour.
                
                For your security, I need you to confirm your account number and the last 
                four digits of your social security number. We also need to verify the 
                security code from your banking app to protect your account.
                
                This is urgent - we need to act within the next 10 minutes or we'll have 
                to freeze your account for your protection.
                """
            }
        }
        
        print(f"👤 Customer: {scenario['customer']['name']}")
        print(f"📱 Phone: {scenario['customer']['phone_number']}")
        print(f"🏠 Location: {scenario['customer']['usual_location']}")
        print()
        print("📞 Suspicious Call Received:")
        print(f"   Caller: {scenario['suspicious_call']['caller_number']}")
        print(f"   Claims: {scenario['suspicious_call']['caller_claimed_identity']}")
        print(f"   Time: {scenario['suspicious_call']['timestamp']}")
        print()
        print("💬 Call Content Summary:")
        print("   - Claims to be from bank security")
        print("   - Reports 'unusual activity' and 'foreign IP address'")
        print("   - Requests account number and SSN")
        print("   - Creates urgency with 10-minute deadline")
        print("   - Threatens account freeze")
        print()
        
        # Store scenario data for subsequent phases
        self.scenario_data = scenario
        
        input("Press Enter to continue to intent analysis...")
        print()
        
    async def _phase_2_intent_analysis(self):
        """Phase 2: Analyze the communication for intent and threats"""
        print("🧠 PHASE 2: Intent Detection & Classification")
        print("-" * 40)
        
        call_content = self.scenario_data["suspicious_call"]["call_content"]
        customer_phone = self.scenario_data["customer"]["phone_number"]
        
        print("🔍 Analyzing call content for intents and threats...")
        
        # Classify the intent using our intent classifier
        classification_result = await self.intent_classifier.classify_intent(call_content)
        
        print("📊 Intent Classification Results:")
        print(f"   Primary Intent: {classification_result.get('primary_intent', 'unknown')}")
        print(f"   Confidence: {classification_result.get('confidence', 0):.1%}")
        print(f"   Intent Type: {classification_result.get('intent_type', 'unknown')}")
        print()
        
        # Extract detected entities
        entities = classification_result.get('entities', {})
        if entities:
            print("🏷️  Detected Entities:")
            for entity_type, entity_list in entities.items():
                if entity_list:
                    print(f"   {entity_type}: {', '.join(entity_list)}")
            print()
            
        # Show urgency and threat indicators
        urgency_score = classification_result.get('urgency_score', 0)
        threat_indicators = classification_result.get('threat_indicators', [])
        
        print(f"⚠️  Urgency Score: {urgency_score:.2f}")
        if threat_indicators:
            print("🚨 Threat Indicators:")
            for indicator in threat_indicators:
                print(f"   - {indicator}")
        print()
        
        # Store analysis results
        self.intent_analysis = classification_result
        
        input("Press Enter to continue to fraud analysis...")
        print()
        
    async def _phase_3_fraud_analysis(self):
        """Phase 3: Multi-agent fraud analysis using CAMARA APIs"""
        print("🕵️ PHASE 3: Multi-Agent Fraud Analysis")
        print("-" * 40)
        
        customer_phone = self.scenario_data["customer"]["phone_number"]
        caller_phone = self.scenario_data["suspicious_call"]["caller_number"]
        
        # Prepare analysis tasks
        analysis_tasks = []
        
        print("🤖 Deploying specialized agents for analysis...")
        print()
        
        # 1. SIM Swap Detection
        print("📱 SIM Swap Agent Analysis:")
        if "sim_swap" in self.agents:
            sim_agent = self.agents["sim_swap"]
            sim_result = await sim_agent.process_request(
                "sim_swap_detection",
                {"phone_number": customer_phone}
            )
            print(f"   Status: {sim_result.get('status', 'unknown')}")
            if sim_result.get('status') == 'success':
                result_data = sim_result.get('result', {})
                print(f"   SIM Swap Detected: {result_data.get('sim_swap_detected', False)}")
                print(f"   Risk Level: {result_data.get('risk_level', 0)}")
            print()
            
        # 2. Device Location Analysis  
        print("📍 Device Location Agent Analysis:")
        if "device_location" in self.agents:
            location_agent = self.agents["device_location"]
            location_result = await location_agent.process_request(
                "location_risk_assessment",
                {
                    "phone_number": customer_phone,
                    "context": {"user_home_country": "US"}
                }
            )
            print(f"   Status: {location_result.get('status', 'unknown')}")
            if location_result.get('status') == 'success':
                result_data = location_result.get('result', {})
                print(f"   Risk Score: {result_data.get('risk_score', 0)}")
                print(f"   Risk Level: {result_data.get('risk_level', 'UNKNOWN')}")
            print()
            
        # 3. KYC Match Verification
        print("🆔 KYC Match Agent Analysis:")
        if "kyc_match" in self.agents:
            kyc_agent = self.agents["kyc_match"]
            # Simulate verification attempt
            kyc_result = await kyc_agent.process_request(
                "identity_verification",
                {
                    "phone_number": customer_phone,
                    "verification_data": {
                        "name": "Sarah Johnson",
                        "phone_number": customer_phone
                    }
                }
            )
            print(f"   Status: {kyc_result.get('status', 'unknown')}")
            if kyc_result.get('status') == 'success':
                result_data = kyc_result.get('result', {})
                print(f"   Verification Status: {result_data.get('verification_status', 'unknown')}")
                print(f"   Match Score: {result_data.get('match_score', 0):.2f}")
            print()
            
        # 4. Scam Signal Detection
        print("🚨 Scam Signal Agent Analysis:")
        if "scam_signal" in self.agents:
            scam_agent = self.agents["scam_signal"]
            scam_result = await scam_agent.process_request(
                "social_engineering_analysis",
                {
                    "phone_number": caller_phone,
                    "communication_content": self.scenario_data["suspicious_call"]["call_content"],
                    "type": "call"
                }
            )
            print(f"   Status: {scam_result.get('status', 'unknown')}")
            if scam_result.get('status') == 'success':
                result_data = scam_result.get('result', {})
                print(f"   Social Engineering Detected: {result_data.get('social_engineering_detected', False)}")
                print(f"   Risk Score: {result_data.get('risk_score', 0):.2f}")
                tactics = result_data.get('tactics_identified', [])
                if tactics:
                    print(f"   Tactics: {', '.join(tactics)}")
            print()
            
        # Store analysis results
        self.fraud_analysis = {
            "sim_swap": sim_result if 'sim_result' in locals() else None,
            "location": location_result if 'location_result' in locals() else None,
            "kyc_match": kyc_result if 'kyc_result' in locals() else None,
            "scam_signal": scam_result if 'scam_result' in locals() else None
        }
        
        input("Press Enter to continue to workflow orchestration...")
        print()
        
    async def _phase_4_workflow_execution(self):
        """Phase 4: Orchestrate comprehensive fraud detection workflow"""
        print("🔄 PHASE 4: Workflow Orchestration")
        print("-" * 40)
        
        print("🎼 Orchestrating comprehensive fraud detection workflow...")
        
        # Create workflow input combining all previous analysis
        workflow_input = {
            "customer_phone": self.scenario_data["customer"]["phone_number"],
            "caller_phone": self.scenario_data["suspicious_call"]["caller_number"],
            "intent_analysis": self.intent_analysis,
            "fraud_analysis": self.fraud_analysis,
            "scenario_context": {
                "communication_type": "phone_call",
                "urgency_claimed": True,
                "authority_impersonation": True,
                "information_request": True
            }
        }
        
        # Execute fraud detection workflow
        print("⚙️  Executing LangGraph fraud detection workflow...")
        workflow_result = await self.orchestrator.execute_workflow(
            "fraud_detection",
            workflow_input
        )
        
        print(f"   Workflow Status: {workflow_result.get('status', 'unknown')}")
        print(f"   Steps Executed: {len(workflow_result.get('execution_steps', []))}")
        print(f"   Total Duration: {workflow_result.get('total_duration_ms', 0)}ms")
        print()
        
        # Show workflow execution steps
        steps = workflow_result.get('execution_steps', [])
        if steps:
            print("📋 Workflow Execution Steps:")
            for i, step in enumerate(steps, 1):
                print(f"   {i}. {step.get('step_type', 'unknown')} - {step.get('agent_id', 'system')}")
                print(f"      Status: {step.get('status', 'unknown')}")
                print(f"      Duration: {step.get('duration_ms', 0)}ms")
            print()
            
        # Store workflow results
        self.workflow_result = workflow_result
        
        input("Press Enter to continue to risk assessment...")
        print()
        
    async def _phase_5_risk_assessment(self):
        """Phase 5: Final risk assessment and recommendations"""
        print("⚖️  PHASE 5: Risk Assessment & Recommendations")
        print("-" * 40)
        
        # Comprehensive fraud detection using the main fraud detection agent
        print("🎯 Running comprehensive fraud detection analysis...")
        
        if "fraud_detection" in self.agents:
            fraud_agent = self.agents["fraud_detection"]
            
            # Prepare comprehensive input
            comprehensive_input = {
                "customer_phone": self.scenario_data["customer"]["phone_number"],
                "caller_phone": self.scenario_data["suspicious_call"]["caller_number"],
                "communication_content": self.scenario_data["suspicious_call"]["call_content"],
                "customer_data": self.scenario_data["customer"],
                "context": {
                    "communication_type": "phone_call",
                    "claims_authority": True,
                    "requests_sensitive_info": True,
                    "creates_urgency": True
                }
            }
            
            # Execute comprehensive fraud detection
            final_result = await fraud_agent.process_request(
                "comprehensive_fraud_detection",
                comprehensive_input
            )
            
            print("📊 FINAL FRAUD ASSESSMENT:")
            print("=" * 50)
            
            if final_result.get('status') == 'success':
                result_data = final_result.get('result', {})
                
                # Overall risk assessment
                print(f"🎯 Overall Fraud Risk: {result_data.get('overall_risk_level', 'UNKNOWN')}")
                print(f"📈 Risk Score: {result_data.get('overall_risk_score', 0):.3f}")
                print(f"🎭 Attack Type: {result_data.get('attack_classification', 'Unknown')}")
                print()
                
                # Risk factors
                risk_factors = result_data.get('risk_factors', [])
                if risk_factors:
                    print("⚠️  Identified Risk Factors:")
                    for factor in risk_factors:
                        print(f"   • {factor}")
                    print()
                
                # Individual analysis results
                individual_results = result_data.get('individual_analysis', {})
                print("🔍 Individual Analysis Results:")
                for analysis_type, analysis_result in individual_results.items():
                    if isinstance(analysis_result, dict):
                        risk_level = analysis_result.get('risk_level', 'UNKNOWN')
                        confidence = analysis_result.get('confidence', 0)
                        print(f"   {analysis_type.replace('_', ' ').title()}: {risk_level} (confidence: {confidence:.1%})")
                print()
                
                # Recommendations
                recommendations = result_data.get('recommendations', [])
                if recommendations:
                    print("💡 RECOMMENDATIONS:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"   {i}. {rec}")
                    print()
                    
                # Confidence and metadata
                print(f"🎯 Analysis Confidence: {final_result.get('metadata', {}).get('confidence', 0):.1%}")
                print(f"⏱️  Processing Time: {final_result.get('processing_time_ms', 0)}ms")
                
            else:
                print(f"❌ Analysis failed: {final_result.get('error', {}).get('message', 'Unknown error')}")
                
        print()
        print("🏁 SCENARIO CONCLUSION:")
        print("-" * 30)
        print("This scenario demonstrates a classic social engineering attack")
        print("combining authority impersonation, urgency creation, and information")
        print("harvesting. The Intent Orchestration Platform successfully:")
        print()
        print("✅ Detected the fraudulent intent in real-time")
        print("✅ Classified the social engineering tactics")
        print("✅ Orchestrated multi-agent analysis")
        print("✅ Provided comprehensive risk assessment")
        print("✅ Generated actionable security recommendations")
        print()
        
    async def cleanup(self):
        """Cleanup demo resources"""
        print("🧹 Cleaning up demo resources...")
        await agent_factory.shutdown_all_agents()
        print("✅ Demo cleanup complete")


async def main():
    """Main demo execution function"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run demo
    demo = FraudDetectionDemo()
    
    try:
        await demo.initialize()
        await demo.run_sarah_scenario()
        
    except KeyboardInterrupt:
        print("\n\n⛔ Demo interrupted by user")
        
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    print("🎭 Intent Orchestration Platform - Fraud Detection Demo")
    print("=" * 60)
    print()
    print("This demo showcases Sarah's social engineering attack scenario")
    print("and demonstrates the platform's fraud detection capabilities.")
    print()
    input("Press Enter to start the demo...")
    print()
    
    asyncio.run(main())