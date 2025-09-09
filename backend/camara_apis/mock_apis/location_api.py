from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import random
import math
import uuid


class LocationRequest(BaseModel):
    device: Union[str, Dict[str, str]] = Field(..., description="Device identifier (phone number or device ID)")
    max_age: Optional[int] = Field(60, description="Maximum age in minutes for location data")
    requested_accuracy: Optional[int] = Field(1000, description="Requested accuracy in meters")


class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: int = Field(..., description="Accuracy in meters")


class LocationResponse(BaseModel):
    device: str
    location: Coordinates
    timestamp: datetime
    age_seconds: int
    confidence: float = Field(..., ge=0.0, le=1.0)
    location_type: str  # "gps", "network", "cell_tower", "wifi"
    country: str
    region: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    timezone: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LocationHistory(BaseModel):
    device: str
    locations: List[Dict[str, Any]]
    time_range: Dict[str, datetime]
    total_points: int


router = APIRouter(prefix="/camara/location/v1", tags=["CAMARA Device Location API"])


class MockLocationAPI:
    """
    Mock implementation of CAMARA Device Location API
    Simulates device location tracking with realistic geographic data
    """
    
    def __init__(self):
        self.major_cities = self._get_major_cities()
        self.country_data = self._get_country_data()
        self.location_database = self._generate_mock_locations()
        self.location_history = self._generate_location_history()
    
    def _get_major_cities(self) -> List[Dict[str, Any]]:
        """Major cities with coordinates for realistic simulation"""
        return [
            {"name": "New York", "country": "US", "lat": 40.7128, "lng": -74.0060, "timezone": "America/New_York"},
            {"name": "London", "country": "UK", "lat": 51.5074, "lng": -0.1278, "timezone": "Europe/London"},
            {"name": "Lagos", "country": "NG", "lat": 6.5244, "lng": 3.3792, "timezone": "Africa/Lagos"},
            {"name": "Paris", "country": "FR", "lat": 48.8566, "lng": 2.3522, "timezone": "Europe/Paris"},
            {"name": "Berlin", "country": "DE", "lat": 52.5200, "lng": 13.4050, "timezone": "Europe/Berlin"},
            {"name": "Tokyo", "country": "JP", "lat": 35.6762, "lng": 139.6503, "timezone": "Asia/Tokyo"},
            {"name": "Sydney", "country": "AU", "lat": -33.8688, "lng": 151.2093, "timezone": "Australia/Sydney"},
            {"name": "Mumbai", "country": "IN", "lat": 19.0760, "lng": 72.8777, "timezone": "Asia/Kolkata"},
            {"name": "São Paulo", "country": "BR", "lat": -23.5505, "lng": -46.6333, "timezone": "America/Sao_Paulo"},
            {"name": "Dubai", "country": "AE", "lat": 25.2048, "lng": 55.2708, "timezone": "Asia/Dubai"}
        ]
    
    def _get_country_data(self) -> Dict[str, Dict[str, str]]:
        """Country code mappings"""
        return {
            "US": {"name": "United States", "region": "North America"},
            "UK": {"name": "United Kingdom", "region": "Europe"},
            "NG": {"name": "Nigeria", "region": "Africa"},
            "FR": {"name": "France", "region": "Europe"},
            "DE": {"name": "Germany", "region": "Europe"},
            "JP": {"name": "Japan", "region": "Asia"},
            "AU": {"name": "Australia", "region": "Oceania"},
            "IN": {"name": "India", "region": "Asia"},
            "BR": {"name": "Brazil", "region": "South America"},
            "AE": {"name": "United Arab Emirates", "region": "Middle East"}
        }
    
    def _generate_mock_locations(self) -> Dict[str, Dict[str, Any]]:
        """Generate mock current locations for devices"""
        mock_data = {}
        
        # Sample device identifiers
        devices = [
            "+1234567890", "+1234567891", "+1234567892", "+1234567893",
            "+442071234567", "+33123456789", "+49301234567", 
            "+2348012345678", "device_001", "device_002"
        ]
        
        for device in devices:
            # Select a random city as current location
            base_city = random.choice(self.major_cities)
            
            # Add some randomness to exact coordinates (within ~5km)
            lat_offset = random.uniform(-0.045, 0.045)  # ~5km at equator
            lng_offset = random.uniform(-0.045, 0.045)
            
            current_lat = base_city["lat"] + lat_offset
            current_lng = base_city["lng"] + lng_offset
            
            # Determine location accuracy and type
            location_types = ["gps", "network", "cell_tower", "wifi"]
            location_type = random.choice(location_types)
            
            accuracy_ranges = {
                "gps": (5, 20),
                "network": (100, 500),
                "cell_tower": (500, 2000),
                "wifi": (20, 100)
            }
            
            accuracy = random.randint(*accuracy_ranges[location_type])
            
            # Generate timestamp (recent)
            minutes_ago = random.randint(1, 60)
            timestamp = datetime.utcnow() - timedelta(minutes=minutes_ago)
            
            # Determine if this is a suspicious location change
            is_suspicious = random.random() < 0.15  # 15% chance
            
            if is_suspicious:
                # Pick a different country/city for suspicious activity
                suspicious_cities = [c for c in self.major_cities if c["country"] != base_city["country"]]
                if suspicious_cities:
                    sus_city = random.choice(suspicious_cities)
                    current_lat = sus_city["lat"] + random.uniform(-0.02, 0.02)
                    current_lng = sus_city["lng"] + random.uniform(-0.02, 0.02)
                    base_city = sus_city
            
            mock_data[device] = {
                "latitude": current_lat,
                "longitude": current_lng,
                "accuracy": accuracy,
                "timestamp": timestamp,
                "location_type": location_type,
                "city_info": base_city,
                "is_suspicious": is_suspicious,
                "confidence": random.uniform(0.7, 0.98)
            }
        
        return mock_data
    
    def _generate_location_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate location history for devices"""
        history = {}
        
        for device, current_location in self.location_database.items():
            device_history = []
            num_points = random.randint(5, 20)
            
            # Start from current location and work backwards
            base_lat = current_location["latitude"]
            base_lng = current_location["longitude"]
            base_city = current_location["city_info"]
            
            for i in range(num_points):
                # Generate historical timestamps
                hours_ago = i * random.randint(1, 4) + random.randint(0, 2)
                timestamp = datetime.utcnow() - timedelta(hours=hours_ago)
                
                # Most locations should be near the base location
                if random.random() < 0.8:  # 80% near base location
                    lat = base_lat + random.uniform(-0.02, 0.02)
                    lng = base_lng + random.uniform(-0.02, 0.02)
                    city_info = base_city
                else:  # 20% at different locations
                    different_city = random.choice(self.major_cities)
                    lat = different_city["lat"] + random.uniform(-0.01, 0.01)
                    lng = different_city["lng"] + random.uniform(-0.01, 0.01)
                    city_info = different_city
                
                location_type = random.choice(["gps", "network", "cell_tower", "wifi"])
                accuracy_ranges = {
                    "gps": (5, 20),
                    "network": (100, 500),
                    "cell_tower": (500, 2000),
                    "wifi": (20, 100)
                }
                accuracy = random.randint(*accuracy_ranges[location_type])
                
                device_history.append({
                    "latitude": lat,
                    "longitude": lng,
                    "accuracy": accuracy,
                    "timestamp": timestamp,
                    "location_type": location_type,
                    "city_info": city_info,
                    "confidence": random.uniform(0.6, 0.95)
                })
            
            # Sort by timestamp (oldest first)
            device_history.sort(key=lambda x: x["timestamp"])
            history[device] = device_history
        
        return history
    
    def get_location(self, device_id: str, max_age_minutes: int = 60, 
                    requested_accuracy: int = 1000) -> LocationResponse:
        """Get current location for a device"""
        
        # Simulate API delay
        import time
        time.sleep(random.uniform(0.1, 0.3))
        
        # Get device location data
        location_data = self.location_database.get(device_id)
        
        if not location_data:
            # Generate a random location for unknown devices
            random_city = random.choice(self.major_cities)
            location_data = {
                "latitude": random_city["lat"] + random.uniform(-0.01, 0.01),
                "longitude": random_city["lng"] + random.uniform(-0.01, 0.01),
                "accuracy": random.randint(100, 1000),
                "timestamp": datetime.utcnow() - timedelta(minutes=random.randint(1, 30)),
                "location_type": "network",
                "city_info": random_city,
                "is_suspicious": False,
                "confidence": 0.6
            }
        
        # Check if location is within max age
        age_seconds = (datetime.utcnow() - location_data["timestamp"]).total_seconds()
        age_minutes = age_seconds / 60
        
        if age_minutes > max_age_minutes:
            # Simulate stale location data
            confidence_penalty = min(0.3, (age_minutes - max_age_minutes) / 100)
            location_data["confidence"] = max(0.3, location_data["confidence"] - confidence_penalty)
        
        # Apply accuracy requirements
        if location_data["accuracy"] > requested_accuracy:
            # Reduce confidence for less accurate data
            accuracy_ratio = requested_accuracy / location_data["accuracy"]
            location_data["confidence"] *= accuracy_ratio
        
        # Get city information
        city_info = location_data["city_info"]
        country_info = self.country_data.get(city_info["country"], {})
        
        # Create response
        coordinates = Coordinates(
            latitude=location_data["latitude"],
            longitude=location_data["longitude"],
            accuracy=location_data["accuracy"]
        )
        
        # Generate postal code (mock)
        postal_code = f"{random.randint(10000, 99999)}"
        if city_info["country"] == "UK":
            postal_code = f"SW{random.randint(1, 9)}A {random.randint(1, 9)}AA"
        elif city_info["country"] == "DE":
            postal_code = f"{random.randint(10000, 99999)}"
        
        metadata = {
            "source": "mock_camara_api",
            "movement_detected": location_data["is_suspicious"],
            "signal_strength": random.randint(-100, -60),
            "satellite_count": random.randint(4, 12) if location_data["location_type"] == "gps" else None,
            "cell_tower_id": f"tower_{random.randint(1000, 9999)}" if location_data["location_type"] == "cell_tower" else None,
            "wifi_network_count": random.randint(5, 15) if location_data["location_type"] == "wifi" else None
        }
        
        # Add risk indicators for suspicious locations
        if location_data["is_suspicious"]:
            metadata["risk_indicators"] = ["unusual_location", "rapid_movement"]
            metadata["travel_speed_kmh"] = random.randint(500, 1200)  # Impossible travel speed
        
        return LocationResponse(
            device=device_id,
            location=coordinates,
            timestamp=location_data["timestamp"],
            age_seconds=int(age_seconds),
            confidence=location_data["confidence"],
            location_type=location_data["location_type"],
            country=city_info["country"],
            region=country_info.get("region"),
            city=city_info["name"],
            postal_code=postal_code,
            timezone=city_info["timezone"],
            metadata=metadata
        )
    
    def get_location_history(self, device_id: str, hours_back: int = 24) -> LocationHistory:
        """Get location history for a device"""
        history_data = self.location_history.get(device_id, [])
        
        # Filter by time range
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        filtered_history = [
            loc for loc in history_data 
            if loc["timestamp"] > cutoff_time
        ]
        
        # Convert to response format
        locations = []
        for loc in filtered_history:
            city_info = loc["city_info"]
            locations.append({
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "accuracy": loc["accuracy"],
                "timestamp": loc["timestamp"].isoformat(),
                "location_type": loc["location_type"],
                "city": city_info["name"],
                "country": city_info["country"],
                "confidence": loc["confidence"]
            })
        
        time_range = {
            "start": min(loc["timestamp"] for loc in filtered_history) if filtered_history else datetime.utcnow(),
            "end": max(loc["timestamp"] for loc in filtered_history) if filtered_history else datetime.utcnow()
        }
        
        return LocationHistory(
            device=device_id,
            locations=locations,
            time_range=time_range,
            total_points=len(locations)
        )
    
    def calculate_distance_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


# Create API instance
mock_api = MockLocationAPI()


@router.post("/retrieve", response_model=LocationResponse)
async def get_device_location(request: LocationRequest):
    """
    Get current location of a device
    
    This endpoint simulates the CAMARA Device Location API functionality
    """
    try:
        device_id = request.device
        if isinstance(device_id, dict):
            device_id = device_id.get("phoneNumber") or device_id.get("deviceId", "unknown")
        
        response = mock_api.get_location(
            device_id=device_id,
            max_age_minutes=request.max_age,
            requested_accuracy=request.requested_accuracy
        )
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Location retrieval failed: {str(e)}")


@router.get("/history/{device_id}", response_model=LocationHistory)
async def get_device_location_history(device_id: str, hours_back: int = 24):
    """Get location history for a device (debug endpoint)"""
    try:
        history = mock_api.get_location_history(device_id, hours_back)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get("/cities")
async def get_supported_cities():
    """Get list of supported cities (debug endpoint)"""
    return mock_api.major_cities


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CAMARA Device Location API Mock",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "tracked_devices": len(mock_api.location_database),
        "supported_cities": len(mock_api.major_cities),
        "supported_countries": len(mock_api.country_data),
        "location_types": ["gps", "network", "cell_tower", "wifi"]
    }