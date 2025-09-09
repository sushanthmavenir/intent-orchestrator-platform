from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random
import uuid
from enum import Enum


class KYCMatchRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number for KYC verification")
    given_name: Optional[str] = Field(None, description="Given name to verify")
    family_name: Optional[str] = Field(None, description="Family name to verify") 
    birth_date: Optional[str] = Field(None, description="Birth date (YYYY-MM-DD)")
    address: Optional[Dict[str, str]] = Field(None, description="Address information")
    id_document: Optional[Dict[str, str]] = Field(None, description="ID document details")


class MatchScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Match confidence score")
    result: str = Field(..., description="Match result: MATCH, NO_MATCH, PARTIAL_MATCH")


class KYCMatchResponse(BaseModel):
    phone_number: str
    overall_match: MatchScore
    name_match: Optional[MatchScore] = None
    birth_date_match: Optional[MatchScore] = None
    address_match: Optional[MatchScore] = None
    id_document_match: Optional[MatchScore] = None
    verification_timestamp: datetime
    verification_status: str
    risk_assessment: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


router = APIRouter(prefix="/camara/kyc-match/v1", tags=["CAMARA KYC Match API"])


class MockKYCMatchAPI:
    """
    Mock implementation of CAMARA KYC Match API
    Simulates identity verification and document matching
    """
    
    def __init__(self):
        self.customer_database = self._generate_mock_customer_data()
        self.document_patterns = self._generate_document_patterns()
        self.risk_profiles = self._generate_risk_profiles()
    
    def _generate_mock_customer_data(self) -> Dict[str, Dict[str, Any]]:
        """Generate mock customer KYC data"""
        mock_data = {}
        
        # Sample customers with various verification scenarios
        customers = [
            {
                "phone": "+1234567890",
                "given_name": "John",
                "family_name": "Smith",
                "birth_date": "1990-05-15",
                "address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "US"
                },
                "id_document": {
                    "type": "passport",
                    "number": "123456789",
                    "country": "US",
                    "expiry": "2025-12-31"
                },
                "verification_score": 0.95,
                "risk_level": "low"
            },
            {
                "phone": "+1234567891",
                "given_name": "Sarah",
                "family_name": "Johnson",
                "birth_date": "1985-08-22",
                "address": {
                    "street": "456 Oak Ave",
                    "city": "Los Angeles",
                    "state": "CA",
                    "postal_code": "90210",
                    "country": "US"
                },
                "id_document": {
                    "type": "drivers_license",
                    "number": "D1234567",
                    "state": "CA",
                    "expiry": "2024-08-22"
                },
                "verification_score": 0.88,
                "risk_level": "low"
            },
            {
                "phone": "+442071234567",
                "given_name": "James",
                "family_name": "Wilson",
                "birth_date": "1978-12-03",
                "address": {
                    "street": "10 Downing Street",
                    "city": "London",
                    "postal_code": "SW1A 2AA",
                    "country": "UK"
                },
                "id_document": {
                    "type": "passport",
                    "number": "987654321",
                    "country": "UK",
                    "expiry": "2026-01-15"
                },
                "verification_score": 0.92,
                "risk_level": "low"
            },
            {
                "phone": "+2348012345678",
                "given_name": "Adaora",
                "family_name": "Okafor",
                "birth_date": "1992-03-18",
                "address": {
                    "street": "15 Victoria Island",
                    "city": "Lagos",
                    "state": "Lagos",
                    "country": "Nigeria"
                },
                "id_document": {
                    "type": "national_id",
                    "number": "12345678901",
                    "country": "NG",
                    "expiry": "2030-03-18"
                },
                "verification_score": 0.87,
                "risk_level": "medium"
            }
        ]
        
        for customer in customers:
            mock_data[customer["phone"]] = customer
        
        return mock_data
    
    def _generate_document_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Generate document validation patterns"""
        return {
            "passport": {
                "format_regex": r"^[A-Z0-9]{9}$",
                "countries": ["US", "UK", "CA", "AU", "DE", "FR", "NG"],
                "typical_validity_years": 10,
                "security_features": ["biometric_chip", "hologram", "watermark"]
            },
            "drivers_license": {
                "format_regex": r"^[A-Z]{1}[0-9]{7}$",
                "countries": ["US"],
                "typical_validity_years": 5,
                "security_features": ["magnetic_strip", "barcode", "hologram"]
            },
            "national_id": {
                "format_regex": r"^[0-9]{11}$",
                "countries": ["NG", "KE", "GH"],
                "typical_validity_years": 10,
                "security_features": ["chip", "biometric_data"]
            }
        }
    
    def _generate_risk_profiles(self) -> Dict[str, List[str]]:
        """Generate risk assessment criteria"""
        return {
            "high_risk_indicators": [
                "document_expired",
                "address_mismatch",
                "name_variation",
                "multiple_recent_attempts",
                "suspicious_location",
                "document_image_quality_poor"
            ],
            "medium_risk_indicators": [
                "partial_address_match",
                "document_near_expiry",
                "minor_name_differences",
                "incomplete_information"
            ],
            "low_risk_indicators": [
                "exact_match",
                "document_valid",
                "consistent_information",
                "verified_address"
            ]
        }
    
    def verify_kyc(self, request: KYCMatchRequest) -> KYCMatchResponse:
        """Perform KYC verification and matching"""
        
        # Simulate processing delay
        import time
        time.sleep(random.uniform(0.5, 1.5))
        
        # Get customer data if exists
        customer_data = self.customer_database.get(request.phone_number)
        
        # Initialize match scores
        name_match = None
        birth_date_match = None
        address_match = None
        id_document_match = None
        
        # Perform name matching
        if request.given_name or request.family_name:
            name_match = self._match_name(
                request.given_name, request.family_name, customer_data
            )
        
        # Perform birth date matching
        if request.birth_date:
            birth_date_match = self._match_birth_date(request.birth_date, customer_data)
        
        # Perform address matching
        if request.address:
            address_match = self._match_address(request.address, customer_data)
        
        # Perform ID document matching
        if request.id_document:
            id_document_match = self._match_id_document(request.id_document, customer_data)
        
        # Calculate overall match score
        overall_match = self._calculate_overall_match([
            name_match, birth_date_match, address_match, id_document_match
        ])
        
        # Perform risk assessment
        risk_assessment = self._assess_risk(
            request, customer_data, overall_match, 
            [name_match, birth_date_match, address_match, id_document_match]
        )
        
        # Determine verification status
        verification_status = self._determine_verification_status(
            overall_match, risk_assessment
        )
        
        # Generate metadata
        metadata = {
            "processing_time_ms": random.randint(500, 1500),
            "checks_performed": len([m for m in [name_match, birth_date_match, address_match, id_document_match] if m]),
            "data_sources": ["government_db", "credit_bureau", "telecom_records"],
            "verification_method": "automated",
            "confidence_factors": self._generate_confidence_factors(customer_data, overall_match)
        }
        
        return KYCMatchResponse(
            phone_number=request.phone_number,
            overall_match=overall_match,
            name_match=name_match,
            birth_date_match=birth_date_match,
            address_match=address_match,
            id_document_match=id_document_match,
            verification_timestamp=datetime.utcnow(),
            verification_status=verification_status,
            risk_assessment=risk_assessment,
            metadata=metadata
        )
    
    def _match_name(self, given_name: Optional[str], family_name: Optional[str], 
                   customer_data: Optional[Dict[str, Any]]) -> MatchScore:
        """Match name information"""
        if not customer_data:
            return MatchScore(score=0.0, result="NO_MATCH")
        
        score = 0.0
        matches = []
        
        if given_name:
            customer_given = customer_data.get("given_name", "").lower()
            if given_name.lower() == customer_given:
                score += 0.5
                matches.append("given_name_exact")
            elif self._calculate_string_similarity(given_name.lower(), customer_given) > 0.8:
                score += 0.4
                matches.append("given_name_similar")
        
        if family_name:
            customer_family = customer_data.get("family_name", "").lower()
            if family_name.lower() == customer_family:
                score += 0.5
                matches.append("family_name_exact")
            elif self._calculate_string_similarity(family_name.lower(), customer_family) > 0.8:
                score += 0.4
                matches.append("family_name_similar")
        
        result = "MATCH" if score > 0.8 else "PARTIAL_MATCH" if score > 0.5 else "NO_MATCH"
        return MatchScore(score=score, result=result)
    
    def _match_birth_date(self, birth_date: str, 
                         customer_data: Optional[Dict[str, Any]]) -> MatchScore:
        """Match birth date information"""
        if not customer_data:
            return MatchScore(score=0.0, result="NO_MATCH")
        
        customer_birth_date = customer_data.get("birth_date")
        if not customer_birth_date:
            return MatchScore(score=0.0, result="NO_MATCH")
        
        if birth_date == customer_birth_date:
            return MatchScore(score=1.0, result="MATCH")
        else:
            # Check if only day/month are swapped (common error)
            try:
                parts1 = birth_date.split("-")
                parts2 = customer_birth_date.split("-")
                if len(parts1) == 3 and len(parts2) == 3:
                    if parts1[0] == parts2[0] and (
                        (parts1[1] == parts2[2] and parts1[2] == parts2[1])
                    ):
                        return MatchScore(score=0.7, result="PARTIAL_MATCH")
            except:
                pass
            
            return MatchScore(score=0.0, result="NO_MATCH")
    
    def _match_address(self, address: Dict[str, str], 
                      customer_data: Optional[Dict[str, Any]]) -> MatchScore:
        """Match address information"""
        if not customer_data or "address" not in customer_data:
            return MatchScore(score=0.0, result="NO_MATCH")
        
        customer_address = customer_data["address"]
        score = 0.0
        total_fields = 0
        
        address_fields = ["street", "city", "state", "postal_code", "country"]
        
        for field in address_fields:
            if field in address and field in customer_address:
                total_fields += 1
                provided = address[field].lower().strip()
                stored = customer_address[field].lower().strip()
                
                if provided == stored:
                    score += 1.0
                elif self._calculate_string_similarity(provided, stored) > 0.8:
                    score += 0.7
                elif field == "country" and provided != stored:
                    # Country mismatch is significant
                    score -= 0.5
        
        if total_fields == 0:
            return MatchScore(score=0.0, result="NO_MATCH")
        
        final_score = max(0.0, score / total_fields)
        result = "MATCH" if final_score > 0.8 else "PARTIAL_MATCH" if final_score > 0.5 else "NO_MATCH"
        
        return MatchScore(score=final_score, result=result)
    
    def _match_id_document(self, id_document: Dict[str, str],
                          customer_data: Optional[Dict[str, Any]]) -> MatchScore:
        """Match ID document information"""
        if not customer_data or "id_document" not in customer_data:
            return MatchScore(score=0.0, result="NO_MATCH")
        
        customer_doc = customer_data["id_document"]
        score = 0.0
        
        # Check document type
        if id_document.get("type") == customer_doc.get("type"):
            score += 0.3
        
        # Check document number
        if id_document.get("number") == customer_doc.get("number"):
            score += 0.5
        
        # Check country/issuing authority
        doc_country = id_document.get("country") or id_document.get("state")
        customer_country = customer_doc.get("country") or customer_doc.get("state")
        if doc_country == customer_country:
            score += 0.2
        
        # Check expiry date
        if "expiry" in id_document and "expiry" in customer_doc:
            if id_document["expiry"] == customer_doc["expiry"]:
                score += 0.1
            else:
                # Check if document is expired
                try:
                    expiry_date = datetime.strptime(id_document["expiry"], "%Y-%m-%d")
                    if expiry_date < datetime.utcnow():
                        score -= 0.2  # Penalty for expired document
                except:
                    pass
        
        score = max(0.0, min(1.0, score))
        result = "MATCH" if score > 0.8 else "PARTIAL_MATCH" if score > 0.5 else "NO_MATCH"
        
        return MatchScore(score=score, result=result)
    
    def _calculate_overall_match(self, match_scores: List[Optional[MatchScore]]) -> MatchScore:
        """Calculate overall match score from individual matches"""
        valid_scores = [score for score in match_scores if score is not None]
        
        if not valid_scores:
            return MatchScore(score=0.0, result="NO_MATCH")
        
        # Weight the scores (name and ID document are more important)
        weights = []
        scores = []
        
        for i, score in enumerate(match_scores):
            if score is not None:
                if i == 0:  # name match
                    weights.append(0.35)
                elif i == 3:  # id document match
                    weights.append(0.35)
                elif i == 1:  # birth date match
                    weights.append(0.20)
                else:  # address match
                    weights.append(0.10)
                scores.append(score.score)
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Calculate weighted average
        overall_score = sum(s * w for s, w in zip(scores, weights))
        
        # Determine result
        if overall_score > 0.85:
            result = "MATCH"
        elif overall_score > 0.6:
            result = "PARTIAL_MATCH"
        else:
            result = "NO_MATCH"
        
        return MatchScore(score=overall_score, result=result)
    
    def _assess_risk(self, request: KYCMatchRequest, customer_data: Optional[Dict[str, Any]],
                    overall_match: MatchScore, individual_matches: List[Optional[MatchScore]]) -> Dict[str, Any]:
        """Assess fraud risk based on verification results"""
        risk_score = 0.1  # Base risk
        risk_factors = []
        
        # Overall match quality
        if overall_match.score < 0.5:
            risk_score += 0.3
            risk_factors.append("low_match_score")
        
        # Check for inconsistencies
        if overall_match.result == "PARTIAL_MATCH":
            risk_score += 0.2
            risk_factors.append("partial_information_match")
        
        # Document expiry check
        if request.id_document and "expiry" in request.id_document:
            try:
                expiry_date = datetime.strptime(request.id_document["expiry"], "%Y-%m-%d")
                days_to_expiry = (expiry_date - datetime.utcnow()).days
                if days_to_expiry < 0:
                    risk_score += 0.4
                    risk_factors.append("expired_document")
                elif days_to_expiry < 30:
                    risk_score += 0.1
                    risk_factors.append("document_near_expiry")
            except:
                risk_score += 0.1
                risk_factors.append("invalid_expiry_date")
        
        # Address country mismatch
        if (request.address and customer_data and "address" in customer_data and
            request.address.get("country") != customer_data["address"].get("country")):
            risk_score += 0.25
            risk_factors.append("address_country_mismatch")
        
        # Random additional risk factors for realism
        if random.random() < 0.1:  # 10% chance
            additional_risks = ["multiple_verification_attempts", "suspicious_timing", "device_fingerprint_change"]
            risk_factors.append(random.choice(additional_risks))
            risk_score += 0.15
        
        risk_score = min(1.0, risk_score)
        
        # Determine risk level
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level, risk_score)
        }
    
    def _determine_verification_status(self, overall_match: MatchScore, 
                                     risk_assessment: Dict[str, Any]) -> str:
        """Determine final verification status"""
        if overall_match.result == "MATCH" and risk_assessment["risk_level"] == "low":
            return "VERIFIED"
        elif overall_match.result == "PARTIAL_MATCH" and risk_assessment["risk_level"] in ["low", "medium"]:
            return "PARTIAL_VERIFICATION"
        elif risk_assessment["risk_level"] == "high":
            return "REJECTED"
        else:
            return "REQUIRES_MANUAL_REVIEW"
    
    def _get_risk_recommendation(self, risk_level: str, risk_score: float) -> str:
        """Get recommendation based on risk assessment"""
        if risk_level == "high":
            return "REJECT_APPLICATION"
        elif risk_level == "medium":
            return "MANUAL_REVIEW_REQUIRED"
        else:
            return "APPROVE_APPLICATION"
    
    def _generate_confidence_factors(self, customer_data: Optional[Dict[str, Any]], 
                                   overall_match: MatchScore) -> List[str]:
        """Generate factors that influenced confidence score"""
        factors = []
        
        if overall_match.score > 0.9:
            factors.append("high_data_quality")
        if overall_match.score > 0.8:
            factors.append("multiple_data_points_verified")
        if customer_data:
            factors.append("existing_customer_record")
        if random.random() < 0.5:
            factors.append("government_database_confirmation")
        
        return factors
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (simple implementation)"""
        if not str1 or not str2:
            return 0.0
        
        # Simple character-based similarity
        len1, len2 = len(str1), len(str2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Count common characters
        common = 0
        for char in str1:
            if char in str2:
                common += 1
        
        return common / max(len1, len2)


# Create API instance
mock_api = MockKYCMatchAPI()


@router.post("/verify", response_model=KYCMatchResponse)
async def verify_kyc(request: KYCMatchRequest):
    """
    Verify KYC information against stored records
    
    This endpoint simulates the CAMARA KYC Match API functionality
    """
    try:
        response = mock_api.verify_kyc(request)
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KYC verification failed: {str(e)}")


@router.get("/customer/{phone_number}")
async def get_customer_data(phone_number: str):
    """Get stored customer data (debug endpoint)"""
    customer = mock_api.customer_database.get(phone_number)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CAMARA KYC Match API Mock",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "customers_in_database": len(mock_api.customer_database),
        "supported_document_types": list(mock_api.document_patterns.keys()),
        "risk_assessment_enabled": True
    }