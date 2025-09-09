from typing import Dict, List, Any
import asyncio
import httpx
from datetime import datetime, timedelta
import re

from ..base.base_agent import BaseAgent


class ScamSignalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="scam_signal_agent", 
            name="Scam Signal Detection Agent",
            description="Specialized agent for detecting social engineering and scam attempts using CAMARA Scam Signal API",
            capabilities=["scam_detection", "social_engineering_analysis", "communication_pattern_analysis", "threat_assessment"]
        )
        
        self.camara_base_url = "http://localhost:8001/camara"
        
    async def _initialize_agent(self) -> None:
        self.logger.info("Initializing Scam Signal Agent")
        
    async def _cleanup_agent(self) -> None:
        self.logger.info("Cleaning up Scam Signal Agent")
        
    async def execute_capability(self, capability_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if capability_type == "scam_detection":
            return await self._detect_scam(input_data)
        elif capability_type == "social_engineering_analysis":
            return await self._analyze_social_engineering(input_data)
        elif capability_type == "communication_pattern_analysis":
            return await self._analyze_communication_patterns(input_data)
        elif capability_type == "threat_assessment":
            return await self._assess_threat_level(input_data)
        else:
            raise ValueError(f"Unsupported capability: {capability_type}")
            
    async def _detect_scam(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number"])
        
        phone_number = input_data["phone_number"]
        communication_data = input_data.get("communication_data", {})
        
        self.logger.info(f"Detecting scam signals for {phone_number}")
        
        try:
            # Prepare scam detection request
            scam_request = {
                "phoneNumber": phone_number,
                "communicationData": communication_data
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.camara_base_url}/scam-signal/v1/check",
                    json=scam_request
                )
                response.raise_for_status()
                scam_data = response.json()
                
            # Analyze scam signals
            scam_analysis = self._analyze_scam_signals(scam_data, communication_data)
            
            return {
                "phone_number": phone_number,
                "scam_detected": scam_data.get("scamDetected", False),
                "scam_confidence": scam_data.get("confidence", 0.0),
                "scam_indicators": scam_data.get("indicators", []),
                "threat_level": scam_analysis["threat_level"],
                "analysis": scam_analysis["analysis"],
                "recommendations": scam_analysis["recommendations"],
                "confidence": 0.87
            }
            
        except Exception as e:
            self.logger.error(f"Scam detection failed: {e}")
            return {
                "phone_number": phone_number,
                "error": f"Scam detection failed: {str(e)}",
                "confidence": 0.0
            }
            
    async def _analyze_social_engineering(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["communication_content"])
        
        communication_content = input_data["communication_content"]
        phone_number = input_data.get("phone_number")
        communication_type = input_data.get("type", "unknown")  # call, sms, email
        
        # Analyze content for social engineering tactics
        se_analysis = self._detect_social_engineering_tactics(communication_content)
        
        # Get additional scam signal data if phone number provided
        additional_signals = {}
        if phone_number:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.camara_base_url}/scam-signal/v1/signals/{phone_number}"
                    )
                    response.raise_for_status()
                    additional_signals = response.json()
            except Exception:
                pass
                
        combined_analysis = self._combine_social_engineering_analysis(se_analysis, additional_signals)
        
        return {
            "phone_number": phone_number,
            "communication_type": communication_type,
            "social_engineering_detected": combined_analysis["detected"],
            "tactics_identified": combined_analysis["tactics"],
            "urgency_indicators": combined_analysis["urgency_indicators"],
            "trust_exploitation": combined_analysis["trust_indicators"],
            "risk_score": combined_analysis["risk_score"],
            "analysis": combined_analysis["analysis"],
            "confidence": 0.83,
            "recommendations": combined_analysis["recommendations"]
        }
        
    async def _analyze_communication_patterns(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number"])
        
        phone_number = input_data["phone_number"]
        time_window_hours = input_data.get("time_window_hours", 72)
        
        try:
            # Get communication pattern data
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.camara_base_url}/scam-signal/v1/patterns/{phone_number}",
                    params={"hours": time_window_hours}
                )
                response.raise_for_status()
                pattern_data = response.json()
                
            pattern_analysis = self._analyze_patterns(pattern_data)
            
            return {
                "phone_number": phone_number,
                "time_window_hours": time_window_hours,
                "communication_patterns": pattern_analysis,
                "anomaly_score": pattern_analysis.get("anomaly_score", 0.0),
                "suspicious_patterns": pattern_analysis.get("suspicious_patterns", []),
                "confidence": 0.80
            }
            
        except Exception as e:
            self.logger.error(f"Communication pattern analysis failed: {e}")
            return {
                "phone_number": phone_number,
                "error": f"Pattern analysis failed: {str(e)}",
                "confidence": 0.0
            }
            
    async def _assess_threat_level(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number"])
        
        phone_number = input_data["phone_number"]
        context = input_data.get("context", {})
        
        # Gather all available scam signal data
        scam_result = await self._detect_scam({"phone_number": phone_number})
        
        if "error" in scam_result:
            return scam_result
            
        # Get communication patterns
        pattern_result = await self._analyze_communication_patterns({"phone_number": phone_number})
        
        # Calculate comprehensive threat assessment
        threat_assessment = self._calculate_threat_level(scam_result, pattern_result, context)
        
        return {
            "phone_number": phone_number,
            "overall_threat_level": threat_assessment["level"],
            "threat_score": threat_assessment["score"],
            "contributing_factors": threat_assessment["factors"],
            "scam_signals": scam_result,
            "pattern_analysis": pattern_result,
            "urgency": threat_assessment["urgency"],
            "confidence": 0.85,
            "recommendations": threat_assessment["recommendations"]
        }
        
    def _analyze_scam_signals(self, scam_data: Dict[str, Any], 
                            communication_data: Dict[str, Any]) -> Dict[str, Any]:
        scam_detected = scam_data.get("scamDetected", False)
        confidence = scam_data.get("confidence", 0.0)
        indicators = scam_data.get("indicators", [])
        
        # Determine threat level
        if scam_detected and confidence > 0.8:
            threat_level = "HIGH"
        elif scam_detected and confidence > 0.5:
            threat_level = "MEDIUM"
        elif indicators:
            threat_level = "LOW"
        else:
            threat_level = "MINIMAL"
            
        # Generate analysis
        if scam_detected:
            analysis = f"Scam detected with {confidence:.1%} confidence. Indicators: {', '.join(indicators)}"
        else:
            analysis = "No significant scam indicators detected in communication patterns."
            
        # Generate recommendations
        recommendations = self._generate_scam_recommendations(threat_level, indicators)
        
        return {
            "threat_level": threat_level,
            "analysis": analysis,
            "recommendations": recommendations
        }
        
    def _detect_social_engineering_tactics(self, content: str) -> Dict[str, Any]:
        content_lower = content.lower()
        
        # Define social engineering indicators
        urgency_patterns = [
            r"urgent", r"immediately", r"expire", r"suspend", r"terminate",
            r"within \d+ hours?", r"deadline", r"act now", r"time[- ]sensitive"
        ]
        
        authority_patterns = [
            r"bank", r"police", r"government", r"irs", r"fbi", r"security team",
            r"support team", r"microsoft", r"apple", r"google", r"amazon"
        ]
        
        fear_patterns = [
            r"account.{0,20}suspend", r"unauthorized.{0,20}access", r"security.{0,20}breach",
            r"fraud.{0,20}detect", r"virus.{0,20}detect", r"hack", r"steal"
        ]
        
        information_requests = [
            r"password", r"pin", r"ssn", r"social security", r"credit card",
            r"banking.{0,20}detail", r"account.{0,20}number", r"verify.{0,20}identity"
        ]
        
        trust_indicators = [
            r"verify your account", r"confirm your identity", r"security purposes",
            r"protect your account", r"for your safety"
        ]
        
        # Count matches
        urgency_matches = sum(1 for pattern in urgency_patterns if re.search(pattern, content_lower))
        authority_matches = sum(1 for pattern in authority_patterns if re.search(pattern, content_lower))
        fear_matches = sum(1 for pattern in fear_patterns if re.search(pattern, content_lower))
        info_matches = sum(1 for pattern in information_requests if re.search(pattern, content_lower))
        trust_matches = sum(1 for pattern in trust_indicators if re.search(pattern, content_lower))
        
        # Identify tactics
        tactics = []
        if urgency_matches > 0:
            tactics.append("urgency_pressure")
        if authority_matches > 0:
            tactics.append("authority_impersonation")
        if fear_matches > 0:
            tactics.append("fear_intimidation")
        if info_matches > 0:
            tactics.append("information_harvesting")
        if trust_matches > 0:
            tactics.append("trust_exploitation")
            
        # Calculate risk score
        total_indicators = urgency_matches + authority_matches + fear_matches + info_matches + trust_matches
        risk_score = min(total_indicators * 0.15, 1.0)
        
        return {
            "urgency_indicators": urgency_matches,
            "authority_indicators": authority_matches,
            "fear_indicators": fear_matches,
            "information_requests": info_matches,
            "trust_indicators": trust_matches,
            "tactics": tactics,
            "risk_score": risk_score,
            "total_indicators": total_indicators
        }
        
    def _combine_social_engineering_analysis(self, content_analysis: Dict[str, Any],
                                           signals: Dict[str, Any]) -> Dict[str, Any]:
        tactics = content_analysis.get("tactics", [])
        base_risk = content_analysis.get("risk_score", 0.0)
        
        # Enhance analysis with signal data
        if signals.get("reportedAsScam"):
            base_risk += 0.3
            tactics.append("previously_reported")
            
        if signals.get("suspiciousPatterns"):
            base_risk += 0.2
            
        final_risk = min(base_risk, 1.0)
        
        # Determine if social engineering detected
        detected = final_risk > 0.3 or len(tactics) >= 2
        
        # Generate analysis
        if detected:
            analysis = f"Social engineering tactics detected: {', '.join(tactics)}. Risk score: {final_risk:.2f}"
        else:
            analysis = "No significant social engineering indicators found."
            
        recommendations = self._generate_social_engineering_recommendations(final_risk, tactics)
        
        return {
            "detected": detected,
            "tactics": tactics,
            "urgency_indicators": content_analysis.get("urgency_indicators", 0),
            "trust_indicators": content_analysis.get("trust_indicators", 0),
            "risk_score": final_risk,
            "analysis": analysis,
            "recommendations": recommendations
        }
        
    def _analyze_patterns(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        patterns = pattern_data.get("patterns", {})
        
        suspicious_patterns = []
        anomaly_score = 0.0
        
        # Check for suspicious call patterns
        call_count = patterns.get("callCount", 0)
        if call_count > 50:  # Excessive calls
            suspicious_patterns.append("excessive_call_volume")
            anomaly_score += 0.3
            
        # Check for blast patterns (many numbers called)
        unique_targets = patterns.get("uniqueTargets", 0)
        if unique_targets > 100:
            suspicious_patterns.append("blast_calling_pattern")
            anomaly_score += 0.4
            
        # Check for short duration calls (robocalls)
        avg_duration = patterns.get("averageCallDuration", 0)
        if avg_duration < 10 and call_count > 10:  # Less than 10 seconds average
            suspicious_patterns.append("short_duration_calls")
            anomaly_score += 0.2
            
        # Check for non-business hours activity
        night_calls = patterns.get("nightTimeCalls", 0)
        if night_calls > call_count * 0.5:  # More than 50% at night
            suspicious_patterns.append("unusual_timing_patterns")
            anomaly_score += 0.2
            
        # Check for sequential number dialing
        if patterns.get("sequentialDialing", False):
            suspicious_patterns.append("sequential_number_dialing")
            anomaly_score += 0.3
            
        anomaly_score = min(anomaly_score, 1.0)
        
        return {
            "call_volume": call_count,
            "unique_targets": unique_targets,
            "average_duration": avg_duration,
            "suspicious_patterns": suspicious_patterns,
            "anomaly_score": anomaly_score,
            "pattern_confidence": 0.75
        }
        
    def _calculate_threat_level(self, scam_result: Dict[str, Any], 
                              pattern_result: Dict[str, Any],
                              context: Dict[str, Any]) -> Dict[str, Any]:
        factors = []
        total_score = 0.0
        
        # Scam detection factors
        if scam_result.get("scam_detected"):
            scam_confidence = scam_result.get("scam_confidence", 0.0)
            total_score += scam_confidence * 0.4
            factors.append(f"Scam detected ({scam_confidence:.1%} confidence)")
            
        # Pattern analysis factors
        if not pattern_result.get("error"):
            anomaly_score = pattern_result.get("anomaly_score", 0.0)
            total_score += anomaly_score * 0.3
            
            suspicious_patterns = pattern_result.get("suspicious_patterns", [])
            if suspicious_patterns:
                factors.append(f"Suspicious communication patterns: {', '.join(suspicious_patterns)}")
                
        # Context factors
        if context.get("multiple_reports"):
            total_score += 0.2
            factors.append("Multiple user reports received")
            
        if context.get("known_scammer_number"):
            total_score += 0.5
            factors.append("Number appears on known scammer lists")
            
        total_score = min(total_score, 1.0)
        
        # Determine threat level and urgency
        if total_score >= 0.8:
            level = "CRITICAL"
            urgency = "IMMEDIATE"
        elif total_score >= 0.6:
            level = "HIGH" 
            urgency = "HIGH"
        elif total_score >= 0.4:
            level = "MEDIUM"
            urgency = "MEDIUM"
        elif total_score >= 0.2:
            level = "LOW"
            urgency = "LOW"
        else:
            level = "MINIMAL"
            urgency = "NONE"
            
        recommendations = self._generate_threat_recommendations(level, factors)
        
        return {
            "level": level,
            "score": round(total_score, 3),
            "factors": factors,
            "urgency": urgency,
            "recommendations": recommendations
        }
        
    def _generate_scam_recommendations(self, threat_level: str, indicators: List[str]) -> List[str]:
        if threat_level == "HIGH":
            return [
                "URGENT: Block number immediately",
                "Report to fraud prevention systems",
                "Alert affected customers",
                "Coordinate with law enforcement if needed"
            ]
        elif threat_level == "MEDIUM":
            return [
                "Monitor number for additional activity",
                "Apply enhanced screening",
                "Consider temporary restrictions",
                "Document indicators for pattern analysis"
            ]
        elif threat_level == "LOW":
            return [
                "Continue monitoring",
                "Log indicators for trend analysis",
                "Apply standard fraud prevention measures"
            ]
        else:
            return ["Maintain standard monitoring procedures"]
            
    def _generate_social_engineering_recommendations(self, risk_score: float, 
                                                   tactics: List[str]) -> List[str]:
        if risk_score >= 0.7:
            return [
                "HIGH RISK: Likely social engineering attempt",
                "Do not provide any personal information",
                "Block communication immediately",
                "Report to security team",
                "Educate users about these tactics"
            ]
        elif risk_score >= 0.4:
            return [
                "Potential social engineering detected",
                "Verify sender through alternative channels",
                "Exercise extreme caution",
                "Do not click links or provide information"
            ]
        else:
            return [
                "Standard security awareness applies",
                "Verify unusual requests independently"
            ]
            
    def _generate_threat_recommendations(self, level: str, factors: List[str]) -> List[str]:
        if level == "CRITICAL":
            return [
                "IMMEDIATE ACTION REQUIRED",
                "Block number across all systems",
                "Alert security operations center",
                "Implement emergency fraud protocols",
                "Consider legal action"
            ]
        elif level == "HIGH":
            return [
                "High priority threat response",
                "Block number and monitor closely",
                "Alert fraud prevention team",
                "Implement enhanced customer protections"
            ]
        elif level == "MEDIUM":
            return [
                "Moderate threat response",
                "Enhanced monitoring and logging",
                "Consider proactive customer notifications",
                "Review and update detection rules"
            ]
        else:
            return [
                "Standard monitoring procedures",
                "Continue pattern analysis",
                "Document for trend tracking"
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
                "scam_detection",
                "social_engineering_analysis",
                "communication_pattern_analysis",
                "threat_assessment"
            ]
        }