from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random
import uuid
from enum import Enum


class ScamSignalRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to analyze for scam signals")
    analysis_period_hours: Optional[int] = Field(24, description="Period to analyze in hours")
    include_call_patterns: Optional[bool] = Field(True, description="Include call pattern analysis")
    include_message_patterns: Optional[bool] = Field(True, description="Include message pattern analysis")


class ScamIndicator(BaseModel):
    indicator_type: str
    severity: str  # "low", "medium", "high", "critical"
    confidence: float = Field(..., ge=0.0, le=1.0)
    description: str
    evidence: List[str]
    first_detected: datetime
    last_detected: datetime


class ScamSignalResponse(BaseModel):
    phone_number: str
    analysis_period: Dict[str, datetime]
    overall_scam_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    scam_indicators: List[ScamIndicator]
    call_pattern_analysis: Optional[Dict[str, Any]] = None
    message_pattern_analysis: Optional[Dict[str, Any]] = None
    behavioral_analysis: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)


router = APIRouter(prefix="/camara/scam-signal/v1", tags=["CAMARA Scam Signal API"])


class MockScamSignalAPI:
    """
    Mock implementation of CAMARA Scam Signal API
    Simulates scam and social engineering detection patterns
    """
    
    def __init__(self):
        self.phone_database = self._generate_mock_phone_data()
        self.scam_patterns = self._load_scam_patterns()
        self.social_engineering_indicators = self._load_social_engineering_indicators()
        self.known_scam_numbers = self._generate_known_scam_numbers()
    
    def _generate_mock_phone_data(self) -> Dict[str, Dict[str, Any]]:
        """Generate mock phone activity data"""
        mock_data = {}
        
        phone_numbers = [
            "+1234567890", "+1234567891", "+1234567892", "+1234567893",
            "+442071234567", "+33123456789", "+2348012345678",
            "+1555123456", "+1800555123", "+1900555789"  # Some suspicious numbers
        ]
        
        for phone in phone_numbers:
            # Generate call patterns
            num_calls = random.randint(5, 50)
            calls = []
            
            for i in range(num_calls):
                call_time = datetime.utcnow() - timedelta(
                    hours=random.randint(1, 168),  # Last week
                    minutes=random.randint(0, 59)
                )
                
                # Generate call characteristics
                duration = random.randint(10, 1800)  # 10 seconds to 30 minutes
                
                # Some numbers have suspicious patterns
                is_suspicious_number = phone in ["+1555123456", "+1800555123", "+1900555789"]
                
                if is_suspicious_number:
                    # Suspicious numbers have different patterns
                    duration = random.randint(30, 120)  # Shorter, high-pressure calls
                    caller_id_spoofed = random.random() < 0.7  # 70% spoofed
                    robocall = random.random() < 0.8  # 80% robocalls
                else:
                    caller_id_spoofed = random.random() < 0.1  # 10% spoofed
                    robocall = random.random() < 0.2  # 20% robocalls
                
                calls.append({
                    "timestamp": call_time,
                    "duration_seconds": duration,
                    "caller_id_spoofed": caller_id_spoofed,
                    "robocall_detected": robocall,
                    "call_frequency_score": random.uniform(0.1, 0.9),
                    "voice_stress_indicators": random.random() < 0.3 if not robocall else False,
                    "urgency_keywords_detected": random.random() < 0.4 if is_suspicious_number else random.random() < 0.1
                })
            
            # Generate message patterns
            num_messages = random.randint(0, 20)
            messages = []
            
            for i in range(num_messages):
                msg_time = datetime.utcnow() - timedelta(
                    hours=random.randint(1, 168),
                    minutes=random.randint(0, 59)
                )
                
                # Generate message characteristics
                if phone in ["+1555123456", "+1800555123"]:
                    # Suspicious messages
                    phishing_indicators = random.randint(2, 5)
                    urgency_score = random.uniform(0.6, 0.9)
                    contains_links = random.random() < 0.8
                else:
                    phishing_indicators = random.randint(0, 1)
                    urgency_score = random.uniform(0.1, 0.4)
                    contains_links = random.random() < 0.2
                
                messages.append({
                    "timestamp": msg_time,
                    "phishing_indicators_count": phishing_indicators,
                    "urgency_score": urgency_score,
                    "contains_suspicious_links": contains_links,
                    "impersonation_detected": random.random() < 0.3 if phishing_indicators > 2 else False,
                    "financial_keywords": random.random() < 0.5 if phishing_indicators > 1 else random.random() < 0.1
                })
            
            # Sort by timestamp
            calls.sort(key=lambda x: x["timestamp"])
            messages.sort(key=lambda x: x["timestamp"])
            
            mock_data[phone] = {
                "calls": calls,
                "messages": messages,
                "account_created": datetime.utcnow() - timedelta(days=random.randint(30, 1000)),
                "reputation_score": random.uniform(0.1, 0.9) if phone not in ["+1555123456", "+1800555123"] else random.uniform(0.1, 0.3),
                "reported_by_users": random.randint(0, 5) if phone not in ["+1555123456", "+1800555123"] else random.randint(10, 50)
            }
        
        return mock_data
    
    def _load_scam_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load known scam patterns for detection"""
        return {
            "tech_support_scam": {
                "keywords": ["microsoft", "windows", "computer", "virus", "infected", "technical support"],
                "call_duration_range": (60, 300),
                "urgency_indicators": ["immediate", "now", "today", "expired"],
                "severity": "high"
            },
            "irs_tax_scam": {
                "keywords": ["irs", "tax", "owe", "arrest", "warrant", "pay immediately"],
                "call_duration_range": (30, 180),
                "urgency_indicators": ["arrest", "warrant", "police", "today only"],
                "severity": "critical"
            },
            "bank_phishing": {
                "keywords": ["bank", "account", "suspended", "verify", "card", "fraud"],
                "call_duration_range": (60, 240),
                "urgency_indicators": ["suspended", "blocked", "verify now"],
                "severity": "high"
            },
            "lottery_scam": {
                "keywords": ["winner", "lottery", "prize", "congratulations", "claim"],
                "call_duration_range": (120, 600),
                "urgency_indicators": ["expires", "limited time", "act now"],
                "severity": "medium"
            },
            "romance_scam": {
                "keywords": ["love", "lonely", "money", "help", "emergency"],
                "call_duration_range": (300, 1800),
                "urgency_indicators": ["emergency", "hospital", "urgent help"],
                "severity": "high"
            }
        }
    
    def _load_social_engineering_indicators(self) -> List[Dict[str, Any]]:
        """Load social engineering detection patterns"""
        return [
            {
                "name": "urgency_manipulation",
                "description": "Creates false sense of urgency",
                "detection_criteria": ["time_pressure", "immediate_action", "deadline"],
                "risk_weight": 0.8
            },
            {
                "name": "authority_impersonation",
                "description": "Impersonates authority figures",
                "detection_criteria": ["government", "police", "bank", "tech_company"],
                "risk_weight": 0.9
            },
            {
                "name": "fear_intimidation",
                "description": "Uses fear and intimidation tactics",
                "detection_criteria": ["arrest", "legal_action", "consequences", "trouble"],
                "risk_weight": 0.7
            },
            {
                "name": "information_harvesting",
                "description": "Attempts to collect personal information",
                "detection_criteria": ["ssn", "password", "account_number", "verify"],
                "risk_weight": 0.85
            },
            {
                "name": "financial_pressure",
                "description": "Pressures for immediate financial action",
                "detection_criteria": ["pay_now", "wire_transfer", "gift_cards", "bitcoin"],
                "risk_weight": 0.95
            }
        ]
    
    def _generate_known_scam_numbers(self) -> List[Dict[str, Any]]:
        """Generate known scam phone numbers database"""
        return [
            {
                "phone": "+1555123456",
                "scam_type": "tech_support_scam",
                "confidence": 0.95,
                "reports": 147,
                "first_reported": datetime.utcnow() - timedelta(days=30)
            },
            {
                "phone": "+1800555123", 
                "scam_type": "irs_tax_scam",
                "confidence": 0.92,
                "reports": 89,
                "first_reported": datetime.utcnow() - timedelta(days=15)
            },
            {
                "phone": "+1900555789",
                "scam_type": "bank_phishing",
                "confidence": 0.88,
                "reports": 56,
                "first_reported": datetime.utcnow() - timedelta(days=7)
            }
        ]
    
    def analyze_scam_signals(self, request: ScamSignalRequest) -> ScamSignalResponse:
        """Analyze phone number for scam and social engineering signals"""
        
        # Simulate processing delay
        import time
        time.sleep(random.uniform(0.3, 0.8))
        
        phone_number = request.phone_number
        analysis_start = datetime.utcnow() - timedelta(hours=request.analysis_period_hours)
        analysis_end = datetime.utcnow()
        
        # Get phone activity data
        phone_data = self.phone_database.get(phone_number, {})
        
        # Initialize analysis results
        scam_indicators = []
        overall_scam_score = 0.1  # Base score
        
        # Analyze call patterns if requested
        call_analysis = None
        if request.include_call_patterns and phone_data.get("calls"):
            call_analysis = self._analyze_call_patterns(
                phone_data["calls"], analysis_start, analysis_end
            )
            scam_indicators.extend(call_analysis.get("indicators", []))
            overall_scam_score += call_analysis.get("score_contribution", 0.0)
        
        # Analyze message patterns if requested
        message_analysis = None
        if request.include_message_patterns and phone_data.get("messages"):
            message_analysis = self._analyze_message_patterns(
                phone_data["messages"], analysis_start, analysis_end
            )
            scam_indicators.extend(message_analysis.get("indicators", []))
            overall_scam_score += message_analysis.get("score_contribution", 0.0)
        
        # Check against known scam numbers
        known_scam = self._check_known_scam_number(phone_number)
        if known_scam:
            scam_indicators.append(
                ScamIndicator(
                    indicator_type="known_scam_number",
                    severity="critical",
                    confidence=known_scam["confidence"],
                    description=f"Number identified as {known_scam['scam_type']}",
                    evidence=[f"Reported {known_scam['reports']} times"],
                    first_detected=known_scam["first_reported"],
                    last_detected=datetime.utcnow()
                )
            )
            overall_scam_score += 0.8
        
        # Behavioral analysis
        behavioral_analysis = self._perform_behavioral_analysis(phone_data, scam_indicators)
        overall_scam_score += behavioral_analysis.get("score_contribution", 0.0)
        
        # Cap the overall score
        overall_scam_score = min(1.0, overall_scam_score)
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_scam_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(overall_scam_score, scam_indicators)
        
        # Generate metadata
        metadata = {
            "analysis_duration_ms": random.randint(300, 800),
            "data_sources": ["call_logs", "message_logs", "user_reports", "ml_models"],
            "model_version": "v2.1.0",
            "indicators_found": len(scam_indicators),
            "phone_reputation": phone_data.get("reputation_score", 0.5),
            "user_reports": phone_data.get("reported_by_users", 0)
        }
        
        return ScamSignalResponse(
            phone_number=phone_number,
            analysis_period={
                "start": analysis_start,
                "end": analysis_end
            },
            overall_scam_score=overall_scam_score,
            risk_level=risk_level,
            scam_indicators=scam_indicators,
            call_pattern_analysis=call_analysis,
            message_pattern_analysis=message_analysis,
            behavioral_analysis=behavioral_analysis,
            recommendations=recommendations,
            metadata=metadata
        )
    
    def _analyze_call_patterns(self, calls: List[Dict[str, Any]], 
                              start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze call patterns for scam indicators"""
        relevant_calls = [
            call for call in calls 
            if start_time <= call["timestamp"] <= end_time
        ]
        
        if not relevant_calls:
            return {"score_contribution": 0.0, "indicators": []}
        
        indicators = []
        score_contribution = 0.0
        
        # Analyze call frequency
        call_frequency = len(relevant_calls) / (24 * (end_time - start_time).days or 1)
        if call_frequency > 5:  # More than 5 calls per day
            indicators.append(
                ScamIndicator(
                    indicator_type="high_call_frequency",
                    severity="medium",
                    confidence=0.7,
                    description=f"High call frequency: {call_frequency:.1f} calls per day",
                    evidence=[f"{len(relevant_calls)} calls in analysis period"],
                    first_detected=relevant_calls[0]["timestamp"],
                    last_detected=relevant_calls[-1]["timestamp"]
                )
            )
            score_contribution += 0.2
        
        # Analyze call duration patterns
        short_calls = [c for c in relevant_calls if c["duration_seconds"] < 60]
        if len(short_calls) / len(relevant_calls) > 0.7:  # 70% very short calls
            indicators.append(
                ScamIndicator(
                    indicator_type="short_duration_pattern",
                    severity="medium",
                    confidence=0.65,
                    description="Pattern of very short calls (hang-ups)",
                    evidence=[f"{len(short_calls)} calls under 1 minute"],
                    first_detected=min(c["timestamp"] for c in short_calls),
                    last_detected=max(c["timestamp"] for c in short_calls)
                )
            )
            score_contribution += 0.15
        
        # Analyze caller ID spoofing
        spoofed_calls = [c for c in relevant_calls if c["caller_id_spoofed"]]
        if len(spoofed_calls) > 0:
            severity = "high" if len(spoofed_calls) / len(relevant_calls) > 0.5 else "medium"
            indicators.append(
                ScamIndicator(
                    indicator_type="caller_id_spoofing",
                    severity=severity,
                    confidence=0.8,
                    description="Caller ID spoofing detected",
                    evidence=[f"{len(spoofed_calls)} calls with spoofed caller ID"],
                    first_detected=min(c["timestamp"] for c in spoofed_calls),
                    last_detected=max(c["timestamp"] for c in spoofed_calls)
                )
            )
            score_contribution += 0.3
        
        # Analyze robocall patterns
        robocalls = [c for c in relevant_calls if c["robocall_detected"]]
        if len(robocalls) > len(relevant_calls) * 0.6:  # 60% robocalls
            indicators.append(
                ScamIndicator(
                    indicator_type="robocall_pattern",
                    severity="medium",
                    confidence=0.75,
                    description="High volume of robocalls detected",
                    evidence=[f"{len(robocalls)} robocalls out of {len(relevant_calls)}"],
                    first_detected=min(c["timestamp"] for c in robocalls),
                    last_detected=max(c["timestamp"] for c in robocalls)
                )
            )
            score_contribution += 0.25
        
        return {
            "score_contribution": min(0.4, score_contribution),  # Cap contribution
            "indicators": indicators,
            "total_calls": len(relevant_calls),
            "call_frequency_per_day": call_frequency,
            "avg_duration_seconds": sum(c["duration_seconds"] for c in relevant_calls) / len(relevant_calls),
            "spoofed_percentage": len(spoofed_calls) / len(relevant_calls) * 100,
            "robocall_percentage": len(robocalls) / len(relevant_calls) * 100
        }
    
    def _analyze_message_patterns(self, messages: List[Dict[str, Any]],
                                 start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze message patterns for scam indicators"""
        relevant_messages = [
            msg for msg in messages 
            if start_time <= msg["timestamp"] <= end_time
        ]
        
        if not relevant_messages:
            return {"score_contribution": 0.0, "indicators": []}
        
        indicators = []
        score_contribution = 0.0
        
        # Analyze phishing indicators
        high_phishing_msgs = [m for m in relevant_messages if m["phishing_indicators_count"] >= 3]
        if high_phishing_msgs:
            indicators.append(
                ScamIndicator(
                    indicator_type="phishing_content",
                    severity="high",
                    confidence=0.85,
                    description="Messages contain multiple phishing indicators",
                    evidence=[f"{len(high_phishing_msgs)} messages with phishing content"],
                    first_detected=min(m["timestamp"] for m in high_phishing_msgs),
                    last_detected=max(m["timestamp"] for m in high_phishing_msgs)
                )
            )
            score_contribution += 0.35
        
        # Analyze urgency patterns
        urgent_messages = [m for m in relevant_messages if m["urgency_score"] > 0.7]
        if len(urgent_messages) > len(relevant_messages) * 0.5:  # 50% urgent messages
            indicators.append(
                ScamIndicator(
                    indicator_type="urgency_manipulation",
                    severity="medium",
                    confidence=0.7,
                    description="High frequency of urgent/pressure messages",
                    evidence=[f"{len(urgent_messages)} urgent messages"],
                    first_detected=min(m["timestamp"] for m in urgent_messages),
                    last_detected=max(m["timestamp"] for m in urgent_messages)
                )
            )
            score_contribution += 0.2
        
        # Analyze suspicious links
        suspicious_link_msgs = [m for m in relevant_messages if m["contains_suspicious_links"]]
        if suspicious_link_msgs:
            indicators.append(
                ScamIndicator(
                    indicator_type="suspicious_links",
                    severity="high",
                    confidence=0.8,
                    description="Messages contain suspicious links",
                    evidence=[f"{len(suspicious_link_msgs)} messages with suspicious links"],
                    first_detected=min(m["timestamp"] for m in suspicious_link_msgs),
                    last_detected=max(m["timestamp"] for m in suspicious_link_msgs)
                )
            )
            score_contribution += 0.3
        
        # Analyze impersonation attempts
        impersonation_msgs = [m for m in relevant_messages if m["impersonation_detected"]]
        if impersonation_msgs:
            indicators.append(
                ScamIndicator(
                    indicator_type="authority_impersonation",
                    severity="high",
                    confidence=0.82,
                    description="Impersonation of authority figures detected",
                    evidence=[f"{len(impersonation_msgs)} messages with impersonation"],
                    first_detected=min(m["timestamp"] for m in impersonation_msgs),
                    last_detected=max(m["timestamp"] for m in impersonation_msgs)
                )
            )
            score_contribution += 0.32
        
        return {
            "score_contribution": min(0.4, score_contribution),  # Cap contribution
            "indicators": indicators,
            "total_messages": len(relevant_messages),
            "high_phishing_count": len(high_phishing_msgs),
            "urgent_message_percentage": len(urgent_messages) / len(relevant_messages) * 100,
            "suspicious_link_percentage": len(suspicious_link_msgs) / len(relevant_messages) * 100,
            "impersonation_count": len(impersonation_msgs)
        }
    
    def _check_known_scam_number(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Check if phone number is in known scam database"""
        for scam_entry in self.known_scam_numbers:
            if scam_entry["phone"] == phone_number:
                return scam_entry
        return None
    
    def _perform_behavioral_analysis(self, phone_data: Dict[str, Any], 
                                   indicators: List[ScamIndicator]) -> Dict[str, Any]:
        """Perform behavioral analysis of the phone number"""
        analysis = {
            "score_contribution": 0.0,
            "reputation_score": phone_data.get("reputation_score", 0.5),
            "account_age_days": (datetime.utcnow() - phone_data.get("account_created", datetime.utcnow())).days,
            "user_reports": phone_data.get("reported_by_users", 0)
        }
        
        # Factor in reputation
        if analysis["reputation_score"] < 0.3:
            analysis["score_contribution"] += 0.2
        
        # Factor in user reports
        if analysis["user_reports"] > 10:
            analysis["score_contribution"] += 0.25
        elif analysis["user_reports"] > 5:
            analysis["score_contribution"] += 0.15
        
        # Factor in account age (very new accounts are suspicious)
        if analysis["account_age_days"] < 7:
            analysis["score_contribution"] += 0.15
        
        analysis["behavioral_flags"] = []
        if analysis["reputation_score"] < 0.3:
            analysis["behavioral_flags"].append("low_reputation")
        if analysis["user_reports"] > 5:
            analysis["behavioral_flags"].append("user_reported")
        if analysis["account_age_days"] < 7:
            analysis["behavioral_flags"].append("new_account")
        
        return analysis
    
    def _determine_risk_level(self, scam_score: float) -> str:
        """Determine risk level based on scam score"""
        if scam_score > 0.8:
            return "critical"
        elif scam_score > 0.6:
            return "high" 
        elif scam_score > 0.4:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(self, scam_score: float, 
                                indicators: List[ScamIndicator]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if scam_score > 0.8:
            recommendations.extend([
                "BLOCK_NUMBER_IMMEDIATELY",
                "REPORT_TO_AUTHORITIES",
                "WARN_OTHER_USERS"
            ])
        elif scam_score > 0.6:
            recommendations.extend([
                "BLOCK_NUMBER",
                "FLAG_FOR_REVIEW",
                "INCREASE_MONITORING"
            ])
        elif scam_score > 0.4:
            recommendations.extend([
                "MONITOR_CLOSELY",
                "WARN_USERS",
                "REQUEST_VERIFICATION"
            ])
        else:
            recommendations.append("CONTINUE_MONITORING")
        
        # Add specific recommendations based on indicators
        indicator_types = {ind.indicator_type for ind in indicators}
        
        if "caller_id_spoofing" in indicator_types:
            recommendations.append("VERIFY_CALLER_IDENTITY")
        if "phishing_content" in indicator_types:
            recommendations.append("BLOCK_SUSPICIOUS_LINKS")
        if "authority_impersonation" in indicator_types:
            recommendations.append("VERIFY_WITH_CLAIMED_ORGANIZATION")
        
        return recommendations


# Create API instance
mock_api = MockScamSignalAPI()


@router.post("/analyze", response_model=ScamSignalResponse)
async def analyze_scam_signals(request: ScamSignalRequest):
    """
    Analyze phone number for scam and social engineering signals
    
    This endpoint simulates the CAMARA Scam Signal API functionality
    """
    try:
        response = mock_api.analyze_scam_signals(request)
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scam signal analysis failed: {str(e)}")


@router.get("/phone-data/{phone_number}")
async def get_phone_data(phone_number: str):
    """Get phone activity data (debug endpoint)"""
    data = mock_api.phone_database.get(phone_number, {})
    if not data:
        raise HTTPException(status_code=404, detail="Phone number not found")
    return data


@router.get("/known-scams")
async def get_known_scam_numbers():
    """Get list of known scam numbers (debug endpoint)"""
    return mock_api.known_scam_numbers


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CAMARA Scam Signal API Mock",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "phones_in_database": len(mock_api.phone_database),
        "known_scam_numbers": len(mock_api.known_scam_numbers),
        "scam_patterns": len(mock_api.scam_patterns),
        "social_engineering_indicators": len(mock_api.social_engineering_indicators)
    }