from typing import Dict, List, Any
import asyncio
import httpx
from datetime import datetime, timedelta
import random

from ..base.base_agent import BaseAgent


class SimSwapAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="sim_swap_agent",
            name="SIM Swap Detection Agent",
            description="Specialized agent for detecting SIM swap fraud using CAMARA SIM Swap API",
            capabilities=["sim_swap_detection", "sim_history_analysis", "fraud_risk_assessment"]
        )
        
        self.camara_base_url = "http://localhost:8001/camara"
        
    async def _initialize_agent(self) -> None:
        self.logger.info("Initializing SIM Swap Agent")
        
    async def _cleanup_agent(self) -> None:
        self.logger.info("Cleaning up SIM Swap Agent")
        
    async def execute_capability(self, capability_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if capability_type == "sim_swap_detection":
            return await self._detect_sim_swap(input_data)
        elif capability_type == "sim_history_analysis":
            return await self._analyze_sim_history(input_data)
        elif capability_type == "fraud_risk_assessment":
            return await self._assess_fraud_risk(input_data)
        else:
            raise ValueError(f"Unsupported capability: {capability_type}")
            
    async def _detect_sim_swap(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number"])
        
        phone_number = input_data["phone_number"]
        max_age_hours = input_data.get("max_age_hours", 240)  # 10 days default
        
        self.logger.info(f"Checking SIM swap status for {phone_number}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.camara_base_url}/sim-swap/v1/retrieve-date",
                    json={
                        "phoneNumber": phone_number,
                        "maxAge": max_age_hours
                    }
                )
                response.raise_for_status()
                sim_data = response.json()
                
            # Calculate risk based on swap recency and patterns
            risk_level = self._calculate_swap_risk(sim_data)
            
            return {
                "phone_number": phone_number,
                "sim_swap_detected": sim_data.get("swapped", False),
                "last_swap_date": sim_data.get("latestSimChange"),
                "risk_level": risk_level,
                "confidence": 0.92,
                "analysis": self._generate_swap_analysis(sim_data, risk_level),
                "recommendations": self._generate_swap_recommendations(risk_level)
            }
            
        except Exception as e:
            self.logger.error(f"SIM swap detection failed: {e}")
            return {
                "phone_number": phone_number,
                "error": f"SIM swap detection failed: {str(e)}",
                "confidence": 0.0
            }
            
    async def _analyze_sim_history(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number"])
        
        phone_number = input_data["phone_number"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.camara_base_url}/sim-swap/v1/history/{phone_number}"
                )
                response.raise_for_status()
                history_data = response.json()
                
            analysis = self._analyze_swap_patterns(history_data)
            
            return {
                "phone_number": phone_number,
                "swap_history": history_data.get("history", []),
                "pattern_analysis": analysis,
                "total_swaps": len(history_data.get("history", [])),
                "confidence": 0.88
            }
            
        except Exception as e:
            self.logger.error(f"SIM history analysis failed: {e}")
            return {
                "phone_number": phone_number,
                "error": f"History analysis failed: {str(e)}",
                "confidence": 0.0
            }
            
    async def _assess_fraud_risk(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number"])
        
        phone_number = input_data["phone_number"]
        context = input_data.get("context", {})
        
        # Get SIM swap data
        sim_result = await self._detect_sim_swap({"phone_number": phone_number})
        
        if "error" in sim_result:
            return sim_result
            
        # Calculate comprehensive fraud risk
        risk_factors = []
        overall_risk = 0.0
        
        # Recent SIM swap factor
        if sim_result.get("sim_swap_detected"):
            risk_factors.append("Recent SIM swap detected")
            overall_risk += 0.4
            
        # Risk level from swap analysis
        swap_risk = sim_result.get("risk_level", 0)
        overall_risk += swap_risk * 0.3
        
        # Context-based factors
        if context.get("suspicious_activity"):
            risk_factors.append("Suspicious account activity reported")
            overall_risk += 0.2
            
        if context.get("recent_password_changes"):
            risk_factors.append("Recent password changes detected")
            overall_risk += 0.1
            
        overall_risk = min(overall_risk, 1.0)
        
        return {
            "phone_number": phone_number,
            "fraud_risk_score": round(overall_risk, 3),
            "risk_category": self._categorize_risk(overall_risk),
            "risk_factors": risk_factors,
            "sim_swap_data": sim_result,
            "confidence": 0.87,
            "recommendations": self._generate_fraud_recommendations(overall_risk)
        }
        
    def _calculate_swap_risk(self, sim_data: Dict[str, Any]) -> float:
        if not sim_data.get("swapped", False):
            return 0.0
            
        last_swap = sim_data.get("latestSimChange")
        if not last_swap:
            return 0.0
            
        try:
            swap_date = datetime.fromisoformat(last_swap.replace('Z', '+00:00'))
            hours_since_swap = (datetime.now() - swap_date.replace(tzinfo=None)).total_seconds() / 3600
            
            # Higher risk for more recent swaps
            if hours_since_swap < 24:
                return 0.9
            elif hours_since_swap < 72:
                return 0.7
            elif hours_since_swap < 168:  # 1 week
                return 0.5
            else:
                return 0.3
                
        except Exception:
            return 0.4
            
    def _analyze_swap_patterns(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        history = history_data.get("history", [])
        
        if not history:
            return {"pattern": "no_history", "risk_indicators": []}
            
        # Analyze swap frequency
        swap_count = len(history)
        risk_indicators = []
        
        if swap_count > 5:
            risk_indicators.append("High frequency of SIM swaps")
        elif swap_count > 2:
            risk_indicators.append("Multiple SIM swaps detected")
            
        # Check for rapid succession swaps
        if len(history) >= 2:
            try:
                recent_swaps = sorted(history, key=lambda x: x.get("date", ""), reverse=True)[:3]
                dates = []
                for swap in recent_swaps:
                    if swap.get("date"):
                        dates.append(datetime.fromisoformat(swap["date"].replace('Z', '+00:00')))
                        
                if len(dates) >= 2:
                    time_diff = (dates[0] - dates[1]).total_seconds() / 3600
                    if time_diff < 72:  # Less than 3 days
                        risk_indicators.append("Rapid succession SIM swaps")
                        
            except Exception:
                pass
                
        return {
            "swap_frequency": "high" if swap_count > 3 else "normal",
            "risk_indicators": risk_indicators,
            "pattern_confidence": 0.85
        }
        
    def _categorize_risk(self, risk_score: float) -> str:
        if risk_score >= 0.8:
            return "HIGH"
        elif risk_score >= 0.5:
            return "MEDIUM"
        elif risk_score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"
            
    def _generate_swap_analysis(self, sim_data: Dict[str, Any], risk_level: float) -> str:
        if not sim_data.get("swapped", False):
            return "No recent SIM swap activity detected for this phone number."
            
        last_swap = sim_data.get("latestSimChange", "unknown")
        
        if risk_level >= 0.7:
            return f"HIGH RISK: Recent SIM swap detected on {last_swap}. This indicates potential SIM swap fraud."
        elif risk_level >= 0.5:
            return f"MEDIUM RISK: SIM swap detected on {last_swap}. Monitor for suspicious activity."
        else:
            return f"LOW RISK: SIM swap detected on {last_swap}, but timing suggests legitimate activity."
            
    def _generate_swap_recommendations(self, risk_level: float) -> List[str]:
        if risk_level >= 0.7:
            return [
                "Immediately verify customer identity through multiple channels",
                "Temporarily suspend high-risk account activities",
                "Implement additional authentication requirements",
                "Monitor for unauthorized account access attempts"
            ]
        elif risk_level >= 0.5:
            return [
                "Verify recent SIM swap was customer-initiated",
                "Enable enhanced monitoring for account activities",
                "Consider requiring additional verification for sensitive operations"
            ]
        else:
            return [
                "Continue standard monitoring procedures",
                "Document SIM swap for historical tracking"
            ]
            
    def _generate_fraud_recommendations(self, risk_score: float) -> List[str]:
        if risk_score >= 0.8:
            return [
                "URGENT: Implement immediate account security measures",
                "Block high-risk transactions and activities",
                "Require in-person identity verification",
                "Coordinate with fraud investigation team"
            ]
        elif risk_score >= 0.5:
            return [
                "Enhance account monitoring and alerting",
                "Require additional authentication for sensitive operations",
                "Review recent account activities for anomalies"
            ]
        else:
            return [
                "Continue standard fraud monitoring",
                "Maintain awareness of SIM swap risk factors"
            ]
            
    async def _get_agent_health(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.camara_base_url}/health")
                camara_status = response.status_code == 200
        except Exception:
            camara_status = False
            
        return {
            "camara_api_connection": camara_status,
            "supported_operations": [
                "sim_swap_detection",
                "sim_history_analysis", 
                "fraud_risk_assessment"
            ]
        }