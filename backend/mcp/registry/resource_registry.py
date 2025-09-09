from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import uuid
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass, asdict
import json


class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class CapabilityType(Enum):
    FRAUD_DETECTION = "fraud_detection"
    TRANSACTION_ANALYSIS = "transaction_analysis"
    DEVICE_VERIFICATION = "device_verification"
    LOCATION_TRACKING = "location_tracking"
    KYC_VERIFICATION = "kyc_verification"
    SIM_SWAP_DETECTION = "sim_swap_detection"
    SCAM_DETECTION = "scam_detection"
    NETWORK_ANALYSIS = "network_analysis"
    DATA_ENRICHMENT = "data_enrichment"
    RISK_SCORING = "risk_scoring"


@dataclass
class AgentCapability:
    """Represents a capability that an agent can provide"""
    capability_type: CapabilityType
    confidence_level: float  # 0.0 to 1.0
    response_time_sla: int  # milliseconds
    data_requirements: List[str]
    output_format: str
    cost_per_request: float = 0.0
    rate_limit: Optional[int] = None  # requests per minute


@dataclass
class AgentResource:
    """Represents an agent resource in the registry"""
    agent_id: str
    name: str
    description: str
    capabilities: List[AgentCapability]
    status: AgentStatus
    endpoint_url: str
    last_heartbeat: datetime
    performance_metrics: Dict[str, float]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert enums to strings
        result['status'] = self.status.value
        result['capabilities'] = [
            {
                **asdict(cap),
                'capability_type': cap.capability_type.value
            }
            for cap in self.capabilities
        ]
        # Convert datetime to ISO string
        result['last_heartbeat'] = self.last_heartbeat.isoformat()
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result


class ResourceRegistry:
    """
    MCP Resource Registry for managing agent capabilities and availability
    Provides discovery, health checking, and performance tracking
    """
    
    def __init__(self, heartbeat_timeout: int = 300):  # 5 minutes
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, AgentResource] = {}
        self.capability_index: Dict[CapabilityType, Set[str]] = {}
        self.heartbeat_timeout = heartbeat_timeout
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize capability index
        for capability_type in CapabilityType:
            self.capability_index[capability_type] = set()
        
        self.logger.info("Resource registry initialized")
    
    def register_agent(self, agent_resource: AgentResource) -> bool:
        """Register a new agent resource"""
        try:
            agent_id = agent_resource.agent_id
            
            # Update timestamps
            now = datetime.utcnow()
            agent_resource.created_at = now
            agent_resource.updated_at = now
            agent_resource.last_heartbeat = now
            
            # Store agent
            self.agents[agent_id] = agent_resource
            
            # Update capability index
            for capability in agent_resource.capabilities:
                self.capability_index[capability.capability_type].add(agent_id)
            
            # Initialize performance history
            self.performance_history[agent_id] = []
            
            self.logger.info(f"Registered agent: {agent_id} ({agent_resource.name})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_resource.agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry"""
        try:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            
            # Remove from capability index
            for capability in agent.capabilities:
                self.capability_index[capability.capability_type].discard(agent_id)
            
            # Clean up
            del self.agents[agent_id]
            self.performance_history.pop(agent_id, None)
            
            self.logger.info(f"Unregistered agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        if agent_id not in self.agents:
            return False
        
        self.agents[agent_id].status = status
        self.agents[agent_id].updated_at = datetime.utcnow()
        
        self.logger.debug(f"Updated agent {agent_id} status to {status.value}")
        return True
    
    def heartbeat(self, agent_id: str, performance_metrics: Optional[Dict[str, float]] = None) -> bool:
        """Process heartbeat from an agent"""
        if agent_id not in self.agents:
            self.logger.warning(f"Heartbeat from unregistered agent: {agent_id}")
            return False
        
        agent = self.agents[agent_id]
        agent.last_heartbeat = datetime.utcnow()
        
        # Update performance metrics if provided
        if performance_metrics:
            agent.performance_metrics.update(performance_metrics)
            
            # Store in history
            history_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': performance_metrics
            }
            
            agent_history = self.performance_history[agent_id]
            agent_history.append(history_entry)
            
            # Keep only last 100 entries
            if len(agent_history) > 100:
                self.performance_history[agent_id] = agent_history[-100:]
        
        # Update status to available if it was offline
        if agent.status == AgentStatus.OFFLINE:
            agent.status = AgentStatus.AVAILABLE
        
        return True
    
    def find_agents_by_capability(self, capability_type: CapabilityType, 
                                 requirements: Optional[Dict[str, Any]] = None) -> List[AgentResource]:
        """Find agents that have a specific capability"""
        agent_ids = self.capability_index.get(capability_type, set())
        matching_agents = []
        
        for agent_id in agent_ids:
            agent = self.agents.get(agent_id)
            if not agent or agent.status not in [AgentStatus.AVAILABLE, AgentStatus.BUSY]:
                continue
            
            # Check if agent has the capability with required parameters
            for capability in agent.capabilities:
                if capability.capability_type == capability_type:
                    if self._matches_requirements(capability, requirements):
                        matching_agents.append(agent)
                    break
        
        return matching_agents
    
    def _matches_requirements(self, capability: AgentCapability, 
                            requirements: Optional[Dict[str, Any]]) -> bool:
        """Check if a capability matches the requirements"""
        if not requirements:
            return True
        
        # Check confidence level requirement
        min_confidence = requirements.get('min_confidence', 0.0)
        if capability.confidence_level < min_confidence:
            return False
        
        # Check SLA requirement
        max_response_time = requirements.get('max_response_time')
        if max_response_time and capability.response_time_sla > max_response_time:
            return False
        
        # Check cost requirement
        max_cost = requirements.get('max_cost')
        if max_cost and capability.cost_per_request > max_cost:
            return False
        
        # Check data requirements
        required_data = requirements.get('required_data', [])
        if required_data and not all(req in capability.data_requirements for req in required_data):
            return False
        
        return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentResource]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self, status_filter: Optional[AgentStatus] = None) -> List[AgentResource]:
        """List all agents, optionally filtered by status"""
        agents = list(self.agents.values())
        
        if status_filter:
            agents = [agent for agent in agents if agent.status == status_filter]
        
        return agents
    
    def get_capability_summary(self) -> Dict[str, int]:
        """Get summary of available capabilities"""
        summary = {}
        for capability_type, agent_ids in self.capability_index.items():
            available_count = sum(
                1 for agent_id in agent_ids
                if self.agents[agent_id].status == AgentStatus.AVAILABLE
            )
            summary[capability_type.value] = available_count
        
        return summary
    
    def check_agent_health(self) -> Dict[str, Any]:
        """Check health status of all agents"""
        now = datetime.utcnow()
        timeout_threshold = now - timedelta(seconds=self.heartbeat_timeout)
        
        health_report = {
            'total_agents': len(self.agents),
            'healthy_agents': 0,
            'unhealthy_agents': 0,
            'offline_agents': 0,
            'agents': {}
        }
        
        for agent_id, agent in self.agents.items():
            is_healthy = agent.last_heartbeat > timeout_threshold
            
            if agent.status == AgentStatus.OFFLINE:
                health_report['offline_agents'] += 1
                status = 'offline'
            elif is_healthy:
                health_report['healthy_agents'] += 1
                status = 'healthy'
            else:
                health_report['unhealthy_agents'] += 1
                status = 'unhealthy'
                # Mark agent as offline if haven't heard from it
                agent.status = AgentStatus.OFFLINE
            
            health_report['agents'][agent_id] = {
                'name': agent.name,
                'status': status,
                'last_heartbeat': agent.last_heartbeat.isoformat(),
                'capabilities_count': len(agent.capabilities)
            }
        
        return health_report
    
    def get_performance_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for an agent"""
        if agent_id not in self.agents:
            return {}
        
        agent = self.agents[agent_id]
        history = self.performance_history.get(agent_id, [])
        
        # Calculate averages from recent history
        recent_metrics = {}
        if history:
            # Get last 10 entries
            recent_history = history[-10:]
            metric_keys = set()
            for entry in recent_history:
                metric_keys.update(entry['metrics'].keys())
            
            for key in metric_keys:
                values = [entry['metrics'].get(key, 0) for entry in recent_history if key in entry['metrics']]
                if values:
                    recent_metrics[f'avg_{key}'] = sum(values) / len(values)
        
        return {
            'agent_id': agent_id,
            'current_metrics': agent.performance_metrics,
            'recent_averages': recent_metrics,
            'history_entries': len(history),
            'last_updated': agent.updated_at.isoformat()
        }
    
    def export_registry_state(self) -> Dict[str, Any]:
        """Export the current state of the registry"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'agents': {
                agent_id: agent.to_dict()
                for agent_id, agent in self.agents.items()
            },
            'capability_summary': self.get_capability_summary(),
            'health_report': self.check_agent_health()
        }
    
    def create_mock_agents(self) -> None:
        """Create mock agents for development and testing"""
        mock_agents = [
            {
                'agent_id': 'fraud-detector-001',
                'name': 'Advanced Fraud Detection Agent',
                'description': 'AI-powered fraud detection with ML models',
                'endpoint_url': 'http://localhost:8001/fraud-detector',
                'capabilities': [
                    AgentCapability(
                        capability_type=CapabilityType.FRAUD_DETECTION,
                        confidence_level=0.95,
                        response_time_sla=2000,
                        data_requirements=['customer_id', 'transaction_data'],
                        output_format='json',
                        cost_per_request=0.05
                    ),
                    AgentCapability(
                        capability_type=CapabilityType.RISK_SCORING,
                        confidence_level=0.90,
                        response_time_sla=1500,
                        data_requirements=['customer_profile', 'transaction_history'],
                        output_format='json',
                        cost_per_request=0.03
                    )
                ]
            },
            {
                'agent_id': 'device-tracker-001',
                'name': 'Device Location Tracker',
                'description': 'CAMARA-compatible device location tracking',
                'endpoint_url': 'http://localhost:8002/device-tracker',
                'capabilities': [
                    AgentCapability(
                        capability_type=CapabilityType.LOCATION_TRACKING,
                        confidence_level=0.85,
                        response_time_sla=3000,
                        data_requirements=['device_id', 'phone_number'],
                        output_format='json',
                        cost_per_request=0.02
                    ),
                    AgentCapability(
                        capability_type=CapabilityType.DEVICE_VERIFICATION,
                        confidence_level=0.80,
                        response_time_sla=2500,
                        data_requirements=['device_id'],
                        output_format='json',
                        cost_per_request=0.01
                    )
                ]
            },
            {
                'agent_id': 'kyc-validator-001',
                'name': 'KYC Validation Service',
                'description': 'Identity verification and KYC compliance',
                'endpoint_url': 'http://localhost:8003/kyc-validator',
                'capabilities': [
                    AgentCapability(
                        capability_type=CapabilityType.KYC_VERIFICATION,
                        confidence_level=0.92,
                        response_time_sla=5000,
                        data_requirements=['customer_id', 'identity_documents'],
                        output_format='json',
                        cost_per_request=0.10
                    )
                ]
            },
            {
                'agent_id': 'sim-swap-detector-001',
                'name': 'SIM Swap Detection Agent',
                'description': 'Detects suspicious SIM card changes',
                'endpoint_url': 'http://localhost:8004/sim-swap-detector',
                'capabilities': [
                    AgentCapability(
                        capability_type=CapabilityType.SIM_SWAP_DETECTION,
                        confidence_level=0.88,
                        response_time_sla=2000,
                        data_requirements=['phone_number', 'customer_id'],
                        output_format='json',
                        cost_per_request=0.03
                    )
                ]
            },
            {
                'agent_id': 'scam-analyzer-001',
                'name': 'Scam Signal Analyzer',
                'description': 'Analyzes communication patterns for scam indicators',
                'endpoint_url': 'http://localhost:8005/scam-analyzer',
                'capabilities': [
                    AgentCapability(
                        capability_type=CapabilityType.SCAM_DETECTION,
                        confidence_level=0.87,
                        response_time_sla=3500,
                        data_requirements=['call_data', 'message_data'],
                        output_format='json',
                        cost_per_request=0.04
                    )
                ]
            }
        ]
        
        for mock_agent_data in mock_agents:
            agent = AgentResource(
                agent_id=mock_agent_data['agent_id'],
                name=mock_agent_data['name'],
                description=mock_agent_data['description'],
                capabilities=mock_agent_data['capabilities'],
                status=AgentStatus.AVAILABLE,
                endpoint_url=mock_agent_data['endpoint_url'],
                last_heartbeat=datetime.utcnow(),
                performance_metrics={
                    'success_rate': 0.95,
                    'avg_response_time': 2000,
                    'requests_processed': 100
                },
                metadata={'mock': True, 'version': '1.0'},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.register_agent(agent)
        
        self.logger.info(f"Created {len(mock_agents)} mock agents for development")