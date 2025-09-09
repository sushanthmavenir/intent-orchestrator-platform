from typing import Dict, List, Any, Optional, Tuple
import asyncio
import httpx
from datetime import datetime, timedelta
import math

from ..base.base_agent import BaseAgent


class DeviceLocationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="device_location_agent",
            name="Device Location Analysis Agent", 
            description="Specialized agent for device location tracking and geospatial analysis using CAMARA Device Location API",
            capabilities=["location_verification", "movement_analysis", "geofencing", "location_risk_assessment"]
        )
        
        self.camara_base_url = "http://localhost:8001/camara"
        
    async def _initialize_agent(self) -> None:
        self.logger.info("Initializing Device Location Agent")
        
    async def _cleanup_agent(self) -> None:
        self.logger.info("Cleaning up Device Location Agent")
        
    async def execute_capability(self, capability_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if capability_type == "location_verification":
            return await self._verify_location(input_data)
        elif capability_type == "movement_analysis":
            return await self._analyze_movement(input_data)
        elif capability_type == "geofencing":
            return await self._check_geofence(input_data)
        elif capability_type == "location_risk_assessment":
            return await self._assess_location_risk(input_data)
        else:
            raise ValueError(f"Unsupported capability: {capability_type}")
            
    async def _verify_location(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number"])
        
        phone_number = input_data["phone_number"]
        expected_area = input_data.get("expected_area")
        accuracy = input_data.get("accuracy", 1000)  # meters
        
        self.logger.info(f"Verifying location for {phone_number}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.camara_base_url}/device-location/v1/retrieve",
                    json={
                        "device": {"phoneNumber": phone_number},
                        "area": expected_area,
                        "accuracy": accuracy
                    }
                )
                response.raise_for_status()
                location_data = response.json()
                
            verification_result = self._analyze_location_verification(location_data, expected_area)
            
            return {
                "phone_number": phone_number,
                "current_location": location_data.get("area", {}),
                "location_match": verification_result["match_status"],
                "match_confidence": verification_result["confidence"],
                "distance_from_expected": verification_result.get("distance_km"),
                "accuracy_radius_meters": location_data.get("accuracy", accuracy),
                "timestamp": location_data.get("timestamp", datetime.utcnow().isoformat()),
                "analysis": verification_result["analysis"],
                "confidence": 0.88,
                "recommendations": verification_result["recommendations"]
            }
            
        except Exception as e:
            self.logger.error(f"Location verification failed: {e}")
            return {
                "phone_number": phone_number,
                "error": f"Location verification failed: {str(e)}",
                "confidence": 0.0
            }
            
    async def _analyze_movement(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number"])
        
        phone_number = input_data["phone_number"]
        time_window_hours = input_data.get("time_window_hours", 24)
        
        try:
            # Get location history
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.camara_base_url}/device-location/v1/history/{phone_number}",
                    params={"hours": time_window_hours}
                )
                response.raise_for_status()
                history_data = response.json()
                
            movement_analysis = self._analyze_movement_patterns(history_data)
            
            return {
                "phone_number": phone_number,
                "time_window_hours": time_window_hours,
                "location_history": history_data.get("locations", []),
                "movement_patterns": movement_analysis,
                "total_distance_km": movement_analysis.get("total_distance", 0),
                "max_speed_kmh": movement_analysis.get("max_speed", 0),
                "unusual_movements": movement_analysis.get("anomalies", []),
                "confidence": 0.85
            }
            
        except Exception as e:
            self.logger.error(f"Movement analysis failed: {e}")
            return {
                "phone_number": phone_number,
                "error": f"Movement analysis failed: {str(e)}",
                "confidence": 0.0
            }
            
    async def _check_geofence(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number", "geofence_area"])
        
        phone_number = input_data["phone_number"]
        geofence = input_data["geofence_area"]
        
        try:
            # Get current location
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.camara_base_url}/device-location/v1/retrieve",
                    json={
                        "device": {"phoneNumber": phone_number},
                        "area": geofence
                    }
                )
                response.raise_for_status()
                location_data = response.json()
                
            # Check if device is within geofence
            within_geofence = self._check_within_area(location_data.get("area", {}), geofence)
            
            return {
                "phone_number": phone_number,
                "current_location": location_data.get("area", {}),
                "geofence_area": geofence,
                "within_geofence": within_geofence["inside"],
                "distance_to_boundary_meters": within_geofence.get("distance_to_boundary"),
                "geofence_confidence": within_geofence["confidence"],
                "timestamp": location_data.get("timestamp", datetime.utcnow().isoformat()),
                "confidence": 0.90
            }
            
        except Exception as e:
            self.logger.error(f"Geofence check failed: {e}")
            return {
                "phone_number": phone_number,
                "error": f"Geofence check failed: {str(e)}",
                "confidence": 0.0
            }
            
    async def _assess_location_risk(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number"])
        
        phone_number = input_data["phone_number"]
        context = input_data.get("context", {})
        risk_factors = []
        risk_score = 0.0
        
        try:
            # Get current location
            location_result = await self._verify_location({"phone_number": phone_number})
            
            if "error" in location_result:
                return location_result
                
            current_location = location_result.get("current_location", {})
            
            # Get movement history for risk analysis
            movement_result = await self._analyze_movement({
                "phone_number": phone_number,
                "time_window_hours": 48
            })
            
            # Analyze location-based risks
            location_risks = self._analyze_location_risks(current_location, context)
            movement_risks = self._analyze_movement_risks(movement_result, context)
            
            risk_factors.extend(location_risks["factors"])
            risk_factors.extend(movement_risks["factors"])
            
            risk_score = min(location_risks["score"] + movement_risks["score"], 1.0)
            
            return {
                "phone_number": phone_number,
                "current_location": current_location,
                "risk_score": round(risk_score, 3),
                "risk_level": self._categorize_risk(risk_score),
                "risk_factors": risk_factors,
                "location_analysis": location_risks["analysis"],
                "movement_analysis": movement_risks["analysis"],
                "confidence": 0.86,
                "recommendations": self._generate_location_recommendations(risk_score, risk_factors)
            }
            
        except Exception as e:
            self.logger.error(f"Location risk assessment failed: {e}")
            return {
                "phone_number": phone_number,
                "error": f"Location risk assessment failed: {str(e)}",
                "confidence": 0.0
            }
            
    def _analyze_location_verification(self, location_data: Dict[str, Any], 
                                     expected_area: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        current_area = location_data.get("area", {})
        
        if not expected_area:
            return {
                "match_status": "no_expected_location",
                "confidence": 0.5,
                "analysis": "No expected location provided for comparison",
                "recommendations": ["Specify expected location for verification"]
            }
            
        # Calculate distance between current and expected locations
        distance_km = self._calculate_distance(current_area, expected_area)
        
        if distance_km is None:
            return {
                "match_status": "unable_to_compare",
                "confidence": 0.0,
                "analysis": "Unable to compare locations due to missing coordinate data",
                "recommendations": ["Verify location data format and completeness"]
            }
            
        # Determine match status based on distance and accuracy
        accuracy_km = location_data.get("accuracy", 1000) / 1000  # Convert to km
        
        if distance_km <= accuracy_km:
            match_status = "exact_match"
            confidence = 0.95
            analysis = f"Device location matches expected area within {accuracy_km}km accuracy"
        elif distance_km <= accuracy_km * 2:
            match_status = "close_match" 
            confidence = 0.75
            analysis = f"Device location is {distance_km:.1f}km from expected area"
        elif distance_km <= 50:  # Within 50km
            match_status = "regional_match"
            confidence = 0.5
            analysis = f"Device location is in same region ({distance_km:.1f}km away)"
        else:
            match_status = "no_match"
            confidence = 0.1
            analysis = f"Device location is significantly different ({distance_km:.1f}km away)"
            
        recommendations = self._generate_verification_recommendations(match_status, distance_km)
        
        return {
            "match_status": match_status,
            "confidence": confidence,
            "distance_km": distance_km,
            "analysis": analysis,
            "recommendations": recommendations
        }
        
    def _analyze_movement_patterns(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        locations = history_data.get("locations", [])
        
        if len(locations) < 2:
            return {
                "total_distance": 0,
                "max_speed": 0,
                "anomalies": [],
                "movement_type": "stationary"
            }
            
        total_distance = 0
        max_speed = 0
        anomalies = []
        
        # Sort locations by timestamp
        sorted_locations = sorted(locations, key=lambda x: x.get("timestamp", ""))
        
        for i in range(1, len(sorted_locations)):
            prev_loc = sorted_locations[i-1]
            curr_loc = sorted_locations[i]
            
            # Calculate distance and speed
            distance = self._calculate_distance(prev_loc.get("area", {}), curr_loc.get("area", {}))
            
            if distance is not None:
                total_distance += distance
                
                # Calculate speed if timestamps available
                prev_time = prev_loc.get("timestamp")
                curr_time = curr_loc.get("timestamp")
                
                if prev_time and curr_time:
                    try:
                        time_diff_hours = (
                            datetime.fromisoformat(curr_time.replace('Z', '+00:00')) - 
                            datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
                        ).total_seconds() / 3600
                        
                        if time_diff_hours > 0:
                            speed_kmh = distance / time_diff_hours
                            max_speed = max(max_speed, speed_kmh)
                            
                            # Detect anomalous speeds
                            if speed_kmh > 500:  # Faster than commercial aircraft
                                anomalies.append({
                                    "type": "impossible_speed",
                                    "speed_kmh": round(speed_kmh, 1),
                                    "timestamp": curr_time,
                                    "description": f"Impossibly high speed: {speed_kmh:.1f} km/h"
                                })
                            elif speed_kmh > 200:  # Faster than highway speeds
                                anomalies.append({
                                    "type": "high_speed",
                                    "speed_kmh": round(speed_kmh, 1),
                                    "timestamp": curr_time,
                                    "description": f"Unusually high speed: {speed_kmh:.1f} km/h"
                                })
                                
                    except Exception:
                        pass
                        
        # Determine movement type
        if total_distance < 1:
            movement_type = "stationary"
        elif total_distance < 50:
            movement_type = "local"
        elif total_distance < 200:
            movement_type = "regional"
        else:
            movement_type = "long_distance"
            
        return {
            "total_distance": round(total_distance, 2),
            "max_speed": round(max_speed, 1),
            "anomalies": anomalies,
            "movement_type": movement_type,
            "location_count": len(locations)
        }
        
    def _check_within_area(self, current_location: Dict[str, Any], 
                          geofence: Dict[str, Any]) -> Dict[str, Any]:
        # Simplified geofence checking
        # In production, would use proper geometric calculations
        
        current_lat = current_location.get("latitude")
        current_lon = current_location.get("longitude")
        
        if not all([current_lat, current_lon]):
            return {"inside": False, "confidence": 0.0}
            
        # Check if geofence is circular (has radius)
        if "radius" in geofence:
            center_lat = geofence.get("latitude")
            center_lon = geofence.get("longitude")
            radius_meters = geofence.get("radius", 1000)
            
            if not all([center_lat, center_lon]):
                return {"inside": False, "confidence": 0.0}
                
            distance_meters = self._calculate_distance_meters(
                (current_lat, current_lon),
                (center_lat, center_lon)
            )
            
            inside = distance_meters <= radius_meters
            distance_to_boundary = abs(distance_meters - radius_meters)
            
            return {
                "inside": inside,
                "confidence": 0.9,
                "distance_to_boundary": distance_to_boundary
            }
            
        # For other geofence types, return basic check
        return {"inside": True, "confidence": 0.5}
        
    def _calculate_distance(self, loc1: Dict[str, Any], loc2: Dict[str, Any]) -> Optional[float]:
        lat1 = loc1.get("latitude")
        lon1 = loc1.get("longitude")
        lat2 = loc2.get("latitude")
        lon2 = loc2.get("longitude")
        
        if not all([lat1, lon1, lat2, lon2]):
            return None
            
        return self._haversine_distance(lat1, lon1, lat2, lon2)
        
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371  # Earth radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
        
    def _calculate_distance_meters(self, point1: Tuple[float, float], 
                                  point2: Tuple[float, float]) -> float:
        lat1, lon1 = point1
        lat2, lon2 = point2
        return self._haversine_distance(lat1, lon1, lat2, lon2) * 1000
        
    def _analyze_location_risks(self, location: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        risk_factors = []
        risk_score = 0.0
        
        # High-risk areas (simplified - would use real geospatial data)
        high_risk_countries = context.get("high_risk_countries", ["XX", "YY"])  # ISO codes
        country = location.get("country", "")
        
        if country in high_risk_countries:
            risk_factors.append(f"Device located in high-risk country: {country}")
            risk_score += 0.3
            
        # Unusual location for user
        if context.get("user_home_country") and context["user_home_country"] != country:
            risk_factors.append("Device in different country than user's home")
            risk_score += 0.2
            
        # VPN/proxy detection (simplified)
        if context.get("vpn_detected"):
            risk_factors.append("VPN or proxy usage detected")
            risk_score += 0.1
            
        analysis = "Standard location-based risk assessment completed"
        if risk_factors:
            analysis = f"Identified {len(risk_factors)} location-based risk factors"
            
        return {
            "score": min(risk_score, 0.5),  # Cap location risk at 0.5
            "factors": risk_factors,
            "analysis": analysis
        }
        
    def _analyze_movement_risks(self, movement_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        risk_factors = []
        risk_score = 0.0
        
        if "error" in movement_data:
            return {"score": 0.0, "factors": [], "analysis": "Unable to analyze movement patterns"}
            
        anomalies = movement_data.get("unusual_movements", [])
        total_distance = movement_data.get("total_distance_km", 0)
        max_speed = movement_data.get("max_speed_kmh", 0)
        
        # Analyze anomalies
        for anomaly in anomalies:
            if anomaly.get("type") == "impossible_speed":
                risk_factors.append("Impossible travel speeds detected (possible location spoofing)")
                risk_score += 0.4
            elif anomaly.get("type") == "high_speed":
                risk_factors.append("Unusually high travel speeds detected")
                risk_score += 0.2
                
        # Rapid long-distance travel
        if total_distance > 1000:  # More than 1000km in time window
            risk_factors.append("Extensive long-distance travel detected")
            risk_score += 0.2
            
        # Context-based movement risks
        if context.get("account_compromise_suspected") and total_distance > 100:
            risk_factors.append("Unusual movement during suspected account compromise")
            risk_score += 0.3
            
        analysis = "Movement pattern analysis completed"
        if risk_factors:
            analysis = f"Detected {len(risk_factors)} movement-based risk indicators"
            
        return {
            "score": min(risk_score, 0.5),  # Cap movement risk at 0.5
            "factors": risk_factors,
            "analysis": analysis
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
            
    def _generate_verification_recommendations(self, match_status: str, distance_km: Optional[float]) -> List[str]:
        if match_status == "exact_match":
            return ["Location verified successfully", "Proceed with normal operations"]
        elif match_status == "close_match":
            return ["Location approximately verified", "Consider additional verification for sensitive operations"]
        elif match_status == "regional_match":
            return ["Location in expected region", "Verify user travel or relocation", "Apply enhanced monitoring"]
        elif match_status == "no_match":
            return ["Location verification failed", "Implement immediate security measures", "Require additional authentication"]
        else:
            return ["Unable to verify location", "Request user confirmation of current location"]
            
    def _generate_location_recommendations(self, risk_score: float, risk_factors: List[str]) -> List[str]:
        recommendations = []
        
        if risk_score >= 0.8:
            recommendations.extend([
                "URGENT: Implement immediate location-based security measures",
                "Block high-risk transactions",
                "Require additional authentication",
                "Consider account suspension pending verification"
            ])
        elif risk_score >= 0.5:
            recommendations.extend([
                "Enhanced location monitoring required",
                "Apply additional verification for sensitive operations",
                "Review recent account activities"
            ])
        elif risk_score >= 0.2:
            recommendations.extend([
                "Standard location monitoring",
                "Document location patterns for future reference"
            ])
        else:
            recommendations.append("Continue normal location monitoring")
            
        return recommendations
        
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
                "location_verification",
                "movement_analysis",
                "geofencing",
                "location_risk_assessment"
            ]
        }