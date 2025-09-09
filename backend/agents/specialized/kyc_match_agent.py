from typing import Dict, List, Any
import asyncio
import httpx
from datetime import datetime
import re

from ..base.base_agent import BaseAgent


class KYCMatchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="kyc_match_agent",
            name="KYC Match Verification Agent",
            description="Specialized agent for identity verification using CAMARA KYC Match API",
            capabilities=["identity_verification", "document_validation", "compliance_check"]
        )
        
        self.camara_base_url = "http://localhost:8001/camara"
        
    async def _initialize_agent(self) -> None:
        self.logger.info("Initializing KYC Match Agent")
        
    async def _cleanup_agent(self) -> None:
        self.logger.info("Cleaning up KYC Match Agent")
        
    async def execute_capability(self, capability_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if capability_type == "identity_verification":
            return await self._verify_identity(input_data)
        elif capability_type == "document_validation":
            return await self._validate_documents(input_data)
        elif capability_type == "compliance_check":
            return await self._perform_compliance_check(input_data)
        else:
            raise ValueError(f"Unsupported capability: {capability_type}")
            
    async def _verify_identity(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number", "verification_data"])
        
        phone_number = input_data["phone_number"]
        verification_data = input_data["verification_data"]
        
        self.logger.info(f"Performing identity verification for {phone_number}")
        
        try:
            # Prepare KYC match request
            kyc_request = {
                "phoneNumber": phone_number,
                "idDocument": verification_data.get("id_document", ""),
                "name": verification_data.get("name", ""),
                "givenName": verification_data.get("given_name", ""),
                "familyName": verification_data.get("family_name", ""),
                "nameKana": verification_data.get("name_kana", ""),
                "givenNameKana": verification_data.get("given_name_kana", ""),
                "familyNameKana": verification_data.get("family_name_kana", ""),
                "birthdate": verification_data.get("birthdate", ""),
                "email": verification_data.get("email", ""),
                "address": verification_data.get("address", ""),
                "houseNumber": verification_data.get("house_number", ""),
                "street": verification_data.get("street", ""),
                "city": verification_data.get("city", ""),
                "region": verification_data.get("region", ""),
                "country": verification_data.get("country", ""),
                "postalCode": verification_data.get("postal_code", "")
            }
            
            # Remove empty fields
            kyc_request = {k: v for k, v in kyc_request.items() if v}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.camara_base_url}/kyc-match/v1/match",
                    json=kyc_request
                )
                response.raise_for_status()
                kyc_result = response.json()
                
            # Analyze verification results
            verification_analysis = self._analyze_verification_results(kyc_result, verification_data)
            
            return {
                "phone_number": phone_number,
                "verification_status": kyc_result.get("match", "unknown"),
                "match_score": kyc_result.get("matchScore", 0.0),
                "field_matches": kyc_result.get("matchedFields", {}),
                "verification_analysis": verification_analysis,
                "risk_assessment": self._assess_identity_risk(kyc_result, verification_analysis),
                "confidence": 0.89,
                "recommendations": self._generate_verification_recommendations(kyc_result)
            }
            
        except Exception as e:
            self.logger.error(f"Identity verification failed: {e}")
            return {
                "phone_number": phone_number,
                "error": f"Identity verification failed: {str(e)}",
                "confidence": 0.0
            }
            
    async def _validate_documents(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["documents"])
        
        documents = input_data["documents"]
        phone_number = input_data.get("phone_number")
        
        validation_results = []
        
        for doc in documents:
            doc_type = doc.get("type", "unknown")
            doc_number = doc.get("number", "")
            
            validation = {
                "document_type": doc_type,
                "document_number": doc_number,
                "format_valid": self._validate_document_format(doc_type, doc_number),
                "checksum_valid": self._validate_checksum(doc_type, doc_number)
            }
            
            # If phone number provided, check against KYC records
            if phone_number:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{self.camara_base_url}/kyc-match/v1/match",
                            json={
                                "phoneNumber": phone_number,
                                "idDocument": doc_number
                            }
                        )
                        response.raise_for_status()
                        kyc_result = response.json()
                        
                    validation["kyc_match"] = kyc_result.get("match", "unknown")
                    validation["match_confidence"] = kyc_result.get("matchScore", 0.0)
                    
                except Exception:
                    validation["kyc_match"] = "error"
                    validation["match_confidence"] = 0.0
                    
            validation_results.append(validation)
            
        overall_validity = all(doc.get("format_valid", False) for doc in validation_results)
        
        return {
            "phone_number": phone_number,
            "document_validations": validation_results,
            "overall_validity": overall_validity,
            "confidence": 0.85,
            "recommendations": self._generate_document_recommendations(validation_results)
        }
        
    async def _perform_compliance_check(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data, ["phone_number", "compliance_requirements"])
        
        phone_number = input_data["phone_number"]
        requirements = input_data["compliance_requirements"]
        customer_data = input_data.get("customer_data", {})
        
        compliance_results = {
            "phone_number": phone_number,
            "compliance_status": "compliant",
            "failed_checks": [],
            "warnings": [],
            "requirements_met": []
        }
        
        # Check identity verification requirement
        if "identity_verification" in requirements:
            if customer_data.get("identity_verified"):
                compliance_results["requirements_met"].append("identity_verification")
            else:
                compliance_results["failed_checks"].append("identity_verification_missing")
                compliance_results["compliance_status"] = "non_compliant"
                
        # Check document validation requirement
        if "document_validation" in requirements:
            if customer_data.get("documents_validated"):
                compliance_results["requirements_met"].append("document_validation")
            else:
                compliance_results["failed_checks"].append("document_validation_missing")
                compliance_results["compliance_status"] = "non_compliant"
                
        # Check address verification
        if "address_verification" in requirements:
            if customer_data.get("address_verified"):
                compliance_results["requirements_met"].append("address_verification")
            else:
                compliance_results["warnings"].append("address_verification_recommended")
                
        # Check age verification
        if "age_verification" in requirements:
            birthdate = customer_data.get("birthdate")
            if birthdate and self._verify_minimum_age(birthdate, requirements.get("minimum_age", 18)):
                compliance_results["requirements_met"].append("age_verification")
            else:
                compliance_results["failed_checks"].append("age_verification_failed")
                compliance_results["compliance_status"] = "non_compliant"
                
        return {
            **compliance_results,
            "confidence": 0.92,
            "recommendations": self._generate_compliance_recommendations(compliance_results)
        }
        
    def _analyze_verification_results(self, kyc_result: Dict[str, Any], 
                                    verification_data: Dict[str, Any]) -> Dict[str, Any]:
        match_status = kyc_result.get("match", "unknown")
        match_score = kyc_result.get("matchScore", 0.0)
        matched_fields = kyc_result.get("matchedFields", {})
        
        analysis = {
            "overall_match": match_status,
            "confidence_score": match_score,
            "matched_attributes": list(matched_fields.keys()),
            "verification_strength": "strong" if match_score > 0.8 else "moderate" if match_score > 0.5 else "weak"
        }
        
        # Analyze specific field matches
        critical_fields = ["name", "birthdate", "idDocument"]
        critical_matches = sum(1 for field in critical_fields if matched_fields.get(field) == "true")
        
        analysis["critical_field_matches"] = critical_matches
        analysis["critical_match_ratio"] = critical_matches / len(critical_fields)
        
        return analysis
        
    def _assess_identity_risk(self, kyc_result: Dict[str, Any], 
                            analysis: Dict[str, Any]) -> Dict[str, Any]:
        risk_score = 0.0
        risk_factors = []
        
        match_score = kyc_result.get("matchScore", 0.0)
        
        # Low match score increases risk
        if match_score < 0.3:
            risk_score += 0.8
            risk_factors.append("Very low identity match score")
        elif match_score < 0.6:
            risk_score += 0.4
            risk_factors.append("Low identity match score")
            
        # Missing critical field matches
        critical_ratio = analysis.get("critical_match_ratio", 0.0)
        if critical_ratio < 0.5:
            risk_score += 0.3
            risk_factors.append("Missing critical identity field matches")
            
        # Partial matches can indicate identity manipulation
        matched_fields = kyc_result.get("matchedFields", {})
        partial_matches = sum(1 for v in matched_fields.values() if v == "partial")
        if partial_matches > 0:
            risk_score += 0.2
            risk_factors.append(f"Partial matches detected ({partial_matches} fields)")
            
        risk_score = min(risk_score, 1.0)
        
        return {
            "risk_score": round(risk_score, 3),
            "risk_level": self._categorize_risk(risk_score),
            "risk_factors": risk_factors
        }
        
    def _validate_document_format(self, doc_type: str, doc_number: str) -> bool:
        if not doc_number:
            return False
            
        # Basic format validation patterns
        patterns = {
            "passport": r"^[A-Z]{1,2}[0-9]{6,9}$",
            "driver_license": r"^[A-Z0-9]{8,12}$",
            "national_id": r"^[0-9]{9,12}$",
            "ssn": r"^[0-9]{3}-[0-9]{2}-[0-9]{4}$"
        }
        
        pattern = patterns.get(doc_type.lower())
        if pattern:
            return bool(re.match(pattern, doc_number.upper().replace(" ", "")))
            
        return True  # Default to valid for unknown types
        
    def _validate_checksum(self, doc_type: str, doc_number: str) -> bool:
        # Simplified checksum validation
        # In real implementation, would use proper algorithms for each document type
        if not doc_number or len(doc_number) < 3:
            return False
            
        # Basic Luhn algorithm for numeric documents
        if doc_type.lower() in ["national_id", "ssn"] and doc_number.replace("-", "").isdigit():
            digits = [int(d) for d in doc_number.replace("-", "")]
            checksum = sum(digits[::2]) + sum((d*2 if d*2 < 10 else d*2-9) for d in digits[1::2])
            return checksum % 10 == 0
            
        return True  # Default to valid
        
    def _verify_minimum_age(self, birthdate: str, minimum_age: int) -> bool:
        try:
            birth_date = datetime.fromisoformat(birthdate.replace('Z', '+00:00'))
            today = datetime.now()
            age = (today - birth_date.replace(tzinfo=None)).days / 365.25
            return age >= minimum_age
        except Exception:
            return False
            
    def _categorize_risk(self, risk_score: float) -> str:
        if risk_score >= 0.8:
            return "HIGH"
        elif risk_score >= 0.5:
            return "MEDIUM"
        elif risk_score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"
            
    def _generate_verification_recommendations(self, kyc_result: Dict[str, Any]) -> List[str]:
        match_score = kyc_result.get("matchScore", 0.0)
        
        if match_score < 0.3:
            return [
                "REJECT: Identity verification failed",
                "Request alternative identification documents",
                "Consider manual verification process",
                "Flag account for enhanced monitoring"
            ]
        elif match_score < 0.6:
            return [
                "Request additional verification documents",
                "Perform secondary identity checks",
                "Limit account privileges until full verification",
                "Monitor for suspicious activities"
            ]
        elif match_score < 0.8:
            return [
                "Consider requesting supplementary documentation",
                "Apply standard monitoring procedures",
                "Document verification attempt for audit trail"
            ]
        else:
            return [
                "APPROVE: Identity successfully verified",
                "Proceed with normal account provisioning",
                "Maintain standard monitoring protocols"
            ]
            
    def _generate_document_recommendations(self, validations: List[Dict[str, Any]]) -> List[str]:
        invalid_docs = [v for v in validations if not v.get("format_valid", False)]
        
        if invalid_docs:
            return [
                "Request corrected or alternative documents",
                "Verify document authenticity through additional channels",
                "Consider manual review of questionable documents"
            ]
        else:
            return [
                "Document formats are valid",
                "Proceed with identity verification process"
            ]
            
    def _generate_compliance_recommendations(self, compliance_results: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        failed_checks = compliance_results.get("failed_checks", [])
        warnings = compliance_results.get("warnings", [])
        
        if "identity_verification_missing" in failed_checks:
            recommendations.append("Complete identity verification process immediately")
            
        if "document_validation_missing" in failed_checks:
            recommendations.append("Validate customer identification documents")
            
        if "age_verification_failed" in failed_checks:
            recommendations.append("Customer does not meet minimum age requirements")
            
        if warnings:
            recommendations.append("Address warning items for full compliance")
            
        if compliance_results.get("compliance_status") == "compliant":
            recommendations.append("Customer meets all compliance requirements")
            
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
                "identity_verification",
                "document_validation",
                "compliance_check"
            ]
        }