from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random
import uuid
from enum import Enum


class SwapStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class DeviceSwapRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to check for device swap")
    max_age: Optional[int] = Field(240, description="Maximum age in hours to check for swaps")


class DeviceSwapResponse(BaseModel):
    phone_number: str
    swapped: bool
    swap_date: Optional[datetime] = None
    previous_device_id: Optional[str] = None
    current_device_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeviceInfo(BaseModel):
    device_id: str
    imei: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None
    first_seen: datetime
    last_seen: datetime


router = APIRouter(prefix="/camara/device-swap/v1", tags=["CAMARA Device Swap API"])


class MockDeviceSwapAPI:
    """
    Mock implementation of CAMARA Device Swap API
    Simulates device swap detection with realistic response patterns
    """
    
    def __init__(self):
        self.device_database = self._generate_mock_device_data()
        self.swap_history = self._generate_swap_history()
    
    def _generate_mock_device_data(self) -> Dict[str, List[DeviceInfo]]:
        """Generate mock device data for testing"""
        mock_data = {}
        
        # Sample phone numbers with different device patterns
        phone_numbers = [
            "+1234567890", "+1234567891", "+1234567892", "+1234567893", "+1234567894",
            "+442071234567", "+33123456789", "+49301234567", "+8613912345678"
        ]
        
        device_makes = ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi", "Huawei"]
        device_models = ["iPhone 13", "Galaxy S21", "Pixel 6", "OnePlus 9", "Mi 11", "P40"]
        
        for phone in phone_numbers:
            devices = []
            num_devices = random.randint(1, 4)  # 1-4 devices per number
            
            for i in range(num_devices):
                device_id = str(uuid.uuid4())
                imei = f"{random.randint(100000000000000, 999999999999999)}"
                make = random.choice(device_makes)
                model = random.choice(device_models)
                
                # Create timeline for device usage
                days_ago = random.randint(1, 365)
                first_seen = datetime.utcnow() - timedelta(days=days_ago)
                
                if i == num_devices - 1:  # Most recent device
                    last_seen = datetime.utcnow()
                else:
                    last_seen = first_seen + timedelta(days=random.randint(30, 200))
                
                devices.append(DeviceInfo(
                    device_id=device_id,
                    imei=imei,
                    make=make,
                    model=model,
                    os_version=f"{random.randint(10, 15)}.{random.randint(0, 9)}",
                    first_seen=first_seen,
                    last_seen=last_seen
                ))
            
            # Sort devices by first_seen date
            devices.sort(key=lambda d: d.first_seen)
            mock_data[phone] = devices
        
        return mock_data
    
    def _generate_swap_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate swap event history"""
        swap_history = {}
        
        for phone_number, devices in self.device_database.items():
            swaps = []
            
            # Generate swap events when there are multiple devices
            if len(devices) > 1:
                for i in range(1, len(devices)):
                    prev_device = devices[i - 1]
                    curr_device = devices[i]
                    
                    # Determine if this was a suspicious swap
                    time_gap = (curr_device.first_seen - prev_device.last_seen).total_seconds()
                    is_suspicious = time_gap < 3600  # Less than 1 hour gap
                    
                    swap_event = {
                        'swap_date': curr_device.first_seen,
                        'from_device_id': prev_device.device_id,
                        'to_device_id': curr_device.device_id,
                        'suspicious': is_suspicious,
                        'time_gap_seconds': time_gap,
                        'location_change': random.choice([True, False]),
                        'risk_score': random.uniform(0.1, 0.9) if is_suspicious else random.uniform(0.0, 0.3)
                    }
                    swaps.append(swap_event)
            
            swap_history[phone_number] = swaps
        
        return swap_history
    
    def check_device_swap(self, phone_number: str, max_age_hours: int = 240) -> DeviceSwapResponse:
        """Check if a device swap occurred for the given phone number"""
        
        # Simulate API delay
        import time
        time.sleep(random.uniform(0.1, 0.5))
        
        # Get device history for phone number
        devices = self.device_database.get(phone_number, [])
        
        if not devices:
            # Generate a basic response for unknown numbers
            return DeviceSwapResponse(
                phone_number=phone_number,
                swapped=False,
                current_device_id=str(uuid.uuid4()),
                confidence=0.5,
                risk_level="unknown",
                metadata={'reason': 'no_device_history'}
            )
        
        # Get most recent device
        current_device = devices[-1]
        
        # Check for recent swaps
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        recent_swaps = [
            swap for swap in self.swap_history.get(phone_number, [])
            if swap['swap_date'] > cutoff_time
        ]
        
        if recent_swaps:
            # Most recent swap
            latest_swap = max(recent_swaps, key=lambda s: s['swap_date'])
            
            # Calculate confidence based on various factors
            confidence = self._calculate_confidence(latest_swap, current_device)
            
            # Determine risk level
            risk_level = self._determine_risk_level(latest_swap, confidence)
            
            return DeviceSwapResponse(
                phone_number=phone_number,
                swapped=True,
                swap_date=latest_swap['swap_date'],
                previous_device_id=latest_swap['from_device_id'],
                current_device_id=current_device.device_id,
                confidence=confidence,
                risk_level=risk_level,
                metadata={
                    'swap_count_in_period': len(recent_swaps),
                    'time_since_swap_hours': (datetime.utcnow() - latest_swap['swap_date']).total_seconds() / 3600,
                    'location_changed': latest_swap['location_change'],
                    'device_make': current_device.make,
                    'device_model': current_device.model
                }
            )
        else:
            # No recent swaps
            return DeviceSwapResponse(
                phone_number=phone_number,
                swapped=False,
                current_device_id=current_device.device_id,
                confidence=0.95,
                risk_level="low",
                metadata={
                    'device_age_days': (datetime.utcnow() - current_device.first_seen).days,
                    'device_make': current_device.make,
                    'device_model': current_device.model,
                    'total_devices_ever': len(devices)
                }
            )
    
    def _calculate_confidence(self, swap_event: Dict[str, Any], current_device: DeviceInfo) -> float:
        """Calculate confidence score for swap detection"""
        base_confidence = 0.8
        
        # Adjust based on time gap
        time_gap = swap_event['time_gap_seconds']
        if time_gap < 300:  # Less than 5 minutes
            base_confidence += 0.15
        elif time_gap < 3600:  # Less than 1 hour
            base_confidence += 0.1
        elif time_gap > 86400:  # More than 1 day
            base_confidence -= 0.1
        
        # Adjust based on location change
        if swap_event['location_change']:
            base_confidence += 0.05
        
        # Adjust based on device age
        device_age = (datetime.utcnow() - current_device.first_seen).days
        if device_age < 1:  # Very new device
            base_confidence += 0.05
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def _determine_risk_level(self, swap_event: Dict[str, Any], confidence: float) -> str:
        """Determine risk level based on swap characteristics"""
        risk_score = swap_event['risk_score']
        
        if confidence > 0.9 and risk_score > 0.7:
            return "high"
        elif confidence > 0.7 and risk_score > 0.5:
            return "medium"
        elif confidence > 0.5:
            return "low"
        else:
            return "unknown"


# Create API instance
mock_api = MockDeviceSwapAPI()


@router.post("/check", response_model=DeviceSwapResponse)
async def check_device_swap(request: DeviceSwapRequest):
    """
    Check if a device swap has occurred for the given phone number
    
    This endpoint simulates the CAMARA Device Swap API functionality
    """
    try:
        response = mock_api.check_device_swap(
            phone_number=request.phone_number,
            max_age_hours=request.max_age
        )
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Device swap check failed: {str(e)}")


@router.get("/devices/{phone_number}", response_model=List[DeviceInfo])
async def get_device_history(phone_number: str):
    """Get device history for a phone number (debug endpoint)"""
    devices = mock_api.device_database.get(phone_number, [])
    return devices


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CAMARA Device Swap API Mock",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database_size": len(mock_api.device_database),
        "total_devices": sum(len(devices) for devices in mock_api.device_database.values())
    }