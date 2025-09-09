from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
import json
import httpx


class AgentStatus(Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class BaseAgent(ABC):
    """
    Base class for all specialized agents
    Provides common functionality for agent registration, health monitoring,
    and communication with the MCP resource registry
    """
    
    def __init__(self, agent_id: str, name: str, description: str, 
                 capabilities: List[str], endpoint_url: str = None):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.endpoint_url = endpoint_url or f"http://localhost:8000/agents/{agent_id}"
        
        # Status and monitoring
        self.status = AgentStatus.INITIALIZING
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.created_at = datetime.utcnow()
        self.last_heartbeat = None
        
        # Performance metrics
        self.metrics = {
            "requests_processed": 0,
            "success_count": 0,
            "error_count": 0,
            "avg_response_time_ms": 0,
            "last_request_time": None,
            "uptime_seconds": 0
        }
        
        # Configuration
        self.config = {}
        self.error_handlers: Dict[str, Callable] = {}
        
        # Communication settings
        self.registry_url = "http://localhost:8000"
        self.http_client = None
        
        self.logger.info(f"Initialized agent {self.agent_id} ({self.name})")
    
    async def initialize(self) -> bool:
        """Initialize the agent and register with MCP registry"""
        try:
            # Initialize HTTP client
            self.http_client = httpx.AsyncClient(timeout=30.0)
            
            # Perform agent-specific initialization
            await self._initialize_agent()
            
            # Register with MCP resource registry
            await self._register_with_registry()
            
            # Start heartbeat
            asyncio.create_task(self._heartbeat_loop())
            
            self.status = AgentStatus.READY
            self.logger.info(f"Agent {self.agent_id} initialized successfully")
            return True
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Failed to initialize agent {self.agent_id}: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent"""
        self.status = AgentStatus.SHUTDOWN
        self.logger.info(f"Shutting down agent {self.agent_id}")
        
        try:
            # Unregister from registry
            await self._unregister_from_registry()
            
            # Close HTTP client
            if self.http_client:
                await self.http_client.aclose()
            
            # Agent-specific cleanup
            await self._cleanup_agent()
            
        except Exception as e:
            self.logger.error(f"Error during agent shutdown: {e}")
    
    @abstractmethod
    async def _initialize_agent(self) -> None:
        """Agent-specific initialization logic"""
        pass
    
    @abstractmethod
    async def _cleanup_agent(self) -> None:
        """Agent-specific cleanup logic"""
        pass
    
    @abstractmethod
    async def execute_capability(self, capability_type: str, 
                               input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific capability"""
        pass
    
    async def process_request(self, capability_type: str, 
                            input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming request
        Handles common processing logic, metrics, and error handling
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.logger.info(f"Processing request {request_id} for capability {capability_type}")
        
        try:
            # Validate capability
            if capability_type not in self.capabilities:
                raise ValueError(f"Capability {capability_type} not supported by this agent")
            
            # Update status
            self.status = AgentStatus.PROCESSING
            
            # Execute the capability
            result = await self.execute_capability(capability_type, input_data)
            
            # Calculate metrics
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update metrics
            await self._update_metrics(processing_time_ms, success=True)
            
            # Prepare response
            response = {
                "request_id": request_id,
                "agent_id": self.agent_id,
                "capability_type": capability_type,
                "status": "success",
                "result": result,
                "processing_time_ms": processing_time_ms,
                "timestamp": end_time.isoformat(),
                "metadata": {
                    "agent_name": self.name,
                    "version": "1.0.0",
                    "confidence": result.get("confidence", 0.8)
                }
            }
            
            self.status = AgentStatus.READY
            self.logger.info(f"Request {request_id} completed successfully in {processing_time_ms}ms")
            
            return response
            
        except Exception as e:
            # Handle errors
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            await self._update_metrics(processing_time_ms, success=False)
            
            error_response = {
                "request_id": request_id,
                "agent_id": self.agent_id,
                "capability_type": capability_type,
                "status": "error",
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "code": getattr(e, 'code', 'AGENT_ERROR')
                },
                "processing_time_ms": processing_time_ms,
                "timestamp": end_time.isoformat()
            }
            
            self.status = AgentStatus.READY
            self.logger.error(f"Request {request_id} failed: {e}")
            
            return error_response
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status"""
        uptime = (datetime.utcnow() - self.created_at).total_seconds()
        
        health_data = {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "capabilities": self.capabilities,
            "metrics": self.metrics.copy(),
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "endpoint_url": self.endpoint_url,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add agent-specific health information
        try:
            agent_health = await self._get_agent_health()
            health_data.update(agent_health)
        except Exception as e:
            health_data["health_check_error"] = str(e)
        
        return health_data
    
    async def _get_agent_health(self) -> Dict[str, Any]:
        """Agent-specific health check information"""
        return {}
    
    async def _update_metrics(self, processing_time_ms: int, success: bool = True) -> None:
        """Update agent performance metrics"""
        self.metrics["requests_processed"] += 1
        self.metrics["last_request_time"] = datetime.utcnow().isoformat()
        
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["error_count"] += 1
        
        # Update average response time
        current_avg = self.metrics["avg_response_time_ms"]
        total_requests = self.metrics["requests_processed"]
        
        if total_requests == 1:
            self.metrics["avg_response_time_ms"] = processing_time_ms
        else:
            # Calculate running average
            self.metrics["avg_response_time_ms"] = int(
                (current_avg * (total_requests - 1) + processing_time_ms) / total_requests
            )
        
        # Update uptime
        self.metrics["uptime_seconds"] = int((datetime.utcnow() - self.created_at).total_seconds())
    
    async def _register_with_registry(self) -> None:
        """Register this agent with the MCP resource registry"""
        registration_data = {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": [
                {
                    "capability_type": cap,
                    "confidence_level": 0.85,
                    "response_time_sla": 5000,
                    "data_requirements": [],
                    "output_format": "json"
                }
                for cap in self.capabilities
            ],
            "status": "available",
            "endpoint_url": self.endpoint_url,
            "metadata": {
                "version": "1.0.0",
                "created_at": self.created_at.isoformat()
            }
        }
        
        try:
            if self.http_client:
                response = await self.http_client.post(
                    f"{self.registry_url}/mcp/agents/register",
                    json=registration_data
                )
                response.raise_for_status()
                self.logger.info(f"Successfully registered agent {self.agent_id} with registry")
        except Exception as e:
            self.logger.warning(f"Failed to register with registry: {e}")
    
    async def _unregister_from_registry(self) -> None:
        """Unregister from the MCP resource registry"""
        try:
            if self.http_client:
                response = await self.http_client.delete(
                    f"{self.registry_url}/mcp/agents/{self.agent_id}"
                )
                response.raise_for_status()
                self.logger.info(f"Successfully unregistered agent {self.agent_id}")
        except Exception as e:
            self.logger.warning(f"Failed to unregister from registry: {e}")
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to the registry"""
        while self.status != AgentStatus.SHUTDOWN:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(10)  # Retry after 10 seconds on error
    
    async def _send_heartbeat(self) -> None:
        """Send heartbeat with current metrics"""
        self.last_heartbeat = datetime.utcnow()
        
        heartbeat_data = {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "metrics": self.metrics,
            "timestamp": self.last_heartbeat.isoformat()
        }
        
        try:
            if self.http_client and self.status != AgentStatus.SHUTDOWN:
                response = await self.http_client.post(
                    f"{self.registry_url}/mcp/agents/{self.agent_id}/heartbeat",
                    json=heartbeat_data
                )
                # Don't raise for status on heartbeat failures to avoid disrupting the loop
        except Exception as e:
            self.logger.debug(f"Heartbeat failed: {e}")
    
    def add_error_handler(self, error_type: str, handler: Callable) -> None:
        """Add custom error handler for specific error types"""
        self.error_handlers[error_type] = handler
    
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """Update agent configuration"""
        self.config.update(config_updates)
        self.logger.info(f"Updated configuration for agent {self.agent_id}")
    
    def get_capability_info(self, capability_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific capability"""
        if capability_type not in self.capabilities:
            return None
        
        return {
            "capability_type": capability_type,
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "description": f"{capability_type} capability provided by {self.name}",
            "confidence_level": 0.85,
            "response_time_sla": 5000,
            "data_requirements": [],
            "output_format": "json",
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    
    async def validate_input(self, input_data: Dict[str, Any], 
                           required_fields: List[str]) -> None:
        """Validate input data for required fields"""
        missing_fields = []
        for field in required_fields:
            if field not in input_data:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def __str__(self) -> str:
        return f"Agent({self.agent_id}, {self.name}, {self.status.value})"
    
    def __repr__(self) -> str:
        return (f"BaseAgent(agent_id='{self.agent_id}', name='{self.name}', "
                f"status='{self.status.value}', capabilities={self.capabilities})")