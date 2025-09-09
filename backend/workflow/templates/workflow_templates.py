from typing import Dict, List, Any, Optional
import yaml
from pathlib import Path
import logging


class WorkflowTemplateManager:
    """
    Manages workflow templates for different intent types
    Templates define the structure, flow, and requirements for workflow execution
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default workflow templates"""
        
        # Fraud Detection Template - Parallel execution for speed
        fraud_template = {
            'name': 'fraud_detection',
            'description': 'Comprehensive fraud detection workflow',
            'intent_types': ['fraud_detection'],
            'flow': {
                'type': 'parallel',
                'timeout_ms': 10000
            },
            'steps': [
                {
                    'step_id': 'fraud_analysis',
                    'name': 'Fraud Risk Analysis',
                    'capability_type': 'fraud_detection',
                    'required': True,
                    'min_confidence': 0.8,
                    'max_response_time': 3000,
                    'priority': 3
                },
                {
                    'step_id': 'device_verification',
                    'name': 'Device Verification',
                    'capability_type': 'device_verification',
                    'required': False,
                    'min_confidence': 0.6,
                    'max_response_time': 4000,
                    'priority': 2
                },
                {
                    'step_id': 'location_check',
                    'name': 'Location Verification',
                    'capability_type': 'location_tracking',
                    'required': False,
                    'min_confidence': 0.7,
                    'max_response_time': 3500,
                    'priority': 2
                },
                {
                    'step_id': 'sim_swap_check',
                    'name': 'SIM Swap Detection',
                    'capability_type': 'sim_swap_detection',
                    'required': False,
                    'min_confidence': 0.75,
                    'max_response_time': 2500,
                    'priority': 2
                },
                {
                    'step_id': 'risk_scoring',
                    'name': 'Risk Score Calculation',
                    'capability_type': 'risk_scoring',
                    'required': True,
                    'min_confidence': 0.7,
                    'max_response_time': 2000,
                    'priority': 3
                }
            ],
            'decisions': [
                {
                    'decision_id': 'risk_evaluation',
                    'type': 'risk_threshold',
                    'threshold': 0.7,
                    'conditions': {
                        'high_risk': {'min_risk_score': 0.8},
                        'medium_risk': {'min_risk_score': 0.5, 'max_risk_score': 0.8},
                        'low_risk': {'max_risk_score': 0.5}
                    }
                }
            ],
            'success_criteria': {
                'min_agents_completed': 2,
                'required_capabilities': ['fraud_detection']
            }
        }
        
        # Customer Verification Template - Sequential for thoroughness
        verification_template = {
            'name': 'customer_verification',
            'description': 'Customer identity verification workflow',
            'intent_types': ['customer_verification'],
            'flow': {
                'type': 'sequential',
                'timeout_ms': 15000
            },
            'steps': [
                {
                    'step_id': 'kyc_verification',
                    'name': 'KYC Document Verification',
                    'capability_type': 'kyc_verification',
                    'required': True,
                    'min_confidence': 0.85,
                    'max_response_time': 8000,
                    'priority': 3
                },
                {
                    'step_id': 'device_verification',
                    'name': 'Device Verification',
                    'capability_type': 'device_verification',
                    'required': True,
                    'min_confidence': 0.7,
                    'max_response_time': 4000,
                    'priority': 2,
                    'dependencies': ['kyc_verification']
                },
                {
                    'step_id': 'location_verification',
                    'name': 'Location Verification',
                    'capability_type': 'location_tracking',
                    'required': False,
                    'min_confidence': 0.6,
                    'max_response_time': 3000,
                    'priority': 1,
                    'dependencies': ['device_verification']
                }
            ],
            'decisions': [
                {
                    'decision_id': 'verification_quality',
                    'type': 'confidence_threshold',
                    'threshold': 0.8,
                    'conditions': {
                        'approved': {'min_confidence': 0.9},
                        'additional_docs_required': {'min_confidence': 0.7, 'max_confidence': 0.9},
                        'rejected': {'max_confidence': 0.7}
                    }
                }
            ],
            'success_criteria': {
                'min_agents_completed': 1,
                'required_capabilities': ['kyc_verification']
            }
        }
        
        # Transaction Monitoring Template - Hybrid flow
        transaction_template = {
            'name': 'transaction_monitoring',
            'description': 'Real-time transaction monitoring workflow',
            'intent_types': ['transaction_monitoring'],
            'flow': {
                'type': 'conditional',
                'timeout_ms': 8000
            },
            'steps': [
                {
                    'step_id': 'transaction_analysis',
                    'name': 'Transaction Pattern Analysis',
                    'capability_type': 'transaction_analysis',
                    'required': True,
                    'min_confidence': 0.7,
                    'max_response_time': 3000,
                    'priority': 3
                },
                {
                    'step_id': 'fraud_check',
                    'name': 'Fraud Detection Check',
                    'capability_type': 'fraud_detection',
                    'required': True,
                    'min_confidence': 0.75,
                    'max_response_time': 2500,
                    'priority': 3
                },
                {
                    'step_id': 'device_check',
                    'name': 'Device Authentication',
                    'capability_type': 'device_verification',
                    'required': False,
                    'min_confidence': 0.6,
                    'max_response_time': 2000,
                    'priority': 2
                }
            ],
            'decisions': [
                {
                    'decision_id': 'transaction_decision',
                    'type': 'risk_threshold',
                    'threshold': 0.6,
                    'conditions': {
                        'block': {'min_risk_score': 0.8},
                        'review': {'min_risk_score': 0.5, 'max_risk_score': 0.8},
                        'allow': {'max_risk_score': 0.5}
                    }
                }
            ],
            'success_criteria': {
                'min_agents_completed': 2,
                'required_capabilities': ['transaction_analysis', 'fraud_detection']
            }
        }
        
        # SIM Swap Detection Template - Fast parallel execution
        sim_swap_template = {
            'name': 'sim_swap_detection',
            'description': 'SIM swap fraud detection workflow',
            'intent_types': ['sim_swap_detection'],
            'flow': {
                'type': 'parallel',
                'timeout_ms': 6000
            },
            'steps': [
                {
                    'step_id': 'sim_swap_analysis',
                    'name': 'SIM Swap Detection',
                    'capability_type': 'sim_swap_detection',
                    'required': True,
                    'min_confidence': 0.8,
                    'max_response_time': 2500,
                    'priority': 3
                },
                {
                    'step_id': 'device_location',
                    'name': 'Device Location Check',
                    'capability_type': 'location_tracking',
                    'required': True,
                    'min_confidence': 0.7,
                    'max_response_time': 3000,
                    'priority': 2
                },
                {
                    'step_id': 'fraud_correlation',
                    'name': 'Fraud Correlation Analysis',
                    'capability_type': 'fraud_detection',
                    'required': False,
                    'min_confidence': 0.6,
                    'max_response_time': 2000,
                    'priority': 1
                }
            ],
            'success_criteria': {
                'min_agents_completed': 2,
                'required_capabilities': ['sim_swap_detection']
            }
        }
        
        # Service Assurance Template - Network monitoring
        service_assurance_template = {
            'name': 'service_assurance',
            'description': 'Network service quality assurance workflow',
            'intent_types': ['service_assurance'],
            'flow': {
                'type': 'sequential',
                'timeout_ms': 12000
            },
            'steps': [
                {
                    'step_id': 'network_analysis',
                    'name': 'Network Performance Analysis',
                    'capability_type': 'network_analysis',
                    'required': True,
                    'min_confidence': 0.7,
                    'max_response_time': 5000,
                    'priority': 3
                },
                {
                    'step_id': 'device_diagnostics',
                    'name': 'Device Diagnostics',
                    'capability_type': 'device_verification',
                    'required': False,
                    'min_confidence': 0.6,
                    'max_response_time': 3000,
                    'priority': 2,
                    'dependencies': ['network_analysis']
                },
                {
                    'step_id': 'location_correlation',
                    'name': 'Location-based Analysis',
                    'capability_type': 'location_tracking',
                    'required': False,
                    'min_confidence': 0.5,
                    'max_response_time': 2000,
                    'priority': 1,
                    'dependencies': ['network_analysis']
                }
            ],
            'success_criteria': {
                'min_agents_completed': 1,
                'required_capabilities': ['network_analysis']
            }
        }
        
        # Store templates
        self.templates = {
            'fraud_detection': fraud_template,
            'customer_verification': verification_template,
            'transaction_monitoring': transaction_template,
            'sim_swap_detection': sim_swap_template,
            'service_assurance': service_assurance_template
        }
        
        self.logger.info(f"Loaded {len(self.templates)} workflow templates")
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a workflow template by name"""
        return self.templates.get(template_name)
    
    def get_template_for_intent(self, intent_type: str) -> Optional[Dict[str, Any]]:
        """Get the best template for a specific intent type"""
        for template in self.templates.values():
            if intent_type in template.get('intent_types', []):
                return template
        
        # Return default template if no specific match
        return self.templates.get('fraud_detection')  # Default fallback
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        return [
            {
                'name': template['name'],
                'description': template['description'],
                'intent_types': template['intent_types'],
                'steps_count': len(template['steps']),
                'flow_type': template['flow']['type']
            }
            for template in self.templates.values()
        ]
    
    def validate_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a workflow template"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['name', 'description', 'flow', 'steps']
        for field in required_fields:
            if field not in template:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Validate flow configuration
        if 'flow' in template:
            flow = template['flow']
            if 'type' not in flow:
                validation_result['errors'].append("Flow type not specified")
                validation_result['is_valid'] = False
            elif flow['type'] not in ['parallel', 'sequential', 'conditional']:
                validation_result['errors'].append(f"Invalid flow type: {flow['type']}")
                validation_result['is_valid'] = False
        
        # Validate steps
        if 'steps' in template:
            steps = template['steps']
            if not steps:
                validation_result['warnings'].append("No steps defined in template")
            
            step_ids = set()
            for step in steps:
                # Check required step fields
                if 'step_id' not in step:
                    validation_result['errors'].append("Step missing step_id")
                    validation_result['is_valid'] = False
                else:
                    if step['step_id'] in step_ids:
                        validation_result['errors'].append(f"Duplicate step_id: {step['step_id']}")
                        validation_result['is_valid'] = False
                    step_ids.add(step['step_id'])
                
                if 'capability_type' not in step:
                    validation_result['errors'].append(f"Step {step.get('step_id')} missing capability_type")
                    validation_result['is_valid'] = False
                
                # Check dependencies
                if 'dependencies' in step:
                    for dep in step['dependencies']:
                        if dep not in step_ids:
                            validation_result['warnings'].append(f"Step {step.get('step_id')} depends on undefined step: {dep}")
        
        return validation_result
    
    def create_custom_template(self, template_data: Dict[str, Any]) -> bool:
        """Create a custom workflow template"""
        validation = self.validate_template(template_data)
        
        if not validation['is_valid']:
            self.logger.error(f"Invalid template: {validation['errors']}")
            return False
        
        template_name = template_data['name']
        self.templates[template_name] = template_data
        
        self.logger.info(f"Created custom template: {template_name}")
        return True
    
    def get_template_requirements(self, template_name: str) -> List[str]:
        """Get capability requirements for a template"""
        template = self.get_template(template_name)
        if not template:
            return []
        
        requirements = []
        for step in template.get('steps', []):
            capability = step.get('capability_type')
            if capability and capability not in requirements:
                requirements.append(capability)
        
        return requirements
    
    def get_estimated_execution_time(self, template_name: str) -> int:
        """Get estimated execution time for a template in milliseconds"""
        template = self.get_template(template_name)
        if not template:
            return 0
        
        flow_type = template['flow']['type']
        steps = template['steps']
        
        if flow_type == 'parallel':
            # Max response time among all steps
            max_time = max(step.get('max_response_time', 3000) for step in steps)
            return max_time + 1000  # Add overhead
        
        elif flow_type == 'sequential':
            # Sum of all response times
            total_time = sum(step.get('max_response_time', 3000) for step in steps)
            return total_time + len(steps) * 500  # Add overhead per step
        
        else:  # conditional
            # Average of parallel and sequential estimates
            max_time = max(step.get('max_response_time', 3000) for step in steps)
            total_time = sum(step.get('max_response_time', 3000) for step in steps)
            return (max_time + total_time) // 2 + len(steps) * 250
    
    def export_template(self, template_name: str) -> Optional[str]:
        """Export a template as YAML string"""
        template = self.get_template(template_name)
        if not template:
            return None
        
        return yaml.dump(template, default_flow_style=False, sort_keys=False)
    
    def import_template_from_yaml(self, yaml_content: str) -> bool:
        """Import a template from YAML content"""
        try:
            template_data = yaml.safe_load(yaml_content)
            return self.create_custom_template(template_data)
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Template import error: {e}")
            return False