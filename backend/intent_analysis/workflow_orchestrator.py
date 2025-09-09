"""
Workflow Orchestrator for Chat-Originated Intents
=================================================

Orchestrates workflow execution for intents created from chat messages.
"""

import asyncio
import json
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)
print(f"WorkflowOrchestrator logger name: {logger.name}")
print(f"WorkflowOrchestrator logger level: {logger.level}")
print(f"WorkflowOrchestrator logger handlers: {logger.handlers}")
print(f"WorkflowOrchestrator logger propagate: {logger.propagate}")


class WorkflowOrchestrator:
    """Orchestrates workflow execution for chat-originated intents"""
    
    def __init__(self, camara_base_url: str = "http://localhost:8003"):
        self.camara_base_url = camara_base_url
        self.active_workflows = {}
        
    async def execute_workflow(self, intent: Dict[str, Any], workflow_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow based on plan"""
        
        logger.info(f"WorkflowOrchestrator: Starting workflow execution for intent {intent['id']}")
        
        workflow_id = f"wf_{intent['id'][:8]}_{datetime.utcnow().strftime('%H%M%S')}"
        
        workflow_state = {
            "id": workflow_id,
            "intent_id": intent["id"],
            "status": "executing",
            "start_time": datetime.utcnow().isoformat(),
            "steps": workflow_plan["steps"].copy(),
            "results": {},
            "progress": 0
        }
        
        self.active_workflows[workflow_id] = workflow_state
        
        try:
            if workflow_plan["workflow_type"] == "fraud_detection":
                result = await self._execute_fraud_detection_workflow(intent, workflow_state)
            elif workflow_plan["workflow_type"] == "security_concern":
                result = await self._execute_security_workflow(intent, workflow_state)
            else:
                result = await self._execute_general_workflow(intent, workflow_state)
                
            workflow_state["status"] = "completed"
            workflow_state["end_time"] = datetime.utcnow().isoformat()
            workflow_state["progress"] = 100
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            workflow_state["status"] = "failed"
            workflow_state["error"] = str(e)
            workflow_state["end_time"] = datetime.utcnow().isoformat()
            
            return {
                "status": "error",
                "workflow_id": workflow_id,
                "error": str(e)
            }
    
    async def _execute_fraud_detection_workflow(self, intent: Dict[str, Any], workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fraud detection workflow"""
        
        logger.info("Starting fraud detection workflow execution")
        
        # Extract entities from intent analysis
        metadata = intent.get("metadata", {}).get("analysis", {})
        entities = metadata.get("entities_found", {})
        
        logger.info(f"Extracted entities: {entities}")
        
        # Get phone numbers from entities or use default for demo
        phone_numbers = entities.get("phone_numbers", [])
        customer_phone = phone_numbers[0] if phone_numbers else "+1-555-0123"
        
        results = {}
        
        # Step 1: SIM Swap Check
        logger.info(f"Step 1: Starting SIM swap check for {customer_phone}")
        await self._update_step_status(workflow_state, "sim_swap_check", "executing")
        sim_swap_result = await self._call_sim_swap_api(customer_phone)
        results["sim_swap"] = sim_swap_result
        await self._update_step_status(workflow_state, "sim_swap_check", "completed")
        workflow_state["progress"] = 20
        logger.info("Step 1: SIM swap check completed")
        
        # Step 2: Device Location Analysis
        logger.info(f"Step 2: Starting Device Location check for {customer_phone}")
        await self._update_step_status(workflow_state, "device_location_analysis", "executing")
        location_result = await self._call_location_api(customer_phone)
        results["location"] = location_result
        await self._update_step_status(workflow_state, "device_location_analysis", "completed")
        workflow_state["progress"] = 40
        logger.info("Step 2: Device Location check completed")
        
        # Step 3: Identity Verification
        logger.info(f"Step 3: Starting Identity Verification for {customer_phone}")
        await self._update_step_status(workflow_state, "identity_verification", "executing")
        kyc_result = await self._call_kyc_api(customer_phone, "Customer Name")
        results["kyc_verification"] = kyc_result
        await self._update_step_status(workflow_state, "identity_verification", "completed")
        workflow_state["progress"] = 60
        logger.info("Step 3: Identity Verification completed")
        
        # Step 4: Communication Analysis
        logger.info(f"Step 4: Starting Communication Analysis for {customer_phone}")
        await self._update_step_status(workflow_state, "communication_analysis", "executing")
        chat_text = json.loads(intent["expression"]["expressionValue"])["rawInput"]
        scam_result = await self._call_scam_signal_api(customer_phone, chat_text)
        results["scam_analysis"] = scam_result
        await self._update_step_status(workflow_state, "communication_analysis", "completed")
        workflow_state["progress"] = 80
        logger.info("Step 4: Communication Analysis completed")
        
        # Step 5: Risk Assessment
        logger
        await self._update_step_status(workflow_state, "risk_assessment", "executing")
        risk_assessment = await self._calculate_overall_risk(results)
        results["risk_assessment"] = risk_assessment
        await self._update_step_status(workflow_state, "risk_assessment", "completed")
        workflow_state["progress"] = 100
        logger.info("Step 5: Risk Assessment completed")
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(results, intent)
        
        return {
            "status": "success",
            "workflow_id": workflow_state["id"],
            "results": results,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "execution_time": self._calculate_execution_time(workflow_state)
        }
    
    async def _execute_security_workflow(self, intent: Dict[str, Any], workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute security concern workflow"""
        
        metadata = intent.get("metadata", {}).get("analysis", {})
        entities = metadata.get("entities_found", {})
        phone_numbers = entities.get("phone_numbers", [])
        customer_phone = phone_numbers[0] if phone_numbers else "+1-555-0123"
        
        results = {}
        
        # Security assessment
        await self._update_step_status(workflow_state, "security_assessment", "executing")
        chat_text = json.loads(intent["expression"]["expressionValue"])["rawInput"]
        security_analysis = await self._analyze_security_concern(chat_text)
        results["security_analysis"] = security_analysis
        await self._update_step_status(workflow_state, "security_assessment", "completed")
        workflow_state["progress"] = 50
        
        # Identity verification
        await self._update_step_status(workflow_state, "identity_verification", "executing")
        kyc_result = await self._call_kyc_api(customer_phone, "Customer Name")
        results["kyc_verification"] = kyc_result
        await self._update_step_status(workflow_state, "identity_verification", "completed")
        workflow_state["progress"] = 100
        
        recommendations = await self._generate_security_recommendations(results, intent)
        
        return {
            "status": "success",
            "workflow_id": workflow_state["id"],
            "results": results,
            "recommendations": recommendations,
            "execution_time": self._calculate_execution_time(workflow_state)
        }
    
    async def _execute_general_workflow(self, intent: Dict[str, Any], workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general inquiry workflow"""
        
        chat_text = json.loads(intent["expression"]["expressionValue"])["rawInput"]
        
        response = await self._generate_general_response(chat_text, intent)
        workflow_state["progress"] = 100
        
        return {
            "status": "success",
            "workflow_id": workflow_state["id"],
            "response": response,
            "execution_time": self._calculate_execution_time(workflow_state)
        }
    
    async def _call_sim_swap_api(self, phone_number: str) -> Dict[str, Any]:
        """Call SIM Swap API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.camara_base_url}/camara/sim-swap/v1/check",
                    json={"phone_number": phone_number, "max_age": 240}
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"SIM Swap API call failed: {e}")
            return {"error": str(e), "api": "sim-swap"}
    
    async def _call_location_api(self, phone_number: str) -> Dict[str, Any]:
        """Call Device Location API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.camara_base_url}/camara/location/v1/retrieve",
                    json={"device": {"phone_number": phone_number}}
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Location API call failed: {e}")
            return {"error": str(e), "api": "location"}
    
    async def _call_kyc_api(self, phone_number: str, name: str) -> Dict[str, Any]:
        """Call KYC Match API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.camara_base_url}/camara/kyc-match/v1/verify",
                    json={"phone_number": phone_number, "name": name}
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"KYC API call failed: {e}")
            return {"error": str(e), "api": "kyc-match"}
    
    async def _call_scam_signal_api(self, phone_number: str, content: str) -> Dict[str, Any]:
        """Call Scam Signal API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.camara_base_url}/camara/scam-signal/v1/analyze",
                    json={"phone_number": phone_number, "communication_content": content}
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Scam Signal API call failed: {e}")
            return {"error": str(e), "api": "scam-signal"}
    
    async def _calculate_overall_risk(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk assessment"""
        
        risk_factors = []
        risk_score = 0.0
        
        # SIM swap risk
        if "sim_swap" in results and not results["sim_swap"].get("error"):
            if results["sim_swap"].get("swapped", False):
                risk_factors.append("Recent SIM swap detected")
                risk_score += 0.4
            risk_score += results["sim_swap"].get("risk_score", 0) * 0.2
        
        # Location risk
        if "location" in results and not results["location"].get("error"):
            confidence = results["location"].get("confidence", 0)
            if confidence < 0.5:
                risk_factors.append("Low location confidence")
                risk_score += 0.2
        
        # KYC verification
        if "kyc_verification" in results and not results["kyc_verification"].get("error"):
            kyc_risk = results["kyc_verification"].get("risk_assessment", {}).get("risk_score", 0)
            risk_score += kyc_risk * 0.3
            
            if results["kyc_verification"].get("overall_match", {}).get("result") == "NO_MATCH":
                risk_factors.append("Identity verification failed")
                risk_score += 0.3
        
        # Scam signal analysis
        if "scam_analysis" in results and not results["scam_analysis"].get("error"):
            scam_score = results["scam_analysis"].get("overall_scam_score", 0)
            risk_score += scam_score * 0.4
            
            if scam_score > 0.5:
                risk_factors.append("High scam signal score")
        
        # Normalize risk score
        risk_score = min(risk_score, 1.0)
        
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "overall_risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "assessment_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_recommendations(self, results: Dict[str, Any], intent: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results"""
        
        recommendations = []
        risk_assessment = results.get("risk_assessment", {})
        risk_level = risk_assessment.get("risk_level", "low")
        
        if risk_level == "high":
            recommendations.extend([
                "⚠️ HIGH RISK: Immediate verification required",
                "🔒 Consider account temporary restrictions",
                "📞 Contact customer directly via verified phone",
                "🚨 Flag for manual security review"
            ])
        elif risk_level == "medium":
            recommendations.extend([
                "⚡ MEDIUM RISK: Additional verification recommended",
                "🔍 Monitor account activity closely",
                "📋 Document interaction for security team"
            ])
        else:
            recommendations.extend([
                "✅ LOW RISK: Standard processing acceptable",
                "📝 Log interaction for audit trail"
            ])
        
        # Add specific recommendations based on API results
        if results.get("sim_swap", {}).get("swapped"):
            recommendations.append("📱 Recent SIM swap detected - verify customer identity")
        
        if results.get("kyc_verification", {}).get("overall_match", {}).get("result") == "NO_MATCH":
            recommendations.append("🆔 Identity verification failed - require additional documentation")
        
        return recommendations
    
    async def _generate_security_recommendations(self, results: Dict[str, Any], intent: Dict[str, Any]) -> List[str]:
        """Generate security-specific recommendations"""
        
        return [
            "🔐 Security concern identified from chat message",
            "📋 Recommend customer education on security practices",
            "🔍 Monitor account for suspicious activity",
            "📞 Follow up with customer via verified contact method"
        ]
    
    async def _analyze_security_concern(self, chat_text: str) -> Dict[str, Any]:
        """Analyze security concern from chat"""
        
        security_keywords = ["hacked", "compromised", "breach", "stolen", "suspicious"]
        urgency_keywords = ["urgent", "immediate", "emergency"]
        
        found_keywords = [kw for kw in security_keywords if kw.lower() in chat_text.lower()]
        urgency_found = [kw for kw in urgency_keywords if kw.lower() in chat_text.lower()]
        
        return {
            "concern_type": "security_incident" if found_keywords else "general_security",
            "urgency_indicators": urgency_found,
            "security_keywords": found_keywords,
            "requires_immediate_attention": bool(urgency_found),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_general_response(self, chat_text: str, intent: Dict[str, Any]) -> str:
        """Generate general response for non-fraud/security intents"""
        
        if "help" in chat_text.lower():
            return "I can help you with fraud detection, security concerns, and intent management. What would you like assistance with?"
        elif "thank" in chat_text.lower():
            return "You're welcome! Is there anything else I can help you with regarding fraud detection or security?"
        else:
            return f"I've received your message: '{chat_text}'. How can I assist you with fraud detection or security concerns?"
    
    async def _update_step_status(self, workflow_state: Dict[str, Any], step_name: str, status: str):
        """Update workflow step status"""
        
        for step in workflow_state["steps"]:
            if step["step"] == step_name:
                step["status"] = status
                step["timestamp"] = datetime.utcnow().isoformat()
                break
    
    def _calculate_execution_time(self, workflow_state: Dict[str, Any]) -> str:
        """Calculate workflow execution time"""
        
        start_time = datetime.fromisoformat(workflow_state["start_time"])
        end_time = datetime.utcnow()
        duration = end_time - start_time
        
        return f"{duration.total_seconds():.2f} seconds"
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        
        return self.active_workflows.get(workflow_id)