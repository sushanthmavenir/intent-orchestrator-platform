import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx
import random
import json

from ..base.base_agent import BaseAgent


class FraudDetectionAgent(BaseAgent):
    """
    Specialized agent for fraud detection using CAMARA APIs
    Coordinates multiple fraud detection capabilities and risk assessment
    """
    
    def __init__(self, agent_id: str = "fraud-detector-001"):
        super().__init__(
            agent_id=agent_id,
            name="Advanced Fraud Detection Agent",
            description="AI-powered fraud detection with ML models and CAMARA API integration",
            capabilities=[
                "fraud_detection",
                "risk_scoring", 
                "transaction_analysis",
                "pattern_recognition"
            ]
        )
        
        # Fraud detection thresholds and settings
        self.risk_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8,
            "critical": 0.9
        }
        
        # CAMARA API endpoints
        self.camara_endpoints = {
            "device_swap": "http://localhost:8000/camara/device-swap/v1/check",
            "sim_swap": "http://localhost:8000/camara/sim-swap/v1/check",
            "location": "http://localhost:8000/camara/location/v1/retrieve",
            "kyc_match": "http://localhost:8000/camara/kyc-match/v1/verify",
            "scam_signal": "http://localhost:8000/camara/scam-signal/v1/analyze"
        }
        
        # Fraud patterns database
        self.fraud_patterns = {
            "sim_swap_fraud": {
                "weight": 0.9,
                "indicators": ["recent_sim_swap", "location_anomaly", "device_change"]
            },
            "account_takeover": {
                "weight": 0.85,
                "indicators": ["multiple_login_attempts", "new_device", "password_reset"]
            },
            "social_engineering": {
                "weight": 0.8,
                "indicators": ["urgent_requests", "authority_impersonation", "information_harvesting"]
            },
            "transaction_fraud": {
                "weight": 0.75,
                "indicators": ["unusual_amount", "new_payee", "time_anomaly"]
            }
        }
    
    async def _initialize_agent(self) -> None:
        """Initialize fraud detection models and data"""
        self.logger.info("Initializing fraud detection models...")
        
        # Simulate ML model loading
        await asyncio.sleep(0.5)
        
        # Load fraud detection rules
        self.fraud_rules = self._load_fraud_rules()
        
        # Initialize statistical models (mock)
        self.anomaly_detector = self._initialize_anomaly_detector()
        
        self.logger.info("Fraud detection agent initialized successfully")
    
    async def _cleanup_agent(self) -> None:
        """Cleanup fraud detection resources"""
        self.logger.info("Cleaning up fraud detection resources")
    
    async def execute_capability(self, capability_type: str, 
                               input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fraud detection capabilities"""
        
        if capability_type == "fraud_detection":
            return await self._detect_fraud(input_data)
        elif capability_type == "risk_scoring":
            return await self._calculate_risk_score(input_data)
        elif capability_type == "transaction_analysis":
            return await self._analyze_transaction(input_data)
        elif capability_type == "pattern_recognition":
            return await self._recognize_patterns(input_data)
        else:
            raise ValueError(f"Unknown capability: {capability_type}")
    
    async def _detect_fraud(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive fraud detection using multiple data sources"""
        
        # Validate required inputs
        await self.validate_input(input_data, ["customer_id"])
        
        customer_id = input_data["customer_id"]
        phone_number = input_data.get("phone_number")
        transaction_data = input_data.get("transaction_data", {})
        
        self.logger.info(f"Detecting fraud for customer {customer_id}")
        
        # Initialize fraud analysis results
        analysis_results = {
            "customer_id": customer_id,
            "phone_number": phone_number,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "fraud_indicators": [],
            "risk_factors": [],
            "camara_checks": {},
            "overall_risk_score": 0.0,
            "recommendation": "allow",
            "confidence": 0.0
        }
        
        # Perform CAMARA API checks if phone number is available
        if phone_number:
            camara_results = await self._perform_camara_checks(phone_number)
            analysis_results["camara_checks"] = camara_results
            
            # Analyze CAMARA results for fraud indicators
            camara_indicators = self._analyze_camara_results(camara_results)
            analysis_results["fraud_indicators"].extend(camara_indicators)
        
        # Analyze transaction patterns
        if transaction_data:
            transaction_analysis = await self._analyze_transaction_patterns(transaction_data)
            analysis_results["transaction_analysis"] = transaction_analysis
            analysis_results["fraud_indicators"].extend(
                transaction_analysis.get("indicators", [])
            )
        
        # Perform behavioral analysis
        behavioral_analysis = await self._analyze_behavior_patterns(input_data)
        analysis_results["behavioral_analysis"] = behavioral_analysis
        analysis_results["fraud_indicators"].extend(
            behavioral_analysis.get("indicators", [])
        )
        
        # Calculate overall risk score
        risk_score = self._calculate_overall_risk_score(analysis_results)
        analysis_results["overall_risk_score"] = risk_score
        
        # Determine recommendation
        recommendation, confidence = self._determine_fraud_recommendation(
            risk_score, analysis_results["fraud_indicators"]
        )
        analysis_results["recommendation"] = recommendation
        analysis_results["confidence"] = confidence
        
        # Generate detailed explanation
        analysis_results["explanation"] = self._generate_fraud_explanation(analysis_results)
        
        return analysis_results
    
    async def _perform_camara_checks(self, phone_number: str) -> Dict[str, Any]:
        """Perform comprehensive CAMARA API checks"""
        camara_results = {}
        
        try:
            # Device Swap Check
            device_swap_data = {"phone_number": phone_number, "max_age": 240}
            device_swap_response = await self._call_camara_api(
                "device_swap", device_swap_data
            )
            camara_results["device_swap"] = device_swap_response
            
            # SIM Swap Check
            sim_swap_data = {"phone_number": phone_number, "max_age": 240}
            sim_swap_response = await self._call_camara_api(
                "sim_swap", sim_swap_data
            )
            camara_results["sim_swap"] = sim_swap_response
            
            # Location Check
            location_data = {"device": phone_number, "max_age": 60}
            location_response = await self._call_camara_api(
                "location", location_data
            )
            camara_results["location"] = location_response
            
            # Scam Signal Check
            scam_data = {
                "phone_number": phone_number,
                "analysis_period_hours": 24,
                "include_call_patterns": True,
                "include_message_patterns": True
            }
            scam_response = await self._call_camara_api(
                "scam_signal", scam_data
            )
            camara_results["scam_signal"] = scam_response
            
        except Exception as e:
            self.logger.error(f"CAMARA API checks failed: {e}")
            camara_results["error"] = str(e)
        
        return camara_results
    
    async def _call_camara_api(self, api_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call to CAMARA endpoint"""
        endpoint = self.camara_endpoints.get(api_type)
        if not endpoint:
            raise ValueError(f"Unknown CAMARA API type: {api_type}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=data, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            self.logger.error(f"CAMARA API {api_type} failed: {e}")
            return {"error": str(e)}
    
    def _analyze_camara_results(self, camara_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze CAMARA API results for fraud indicators"""
        indicators = []
        
        # Analyze Device Swap results
        device_swap = camara_results.get("device_swap", {})
        if device_swap.get("swapped") and device_swap.get("confidence", 0) > 0.7:
            indicators.append({
                "type": "recent_device_swap",
                "severity": "high" if device_swap.get("risk_level") == "high" else "medium",
                "confidence": device_swap.get("confidence", 0),
                "details": f"Device swap detected {device_swap.get('swap_date')}",
                "source": "camara_device_swap"
            })
        
        # Analyze SIM Swap results
        sim_swap = camara_results.get("sim_swap", {})
        if sim_swap.get("swapped") and sim_swap.get("risk_score", 0) > 0.6:
            indicators.append({
                "type": "recent_sim_swap",
                "severity": "critical" if sim_swap.get("risk_score") > 0.8 else "high",
                "confidence": sim_swap.get("confidence", 0),
                "details": f"SIM swap detected {sim_swap.get('swap_date')}",
                "source": "camara_sim_swap"
            })
        
        # Analyze Location results
        location = camara_results.get("location", {})
        if location.get("metadata", {}).get("movement_detected"):
            indicators.append({
                "type": "unusual_location",
                "severity": "medium",
                "confidence": location.get("confidence", 0),
                "details": f"Unusual location detected: {location.get('city')}",
                "source": "camara_location"
            })
        
        # Analyze Scam Signal results
        scam_signal = camara_results.get("scam_signal", {})
        if scam_signal.get("overall_scam_score", 0) > 0.5:
            indicators.append({
                "type": "scam_signals_detected",
                "severity": scam_signal.get("risk_level", "medium"),
                "confidence": scam_signal.get("overall_scam_score", 0),
                "details": f"Scam patterns detected with {len(scam_signal.get('scam_indicators', []))} indicators",
                "source": "camara_scam_signal"
            })
        
        return indicators
    
    async def _analyze_transaction_patterns(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transaction patterns for fraud indicators"""
        
        analysis = {
            "indicators": [],
            "anomalies": [],
            "risk_factors": []
        }
        
        amount = transaction_data.get("amount", 0)
        recipient = transaction_data.get("recipient")
        time_of_day = transaction_data.get("timestamp", datetime.utcnow()).hour
        transaction_type = transaction_data.get("type", "transfer")
        
        # Check for unusual amounts
        if amount > 10000:  # High amount threshold
            analysis["indicators"].append({
                "type": "high_amount_transaction",
                "severity": "high",
                "confidence": 0.8,
                "details": f"Transaction amount ${amount} exceeds normal threshold",
                "source": "transaction_analysis"
            })
        
        # Check for unusual timing
        if time_of_day < 6 or time_of_day > 23:  # Outside normal hours
            analysis["indicators"].append({
                "type": "unusual_time",
                "severity": "medium",
                "confidence": 0.6,
                "details": f"Transaction at {time_of_day}:00 outside normal hours",
                "source": "transaction_analysis"
            })
        
        # Check for new recipient (mock logic)
        if recipient and random.random() < 0.3:  # 30% chance of new recipient
            analysis["indicators"].append({
                "type": "new_recipient",
                "severity": "medium",
                "confidence": 0.7,
                "details": f"First transaction to recipient {recipient}",
                "source": "transaction_analysis"
            })
        
        return analysis
    
    async def _analyze_behavior_patterns(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns for fraud indicators"""
        
        analysis = {
            "indicators": [],
            "behavioral_score": 0.0,
            "patterns": []
        }
        
        # Mock behavioral analysis
        customer_id = input_data["customer_id"]
        
        # Simulate different behavioral patterns based on customer ID
        if hash(customer_id) % 10 < 2:  # 20% chance of suspicious behavior
            analysis["indicators"].append({
                "type": "unusual_login_pattern",
                "severity": "medium",
                "confidence": 0.7,
                "details": "Multiple login attempts from different locations",
                "source": "behavioral_analysis"
            })
            analysis["behavioral_score"] += 0.3
        
        if hash(customer_id) % 15 < 1:  # ~7% chance of high-risk behavior
            analysis["indicators"].append({
                "type": "rapid_successive_actions",
                "severity": "high",
                "confidence": 0.8,
                "details": "Unusually rapid sequence of account actions",
                "source": "behavioral_analysis"
            })
            analysis["behavioral_score"] += 0.5
        
        return analysis
    
    def _calculate_overall_risk_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall fraud risk score"""
        base_score = 0.1  # Baseline risk
        
        # Weight fraud indicators
        for indicator in analysis_results["fraud_indicators"]:
            severity = indicator.get("severity", "low")
            confidence = indicator.get("confidence", 0.5)
            
            severity_weights = {
                "low": 0.1,
                "medium": 0.3,
                "high": 0.5,
                "critical": 0.8
            }
            
            weight = severity_weights.get(severity, 0.1)
            base_score += weight * confidence
        
        # Factor in CAMARA results
        camara_checks = analysis_results.get("camara_checks", {})
        
        # SIM swap is critical
        sim_swap = camara_checks.get("sim_swap", {})
        if sim_swap.get("swapped"):
            base_score += sim_swap.get("risk_score", 0) * 0.7
        
        # Scam signals are significant
        scam_signal = camara_checks.get("scam_signal", {})
        base_score += scam_signal.get("overall_scam_score", 0) * 0.5
        
        # Behavioral analysis
        behavioral = analysis_results.get("behavioral_analysis", {})
        base_score += behavioral.get("behavioral_score", 0) * 0.4
        
        return min(1.0, base_score)
    
    def _determine_fraud_recommendation(self, risk_score: float, 
                                      indicators: List[Dict[str, Any]]) -> tuple[str, float]:
        """Determine fraud prevention recommendation"""
        
        # Count critical and high severity indicators
        critical_count = sum(1 for ind in indicators if ind.get("severity") == "critical")
        high_count = sum(1 for ind in indicators if ind.get("severity") == "high")
        
        if risk_score > 0.9 or critical_count >= 2:
            return "block", 0.95
        elif risk_score > 0.7 or critical_count >= 1 or high_count >= 3:
            return "review", 0.85
        elif risk_score > 0.5 or high_count >= 1:
            return "monitor", 0.75
        else:
            return "allow", 0.8
    
    def _generate_fraud_explanation(self, analysis_results: Dict[str, Any]) -> str:
        """Generate human-readable explanation of fraud analysis"""
        risk_score = analysis_results["overall_risk_score"]
        recommendation = analysis_results["recommendation"]
        indicators = analysis_results["fraud_indicators"]
        
        explanation = f"Fraud analysis completed with risk score {risk_score:.2f}. "
        explanation += f"Recommendation: {recommendation.upper()}. "
        
        if indicators:
            explanation += f"Found {len(indicators)} fraud indicators: "
            indicator_summaries = []
            for ind in indicators[:3]:  # Top 3 indicators
                indicator_summaries.append(f"{ind['type']} ({ind['severity']} severity)")
            explanation += ", ".join(indicator_summaries)
            
            if len(indicators) > 3:
                explanation += f" and {len(indicators) - 3} others"
        else:
            explanation += "No significant fraud indicators detected."
        
        return explanation
    
    async def _calculate_risk_score(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed risk score breakdown"""
        
        # Simplified risk scoring for demonstration
        base_risk = 0.2
        
        # Factor in various risk components
        risk_components = {
            "account_age": random.uniform(0.0, 0.2),
            "transaction_history": random.uniform(0.0, 0.3),
            "device_trust": random.uniform(0.0, 0.4),
            "location_consistency": random.uniform(0.0, 0.2),
            "behavioral_patterns": random.uniform(0.0, 0.3)
        }
        
        total_risk = base_risk + sum(risk_components.values())
        total_risk = min(1.0, total_risk)
        
        return {
            "overall_risk_score": total_risk,
            "risk_level": self._get_risk_level(total_risk),
            "risk_components": risk_components,
            "confidence": 0.8,
            "explanation": f"Risk score {total_risk:.2f} based on multiple factors"
        }
    
    async def _analyze_transaction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual transaction for fraud"""
        
        transaction = input_data.get("transaction", {})
        
        return {
            "transaction_id": transaction.get("id", "unknown"),
            "risk_score": random.uniform(0.1, 0.9),
            "anomalies": ["unusual_amount", "new_merchant"] if random.random() < 0.3 else [],
            "recommendation": random.choice(["approve", "review", "decline"]),
            "confidence": random.uniform(0.7, 0.95)
        }
    
    async def _recognize_patterns(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize fraud patterns in data"""
        
        patterns_found = []
        
        # Mock pattern recognition
        for pattern_name, pattern_config in self.fraud_patterns.items():
            if random.random() < 0.2:  # 20% chance each pattern is found
                patterns_found.append({
                    "pattern_name": pattern_name,
                    "confidence": random.uniform(0.6, 0.95),
                    "indicators": pattern_config["indicators"],
                    "weight": pattern_config["weight"]
                })
        
        return {
            "patterns_detected": patterns_found,
            "pattern_count": len(patterns_found),
            "highest_confidence": max([p["confidence"] for p in patterns_found]) if patterns_found else 0.0
        }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= self.risk_thresholds["critical"]:
            return "critical"
        elif risk_score >= self.risk_thresholds["high"]:
            return "high"
        elif risk_score >= self.risk_thresholds["medium"]:
            return "medium"
        else:
            return "low"
    
    def _load_fraud_rules(self) -> Dict[str, Any]:
        """Load fraud detection rules (mock implementation)"""
        return {
            "sim_swap_rules": {
                "recent_swap_threshold_hours": 72,
                "risk_multiplier": 2.0
            },
            "transaction_rules": {
                "high_amount_threshold": 10000,
                "unusual_time_hours": [0, 1, 2, 3, 4, 5, 23]
            }
        }
    
    def _initialize_anomaly_detector(self) -> Dict[str, Any]:
        """Initialize anomaly detection models (mock)"""
        return {
            "model_type": "isolation_forest",
            "version": "1.2.0",
            "trained_on": "fraud_dataset_2024"
        }
    
    async def _get_agent_health(self) -> Dict[str, Any]:
        """Get fraud detection agent specific health info"""
        return {
            "camara_endpoints_status": "operational",
            "fraud_models_loaded": True,
            "rule_engine_status": "active",
            "last_model_update": datetime.utcnow().isoformat()
        }