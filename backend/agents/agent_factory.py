from typing import Dict, List, Optional
import asyncio
import logging
from .base.base_agent import BaseAgent
from .specialized import (
    FraudDetectionAgent,
    SimSwapAgent,
    KYCMatchAgent,
    DeviceLocationAgent,
    ScamSignalAgent
)


class AgentFactory:
    """
    Factory class for creating and managing specialized agents
    Provides centralized agent instantiation and lifecycle management
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agent_registry: Dict[str, BaseAgent] = {}
        self.agent_classes = {
            "fraud_detection": FraudDetectionAgent,
            "sim_swap": SimSwapAgent,
            "kyc_match": KYCMatchAgent,
            "device_location": DeviceLocationAgent,
            "scam_signal": ScamSignalAgent
        }
        
    async def create_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Create and initialize a new agent instance"""
        if agent_type not in self.agent_classes:
            self.logger.error(f"Unknown agent type: {agent_type}")
            return None
            
        try:
            agent_class = self.agent_classes[agent_type]
            agent = agent_class()
            
            # Initialize the agent
            success = await agent.initialize()
            if not success:
                self.logger.error(f"Failed to initialize {agent_type} agent")
                return None
                
            # Register the agent
            self.agent_registry[agent.agent_id] = agent
            self.logger.info(f"Created and registered {agent_type} agent: {agent.agent_id}")
            
            return agent
            
        except Exception as e:
            self.logger.error(f"Error creating {agent_type} agent: {e}")
            return None
            
    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an existing agent by ID"""
        return self.agent_registry.get(agent_id)
        
    async def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Get all agents that support a specific capability"""
        matching_agents = []
        for agent in self.agent_registry.values():
            if capability in agent.capabilities:
                matching_agents.append(agent)
        return matching_agents
        
    async def create_all_agents(self) -> Dict[str, BaseAgent]:
        """Create instances of all available agent types"""
        created_agents = {}
        
        for agent_type in self.agent_classes.keys():
            agent = await self.create_agent(agent_type)
            if agent:
                created_agents[agent_type] = agent
                
        self.logger.info(f"Created {len(created_agents)} agents: {list(created_agents.keys())}")
        return created_agents
        
    async def shutdown_agent(self, agent_id: str) -> bool:
        """Shutdown and remove a specific agent"""
        agent = self.agent_registry.get(agent_id)
        if not agent:
            self.logger.warning(f"Agent {agent_id} not found for shutdown")
            return False
            
        try:
            await agent.shutdown()
            del self.agent_registry[agent_id]
            self.logger.info(f"Successfully shutdown agent {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error shutting down agent {agent_id}: {e}")
            return False
            
    async def shutdown_all_agents(self) -> None:
        """Shutdown all registered agents"""
        agent_ids = list(self.agent_registry.keys())
        
        for agent_id in agent_ids:
            await self.shutdown_agent(agent_id)
            
        self.logger.info("All agents shutdown")
        
    def list_available_agent_types(self) -> List[str]:
        """Get list of all available agent types"""
        return list(self.agent_classes.keys())
        
    def get_agent_info(self, agent_type: str) -> Optional[Dict[str, any]]:
        """Get information about an agent type"""
        if agent_type not in self.agent_classes:
            return None
            
        agent_class = self.agent_classes[agent_type]
        
        # Create temporary instance to get metadata (without initialization)
        temp_agent = agent_class()
        
        return {
            "agent_type": agent_type,
            "agent_id": temp_agent.agent_id,
            "name": temp_agent.name,
            "description": temp_agent.description,
            "capabilities": temp_agent.capabilities,
            "endpoint_url": temp_agent.endpoint_url
        }
        
    def get_all_agent_info(self) -> Dict[str, Dict[str, any]]:
        """Get information about all available agent types"""
        agent_info = {}
        
        for agent_type in self.agent_classes.keys():
            info = self.get_agent_info(agent_type)
            if info:
                agent_info[agent_type] = info
                
        return agent_info
        
    async def health_check_all(self) -> Dict[str, Dict[str, any]]:
        """Perform health check on all registered agents"""
        health_results = {}
        
        for agent_id, agent in self.agent_registry.items():
            try:
                health_data = await agent.health_check()
                health_results[agent_id] = health_data
            except Exception as e:
                health_results[agent_id] = {
                    "agent_id": agent_id,
                    "status": "error",
                    "error": str(e)
                }
                
        return health_results
        
    def get_registry_status(self) -> Dict[str, any]:
        """Get current status of the agent registry"""
        return {
            "total_agents": len(self.agent_registry),
            "agent_ids": list(self.agent_registry.keys()),
            "available_types": self.list_available_agent_types(),
            "agents_by_type": {
                agent_type: [
                    agent.agent_id for agent in self.agent_registry.values()
                    if agent.__class__.__name__.lower().replace('agent', '') == agent_type.replace('_', '')
                ]
                for agent_type in self.agent_classes.keys()
            }
        }


# Global agent factory instance
agent_factory = AgentFactory()