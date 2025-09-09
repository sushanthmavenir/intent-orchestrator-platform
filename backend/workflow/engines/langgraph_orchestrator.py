from typing import Dict, List, Any, Optional, Callable, Tuple
import asyncio
import uuid
import logging
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .workflow_state import WorkflowState, WorkflowStep, AgentResult, StepStatus, WorkflowStatus
from ..templates.workflow_templates import WorkflowTemplateManager
from ...mcp.registry.resource_registry import ResourceRegistry, CapabilityType
from ...mcp.matchers.capability_matcher import CapabilityMatcher, CapabilityRequirement, MatchingStrategy


class LangGraphOrchestrator:
    """
    LangGraph-based workflow orchestration engine
    Manages complex multi-agent workflows with conditional routing and parallel execution
    """
    
    def __init__(self, resource_registry: ResourceRegistry):
        self.logger = logging.getLogger(__name__)
        self.resource_registry = resource_registry
        self.capability_matcher = CapabilityMatcher(resource_registry)
        self.template_manager = WorkflowTemplateManager()
        
        # Active workflows
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.workflow_graphs: Dict[str, StateGraph] = {}
        
        # Checkpointer for workflow state persistence
        self.checkpointer = MemorySaver()
        
        self.logger.info("LangGraph orchestrator initialized")
    
    async def create_workflow(self, intent_id: str, intent_type: str, 
                            input_data: Dict[str, Any], 
                            template_name: Optional[str] = None) -> str:
        """
        Create and initialize a new workflow
        
        Args:
            intent_id: TMF 921A intent ID
            intent_type: Type of intent (fraud_detection, etc.)
            input_data: Initial data for the workflow
            template_name: Optional specific template to use
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        
        # Initialize workflow state
        workflow_state = WorkflowState(workflow_id, intent_id, intent_type)
        workflow_state.input_data = input_data
        
        # Get workflow template
        if template_name:
            template = self.template_manager.get_template(template_name)
        else:
            template = self.template_manager.get_template_for_intent(intent_type)
        
        if not template:
            raise ValueError(f"No template found for intent type: {intent_type}")
        
        # Select agents based on template requirements
        await self._select_agents_for_workflow(workflow_state, template)
        
        # Build workflow graph
        graph = self._build_workflow_graph(workflow_state, template)
        
        # Store workflow
        self.active_workflows[workflow_id] = workflow_state
        self.workflow_graphs[workflow_id] = graph
        
        self.logger.info(f"Created workflow {workflow_id} for intent {intent_id}")
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute a workflow asynchronously
        
        Args:
            workflow_id: ID of the workflow to execute
            
        Returns:
            Workflow execution results
        """
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow_state = self.active_workflows[workflow_id]
        workflow_graph = self.workflow_graphs[workflow_id]
        
        try:
            # Start workflow execution
            workflow_state.start_workflow()
            
            # Execute the graph
            config = {"configurable": {"thread_id": workflow_id}}
            
            async for output in workflow_graph.astream(
                {"workflow_state": workflow_state},
                config=config
            ):
                # Process intermediate outputs
                self.logger.debug(f"Workflow {workflow_id} output: {output}")
                
                # Update workflow state based on output
                if "workflow_state" in output:
                    updated_state = output["workflow_state"]
                    if isinstance(updated_state, WorkflowState):
                        self.active_workflows[workflow_id] = updated_state
            
            # Get final results
            final_state = self.active_workflows[workflow_id]
            
            if final_state.status == WorkflowStatus.RUNNING:
                final_state.complete_workflow()
            
            results = final_state.get_aggregated_results()
            
            self.logger.info(f"Workflow {workflow_id} completed with status: {final_state.status}")
            return results
            
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            workflow_state.fail_workflow(str(e))
            return workflow_state.get_aggregated_results()
    
    async def _select_agents_for_workflow(self, workflow_state: WorkflowState, 
                                        template: Dict[str, Any]) -> None:
        """Select appropriate agents for workflow execution"""
        
        # Get requirements from template
        capability_requirements = []
        
        for step_config in template.get('steps', []):
            if 'capability_type' in step_config:
                capability_type = CapabilityType(step_config['capability_type'])
                
                requirement = CapabilityRequirement(
                    capability_type=capability_type,
                    min_confidence=step_config.get('min_confidence', 0.7),
                    max_response_time=step_config.get('max_response_time', 5000),
                    priority=step_config.get('priority', 2)
                )
                capability_requirements.append(requirement)
        
        # Find matching agents
        strategy = MatchingStrategy.BEST_PERFORMANCE
        matches = self.capability_matcher.find_best_agents(
            capability_requirements, strategy, max_agents=10
        )
        
        # Assign agents to workflow
        for match in matches:
            workflow_state.selected_agents[match.capability_type.value] = match.agent.agent_id
            
            # Create workflow step
            step = WorkflowStep(
                step_id=f"step_{match.capability_type.value}",
                name=f"{match.capability_type.value.replace('_', ' ').title()} Step",
                description=f"Execute {match.capability_type.value} using {match.agent.name}",
                agent_id=match.agent.agent_id,
                capability_type=match.capability_type.value
            )
            
            workflow_state.add_step(step)
        
        self.logger.info(f"Selected {len(matches)} agents for workflow {workflow_state.workflow_id}")
    
    def _build_workflow_graph(self, workflow_state: WorkflowState, 
                            template: Dict[str, Any]) -> StateGraph:
        """Build LangGraph workflow from template"""
        
        # Create state graph
        workflow = StateGraph(dict)
        
        # Add nodes based on template
        steps_config = template.get('steps', [])
        
        # Add start node
        workflow.add_node("start", self._start_node)
        
        # Add agent execution nodes
        for step_config in steps_config:
            step_id = step_config['step_id']
            node_func = self._create_agent_node(step_id, step_config)
            workflow.add_node(step_id, node_func)
        
        # Add decision nodes if specified
        for decision_config in template.get('decisions', []):
            decision_id = decision_config['decision_id']
            decision_func = self._create_decision_node(decision_id, decision_config)
            workflow.add_node(decision_id, decision_func)
        
        # Add aggregation node
        workflow.add_node("aggregate", self._aggregate_results_node)
        
        # Add end node
        workflow.add_node("end", self._end_node)
        
        # Set entry point
        workflow.set_entry_point("start")
        
        # Add edges based on template
        self._add_workflow_edges(workflow, template)
        
        # Compile the graph
        compiled_graph = workflow.compile(checkpointer=self.checkpointer)
        
        return compiled_graph
    
    def _add_workflow_edges(self, workflow: StateGraph, template: Dict[str, Any]) -> None:
        """Add edges to workflow graph based on template configuration"""
        
        # Get flow configuration
        flow_config = template.get('flow', {})
        
        if flow_config.get('type') == 'parallel':
            # Parallel execution flow
            workflow.add_edge("start", "aggregate")
            
            # All agent nodes run in parallel
            for step_config in template.get('steps', []):
                step_id = step_config['step_id']
                workflow.add_edge("start", step_id)
                workflow.add_edge(step_id, "aggregate")
        
        elif flow_config.get('type') == 'sequential':
            # Sequential execution flow
            steps = [step['step_id'] for step in template.get('steps', [])]
            
            # Chain steps sequentially
            workflow.add_edge("start", steps[0] if steps else "aggregate")
            
            for i in range(len(steps) - 1):
                workflow.add_edge(steps[i], steps[i + 1])
            
            if steps:
                workflow.add_edge(steps[-1], "aggregate")
        
        elif flow_config.get('type') == 'conditional':
            # Conditional flow with decision points
            workflow.add_conditional_edges(
                "start",
                self._routing_condition,
                {
                    "parallel": "aggregate",
                    "sequential": template.get('steps', [{}])[0].get('step_id', 'aggregate')
                }
            )
        
        # Always end at aggregation then end
        workflow.add_edge("aggregate", "end")
        workflow.add_edge("end", END)
    
    def _create_agent_node(self, step_id: str, step_config: Dict[str, Any]) -> Callable:
        """Create an agent execution node"""
        
        async def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
            workflow_state: WorkflowState = state["workflow_state"]
            
            # Start step execution
            workflow_state.start_step(step_id)
            
            try:
                # Get agent for this step
                capability_type = step_config.get('capability_type')
                agent_id = workflow_state.selected_agents.get(capability_type)
                
                if not agent_id:
                    raise ValueError(f"No agent selected for capability: {capability_type}")
                
                # Execute agent (mock execution for now)
                result = await self._execute_agent(agent_id, capability_type, workflow_state)
                
                # Complete step
                workflow_state.complete_step(step_id, result)
                
                self.logger.info(f"Completed step {step_id} with agent {agent_id}")
                
            except Exception as e:
                self.logger.error(f"Step {step_id} failed: {e}")
                workflow_state.fail_step(step_id, str(e))
            
            return {"workflow_state": workflow_state}
        
        return agent_node
    
    def _create_decision_node(self, decision_id: str, decision_config: Dict[str, Any]) -> Callable:
        """Create a decision node for conditional routing"""
        
        async def decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
            workflow_state: WorkflowState = state["workflow_state"]
            
            # Make decision based on current results
            decision = await self._make_decision(decision_config, workflow_state)
            
            # Record decision
            workflow_state.add_decision(
                decision_id,
                decision['choice'],
                decision['reasoning'],
                decision['confidence']
            )
            
            return {"workflow_state": workflow_state}
        
        return decision_node
    
    async def _execute_agent(self, agent_id: str, capability_type: str, 
                           workflow_state: WorkflowState) -> AgentResult:
        """Execute an agent (mock implementation)"""
        start_time = datetime.utcnow()
        
        agent = self.resource_registry.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found in registry: {agent_id}")

        # Prepare input data for the agent
        agent_input_data = {}
        if capability_type == "identity_verification":
            # Construct verification_data for KYCMatchAgent
            verification_data = {
                "given_name": workflow_state.input_data.get("given_name"),
                "family_name": workflow_state.input_data.get("family_name"),
                "name": workflow_state.input_data.get("full_name"), # Use full_name if available
                # Add other relevant fields if available in workflow_state.input_data
            }
            # Filter out empty values
            verification_data = {k: v for k, v in verification_data.items() if v}

            agent_input_data = {
                "phone_number": workflow_state.input_data.get("phone_number"),
                "verification_data": verification_data
            }
        else:
            # For other capabilities, pass the raw input data for now
            agent_input_data = workflow_state.input_data

        # Execute the agent's capability
        result_data = await agent.execute_capability(capability_type, agent_input_data)

        end_time = datetime.utcnow()
        actual_execution_time = int((end_time - start_time).total_seconds() * 1000)

        return AgentResult(
            agent_id=agent_id,
            capability_type=capability_type,
            status=StepStatus.COMPLETED,
            result=result_data,
            execution_time_ms=actual_execution_time,
            confidence=result_data.get("confidence", 0.9),
            timestamp=end_time
        )
    
    
    
    async def _make_decision(self, decision_config: Dict[str, Any], 
                           workflow_state: WorkflowState) -> Dict[str, Any]:
        """Make a decision based on current workflow state"""
        
        decision_type = decision_config.get('type', 'risk_threshold')
        
        if decision_type == 'risk_threshold':
            threshold = decision_config.get('threshold', 0.7)
            
            if workflow_state.risk_score > threshold:
                return {
                    'choice': 'high_risk_path',
                    'reasoning': f'Risk score {workflow_state.risk_score:.2f} exceeds threshold {threshold}',
                    'confidence': 0.9
                }
            else:
                return {
                    'choice': 'normal_path',
                    'reasoning': f'Risk score {workflow_state.risk_score:.2f} below threshold {threshold}',
                    'confidence': 0.8
                }
        
        # Default decision
        return {
            'choice': 'continue',
            'reasoning': 'No specific decision criteria met',
            'confidence': 0.5
        }
    
    async def _start_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow start node"""
        workflow_state: WorkflowState = state["workflow_state"]
        workflow_state.update_context("started_at", datetime.utcnow().isoformat())
        return {"workflow_state": workflow_state}
    
    async def _aggregate_results_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all agent executions"""
        workflow_state: WorkflowState = state["workflow_state"]
        
        # Calculate overall risk score
        if workflow_state.intent_type == 'fraud_detection':
            fraud_results = [
                result.result for result in workflow_state.agent_results.values()
                if result.capability_type == 'fraud_detection'
            ]
            
            if fraud_results:
                risk_scores = [r.get('risk_score', 0) for r in fraud_results]
                workflow_state.risk_score = max(risk_scores) if risk_scores else 0
        
        # Store aggregated data
        workflow_state.output_data['aggregated_at'] = datetime.utcnow().isoformat()
        workflow_state.output_data['total_agents'] = len(workflow_state.agent_results)
        
        return {"workflow_state": workflow_state}
    
    async def _end_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow end node"""
        workflow_state: WorkflowState = state["workflow_state"]
        workflow_state.update_context("ended_at", datetime.utcnow().isoformat())
        return {"workflow_state": workflow_state}
    
    def _routing_condition(self, state: Dict[str, Any]) -> str:
        """Determine routing based on workflow state"""
        workflow_state: WorkflowState = state["workflow_state"]
        
        # Simple routing logic based on intent type
        if workflow_state.intent_type == 'fraud_detection':
            return "parallel"  # Run fraud agents in parallel
        else:
            return "sequential"  # Sequential for other types
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        if workflow_id not in self.active_workflows:
            return None
        
        return self.active_workflows[workflow_id].to_dict()
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflows"""
        return [
            {
                'workflow_id': wf_id,
                'intent_id': wf.intent_id,
                'status': wf.status.value,
                'created_at': wf.created_at.isoformat(),
                'progress': len([s for s in wf.steps.values() if s.status == StepStatus.COMPLETED]) / len(wf.steps) if wf.steps else 0
            }
            for wf_id, wf in self.active_workflows.items()
        ]
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id not in self.active_workflows:
            return False
        
        workflow_state = self.active_workflows[workflow_id]
        workflow_state.status = WorkflowStatus.CANCELLED
        workflow_state.completed_at = datetime.utcnow()
        
        self.logger.info(f"Cancelled workflow {workflow_id}")
        return True