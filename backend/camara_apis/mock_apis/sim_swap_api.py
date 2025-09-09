from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random
import uuid
from enum import Enum


class SIMSwapRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to check for SIM swap")
    max_age: Optional[int] = Field(240, description="Maximum age in hours to check for swaps")


class SIMSwapResponse(BaseModel):
    phone_number: str
    swapped: bool
    swap_date: Optional[datetime] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    previous_imsi: Optional[str] = None
    current_imsi: str
    operator_change: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SIMInfo(BaseModel):
    imsi: str
    iccid: Optional[str] = None
    operator: str
    country_code: str
    activated_date: datetime
    deactivated_date: Optional[datetime] = None
    swap_reason: Optional[str] = None


router = APIRouter(prefix="/camara/sim-swap/v1", tags=["CAMARA SIM Swap API"])


class MockSIMSwapAPI:
    """
    Mock implementation of CAMARA SIM Swap API
    Simulates SIM swap detection with realistic fraud patterns
    """
    
    def __init__(self):
        self.operators = {
            'US': ['Verizon', 'AT&T', 'T-Mobile', 'Sprint'],
            'UK': ['EE', 'Vodafone', 'O2', 'Three'],
            'DE': ['T-Mobile', 'Vodafone', 'O2', 'E-Plus'],
            'FR': ['Orange', 'SFR', 'Bouygues', 'Free'],
            'NG': ['MTN', 'Airtel', 'Glo', '9mobile']
        }
        self.sim_database = self._generate_mock_sim_data()
        self.swap_patterns = self._generate_swap_patterns()
    
    def _generate_mock_sim_data(self) -> Dict[str, List[SIMInfo]]:
        """Generate mock SIM card data"""
        mock_data = {}
        
        phone_numbers = [
            "+1234567890", "+1234567891", "+1234567892", "+1234567893",
            "+442071234567", "+33123456789", "+49301234567", 
            "+2348012345678", "+8613912345678"
        ]
        
        for phone in phone_numbers:
            sims = []
            num_sims = random.randint(1, 5)  # 1-5 SIM cards per number
            
            # Determine country based on phone number
            if phone.startswith('+1'):
                country = 'US'
            elif phone.startswith('+44'):
                country = 'UK'
            elif phone.startswith('+49'):
                country = 'DE'
            elif phone.startswith('+33'):
                country = 'FR'
            elif phone.startswith('+234'):
                country = 'NG'
            else:
                country = 'US'  # Default
            
            operators = self.operators.get(country, ['Generic'])
            
            for i in range(num_sims):
                # Generate IMSI (15 digits)
                mcc = {'US': '310', 'UK': '234', 'DE': '262', 'FR': '208', 'NG': '621'}.get(country, '310')
                mnc = f"{random.randint(10, 99):02d}"
                msin = f"{random.randint(1000000000, 9999999999)}"
                imsi = f"{mcc}{mnc}{msin}"
                
                # Generate ICCID (19-20 digits)
                iccid = f"89{country[:2].upper()}{random.randint(10000000000000000, 99999999999999999)}"
                
                # Create timeline
                days_ago = random.randint(1, 730)  # Up to 2 years ago
                activated = datetime.utcnow() - timedelta(days=days_ago)
                
                # Most recent SIM is still active
                if i == num_sims - 1:
                    deactivated = None
                else:
                    deactivated = activated + timedelta(days=random.randint(30, 365))
                
                # Determine swap reason for deactivated SIMs
                swap_reason = None
                if deactivated:
                    reasons = ['user_request', 'lost_stolen', 'damaged', 'upgrade', 'fraud_prevention']
                    swap_reason = random.choice(reasons)
                
                sims.append(SIMInfo(
                    imsi=imsi,
                    iccid=iccid,
                    operator=random.choice(operators),
                    country_code=country,
                    activated_date=activated,
                    deactivated_date=deactivated,
                    swap_reason=swap_reason
                ))
            
            # Sort by activation date
            sims.sort(key=lambda s: s.activated_date)
            mock_data[phone] = sims
        
        return mock_data
    
    def _generate_swap_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Generate realistic swap patterns for fraud detection"""
        patterns = {}
        
        for phone_number, sims in self.sim_database.items():
            pattern_data = {
                'swap_frequency': len(sims) - 1,  # Number of swaps
                'avg_sim_lifetime_days': 0,
                'suspicious_swaps': 0,
                'international_swaps': 0,
                'operator_changes': 0,
                'fraud_indicators': []
            }
            
            if len(sims) > 1:
                lifetimes = []
                prev_sim = None
                
                for sim in sims:
                    if prev_sim:
                        # Check for suspicious patterns
                        time_gap = (sim.activated_date - prev_sim.deactivated_date).total_seconds() if prev_sim.deactivated_date else 0
                        
                        # Very quick swap (less than 1 hour)
                        if time_gap < 3600:
                            pattern_data['suspicious_swaps'] += 1
                            pattern_data['fraud_indicators'].append('rapid_swap')
                        
                        # Operator change
                        if sim.operator != prev_sim.operator:
                            pattern_data['operator_changes'] += 1
                        
                        # Country change (international)
                        if sim.country_code != prev_sim.country_code:
                            pattern_data['international_swaps'] += 1
                            pattern_data['fraud_indicators'].append('international_swap')
                        
                        # Lost/stolen reason
                        if prev_sim.swap_reason == 'lost_stolen':
                            pattern_data['fraud_indicators'].append('reported_lost_stolen')
                    
                    # Calculate lifetime
                    if sim.deactivated_date:
                        lifetime = (sim.deactivated_date - sim.activated_date).days
                        lifetimes.append(lifetime)
                    
                    prev_sim = sim
                
                if lifetimes:
                    pattern_data['avg_sim_lifetime_days'] = sum(lifetimes) / len(lifetimes)
            
            patterns[phone_number] = pattern_data
        
        return patterns
    
    def check_sim_swap(self, phone_number: str, max_age_hours: int = 240) -> SIMSwapResponse:
        """Check if a SIM swap occurred for the given phone number"""
        
        # Simulate API delay
        import time
        time.sleep(random.uniform(0.1, 0.4))
        
        # Get SIM history
        sims = self.sim_database.get(phone_number, [])
        
        if not sims:
            # Generate basic response for unknown numbers
            return SIMSwapResponse(
                phone_number=phone_number,
                swapped=False,
                confidence=0.5,
                risk_score=0.2,
                risk_level="unknown",
                current_imsi=f"310999{random.randint(1000000000, 9999999999)}",
                metadata={'reason': 'no_sim_history'}
            )
        
        current_sim = sims[-1]
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Check if current SIM was activated recently
        recent_swap = current_sim.activated_date > cutoff_time
        
        if recent_swap and len(sims) > 1:
            previous_sim = sims[-2]
            pattern_data = self.swap_patterns.get(phone_number, {})
            
            # Calculate confidence and risk
            confidence = self._calculate_swap_confidence(current_sim, previous_sim, pattern_data)
            risk_score = self._calculate_risk_score(current_sim, previous_sim, pattern_data)
            risk_level = self._determine_risk_level(risk_score, confidence)
            
            # Check operator change
            operator_change = current_sim.operator != previous_sim.operator
            
            return SIMSwapResponse(
                phone_number=phone_number,
                swapped=True,
                swap_date=current_sim.activated_date,
                confidence=confidence,
                risk_score=risk_score,
                risk_level=risk_level,
                previous_imsi=previous_sim.imsi,
                current_imsi=current_sim.imsi,
                operator_change=operator_change,
                metadata={
                    'hours_since_swap': (datetime.utcnow() - current_sim.activated_date).total_seconds() / 3600,
                    'previous_operator': previous_sim.operator,
                    'current_operator': current_sim.operator,
                    'previous_country': previous_sim.country_code,
                    'current_country': current_sim.country_code,
                    'swap_reason': previous_sim.swap_reason,
                    'total_swaps_ever': len(sims) - 1,
                    'suspicious_swaps': pattern_data.get('suspicious_swaps', 0),
                    'fraud_indicators': pattern_data.get('fraud_indicators', [])
                }
            )
        else:
            # No recent swap
            return SIMSwapResponse(
                phone_number=phone_number,
                swapped=False,
                confidence=0.95,
                risk_score=0.1,
                risk_level="low",
                current_imsi=current_sim.imsi,
                metadata={
                    'sim_age_days': (datetime.utcnow() - current_sim.activated_date).days,
                    'operator': current_sim.operator,
                    'country': current_sim.country_code,
                    'total_sims_ever': len(sims),
                    'last_swap_days_ago': (datetime.utcnow() - sims[-2].activated_date).days if len(sims) > 1 else None
                }
            )
    
    def _calculate_swap_confidence(self, current_sim: SIMInfo, previous_sim: SIMInfo, 
                                 pattern_data: Dict[str, Any]) -> float:
        """Calculate confidence for SIM swap detection"""
        base_confidence = 0.9  # High base confidence for detected swaps
        
        # Time factor - very recent swaps have higher confidence
        hours_since = (datetime.utcnow() - current_sim.activated_date).total_seconds() / 3600
        if hours_since < 1:
            base_confidence += 0.05
        elif hours_since > 168:  # More than a week
            base_confidence -= 0.1
        
        # Deactivation gap - immediate reactivation is more suspicious
        if previous_sim.deactivated_date:
            gap = (current_sim.activated_date - previous_sim.deactivated_date).total_seconds()
            if gap < 300:  # Less than 5 minutes
                base_confidence += 0.05
        
        # Pattern factors
        if pattern_data.get('suspicious_swaps', 0) > 2:
            base_confidence -= 0.05
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def _calculate_risk_score(self, current_sim: SIMInfo, previous_sim: SIMInfo,
                            pattern_data: Dict[str, Any]) -> float:
        """Calculate fraud risk score"""
        risk_score = 0.3  # Base risk for any swap
        
        # Rapid succession swaps
        if pattern_data.get('suspicious_swaps', 0) > 0:
            risk_score += 0.3
        
        # International swaps
        if current_sim.country_code != previous_sim.country_code:
            risk_score += 0.25
        
        # Lost/stolen reason
        if previous_sim.swap_reason == 'lost_stolen':
            risk_score += 0.2
        
        # Multiple recent swaps
        total_swaps = pattern_data.get('swap_frequency', 0)
        if total_swaps > 3:
            risk_score += 0.15
        
        # Very short SIM lifetime
        if pattern_data.get('avg_sim_lifetime_days', 365) < 30:
            risk_score += 0.1
        
        # Fraud indicators
        fraud_indicators = pattern_data.get('fraud_indicators', [])
        if 'rapid_swap' in fraud_indicators:
            risk_score += 0.2
        if 'international_swap' in fraud_indicators:
            risk_score += 0.15
        
        return min(risk_score, 1.0)
    
    def _determine_risk_level(self, risk_score: float, confidence: float) -> str:
        """Determine overall risk level"""
        if confidence > 0.8 and risk_score > 0.7:
            return "high"
        elif confidence > 0.6 and risk_score > 0.5:
            return "medium"
        elif risk_score > 0.3:
            return "low"
        else:
            return "very_low"


# Create API instance
mock_api = MockSIMSwapAPI()


@router.post("/check", response_model=SIMSwapResponse)
async def check_sim_swap(request: SIMSwapRequest):
    """
    Check if a SIM swap has occurred for the given phone number
    
    This endpoint simulates the CAMARA SIM Swap API functionality
    """
    try:
        response = mock_api.check_sim_swap(
            phone_number=request.phone_number,
            max_age_hours=request.max_age
        )
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SIM swap check failed: {str(e)}")


@router.get("/sim-history/{phone_number}", response_model=List[SIMInfo])
async def get_sim_history(phone_number: str):
    """Get SIM card history for a phone number (debug endpoint)"""
    sims = mock_api.sim_database.get(phone_number, [])
    return sims


@router.get("/patterns/{phone_number}")
async def get_swap_patterns(phone_number: str):
    """Get swap patterns for analysis (debug endpoint)"""
    patterns = mock_api.swap_patterns.get(phone_number, {})
    return patterns


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CAMARA SIM Swap API Mock",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database_size": len(mock_api.sim_database),
        "total_sims": sum(len(sims) for sims in mock_api.sim_database.values()),
        "operators_supported": sum(len(ops) for ops in mock_api.operators.values())
    }