from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import json


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """Result from an agent execution"""
    agent_id: str
    capability_type: str
    status: StepStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass 
class WorkflowStep:
    """Represents a single step in the workflow"""
    step_id: str
    name: str
    description: str
    agent_id: Optional[str] = None
    capability_type: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[AgentResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


class WorkflowState:
    """
    Comprehensive workflow state management for LangGraph orchestration
    Tracks execution progress, agent results, and decision points
    """
    
    def __init__(self, workflow_id: str, intent_id: str, intent_type: str):
        self.workflow_id = workflow_id
        self.intent_id = intent_id
        self.intent_type = intent_type
        
        # Workflow metadata
        self.status = WorkflowStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.updated_at = datetime.utcnow()
        
        # Execution state
        self.steps: Dict[str, WorkflowStep] = {}
        self.step_order: List[str] = []
        self.current_step: Optional[str] = None
        
        # Context and data
        self.context: Dict[str, Any] = {}
        self.input_data: Dict[str, Any] = {}
        self.output_data: Dict[str, Any] = {}
        self.intermediate_results: Dict[str, Any] = {}
        
        # Agent management
        self.selected_agents: Dict[str, str] = {}  # capability_type -> agent_id
        self.agent_results: Dict[str, AgentResult] = {}
        
        # Decision tracking
        self.decisions_made: List[Dict[str, Any]] = []
        self.risk_score: float = 0.0
        self.confidence_scores: Dict[str, float] = {}
        
        # Error handling
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Performance metrics
        self.execution_metrics: Dict[str, Any] = {
            'total_execution_time': 0,
            'agent_call_count': 0,
            'parallel_executions': 0,
            'retry_count': 0
        }
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow"""
        self.steps[step.step_id] = step
        if step.step_id not in self.step_order:
            self.step_order.append(step.step_id)
        self._update_timestamp()
    
    def start_workflow(self) -> None:
        """Mark workflow as started"""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.utcnow()
        self._update_timestamp()
    
    def complete_workflow(self, final_result: Optional[Dict[str, Any]] = None) -> None:
        """Mark workflow as completed"""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if final_result:
            self.output_data.update(final_result)
        
        # Calculate final metrics
        if self.started_at:
            execution_time = (self.completed_at - self.started_at).total_seconds() * 1000
            self.execution_metrics['total_execution_time'] = execution_time
        
        self._update_timestamp()
    
    def fail_workflow(self, error: str) -> None:
        """Mark workflow as failed"""
        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.errors.append(f"Workflow failed: {error}")
        self._update_timestamp()
    
    def start_step(self, step_id: str) -> bool:
        """Start execution of a specific step"""
        if step_id not in self.steps:
            return False
        
        step = self.steps[step_id]
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()
        self.current_step = step_id
        self._update_timestamp()
        return True
    
    def complete_step(self, step_id: str, result: AgentResult) -> bool:
        """Complete a step with results"""
        if step_id not in self.steps:
            return False
        
        step = self.steps[step_id]
        step.status = StepStatus.COMPLETED
        step.completed_at = datetime.utcnow()
        step.result = result
        
        # Store result by agent ID
        self.agent_results[result.agent_id] = result
        
        # Update intermediate results
        self.intermediate_results[step_id] = result.result
        
        # Update metrics
        self.execution_metrics['agent_call_count'] += 1
        
        self._update_timestamp()
        return True
    
    def fail_step(self, step_id: str, error: str, should_retry: bool = True) -> bool:
        """Mark a step as failed"""
        if step_id not in self.steps:
            return False
        
        step = self.steps[step_id]
        step.retry_count += 1
        
        if should_retry and step.retry_count <= step.max_retries:
            # Reset for retry
            step.status = StepStatus.PENDING
            step.started_at = None
            self.execution_metrics['retry_count'] += 1
            self.warnings.append(f"Retrying step {step_id} (attempt {step.retry_count})")
        else:
            # Mark as permanently failed
            step.status = StepStatus.FAILED
            step.completed_at = datetime.utcnow()
            self.errors.append(f"Step {step_id} failed: {error}")
        
        self._update_timestamp()
        return True
    
    def get_next_steps(self) -> List[str]:
        """Get list of steps that are ready to execute"""
        ready_steps = []
        
        for step_id in self.step_order:
            step = self.steps[step_id]
            
            if step.status != StepStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            dependencies_met = all(
                self.steps[dep_id].status == StepStatus.COMPLETED
                for dep_id in step.dependencies
                if dep_id in self.steps
            )
            
            if dependencies_met:
                ready_steps.append(step_id)
        
        return ready_steps
    
    def get_parallel_steps(self) -> List[List[str]]:
        """Get groups of steps that can run in parallel"""
        ready_steps = self.get_next_steps()
        
        # Group by dependency level
        parallel_groups = []
        remaining_steps = ready_steps.copy()
        
        while remaining_steps:
            current_group = []
            
            for step_id in remaining_steps.copy():
                step = self.steps[step_id]
                
                # Check if any dependencies are in remaining steps
                has_pending_deps = any(
                    dep_id in remaining_steps for dep_id in step.dependencies
                )
                
                if not has_pending_deps:
                    current_group.append(step_id)
                    remaining_steps.remove(step_id)
            
            if current_group:
                parallel_groups.append(current_group)
            else:
                # Break infinite loop if no progress
                break
        
        return parallel_groups
    
    def update_context(self, key: str, value: Any) -> None:
        """Update workflow context"""
        self.context[key] = value
        self._update_timestamp()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from workflow context"""
        return self.context.get(key, default)
    
    def add_decision(self, decision_point: str, decision: str, 
                    reasoning: str, confidence: float = 1.0) -> None:
        """Record a decision made during workflow execution"""
        decision_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'decision_point': decision_point,
            'decision': decision,
            'reasoning': reasoning,
            'confidence': confidence
        }
        self.decisions_made.append(decision_record)
        self._update_timestamp()
    
    def calculate_overall_confidence(self) -> float:
        """Calculate overall confidence based on agent results"""
        if not self.agent_results:
            return 0.0
        
        confidences = [result.confidence for result in self.agent_results.values()]
        return sum(confidences) / len(confidences)
    
    def get_aggregated_results(self) -> Dict[str, Any]:
        """Get aggregated results from all completed steps"""
        aggregated = {
            'workflow_id': self.workflow_id,
            'intent_id': self.intent_id,
            'status': self.status.value,
            'overall_confidence': self.calculate_overall_confidence(),
            'risk_score': self.risk_score,
            'execution_time_ms': self.execution_metrics.get('total_execution_time', 0),
            'steps_completed': len([s for s in self.steps.values() if s.status == StepStatus.COMPLETED]),
            'steps_failed': len([s for s in self.steps.values() if s.status == StepStatus.FAILED]),
            'agent_results': {},
            'decisions': self.decisions_made,
            'final_recommendation': None
        }
        
        # Add agent results
        for agent_id, result in self.agent_results.items():
            aggregated['agent_results'][agent_id] = {
                'capability': result.capability_type,
                'confidence': result.confidence,
                'result': result.result,
                'execution_time': result.execution_time_ms
            }
        
        # Generate final recommendation based on intent type
        aggregated['final_recommendation'] = self._generate_final_recommendation()
        
        return aggregated
    
    def _generate_final_recommendation(self) -> Dict[str, Any]:
        """Generate final recommendation based on workflow results"""
        if self.intent_type == 'fraud_detection':
            return self._generate_fraud_recommendation()
        elif self.intent_type == 'customer_verification':
            return self._generate_verification_recommendation()
        else:
            return {'action': 'review_results', 'priority': 'medium'}
    
    def _generate_fraud_recommendation(self) -> Dict[str, Any]:
        """Generate fraud detection recommendation"""
        if self.risk_score > 0.8:
            return {
                'action': 'block_transaction',
                'priority': 'high',
                'reasoning': 'High fraud risk detected',
                'confidence': self.calculate_overall_confidence()
            }
        elif self.risk_score > 0.6:
            return {
                'action': 'manual_review',
                'priority': 'medium',
                'reasoning': 'Moderate fraud risk - requires review',
                'confidence': self.calculate_overall_confidence()
            }
        else:
            return {
                'action': 'allow_transaction',
                'priority': 'low',
                'reasoning': 'Low fraud risk',
                'confidence': self.calculate_overall_confidence()
            }
    
    def _generate_verification_recommendation(self) -> Dict[str, Any]:
        """Generate customer verification recommendation"""
        overall_confidence = self.calculate_overall_confidence()
        
        if overall_confidence > 0.9:
            return {
                'action': 'approve_verification',
                'priority': 'low',
                'reasoning': 'High confidence verification',
                'confidence': overall_confidence
            }
        elif overall_confidence > 0.7:
            return {
                'action': 'request_additional_documents',
                'priority': 'medium', 
                'reasoning': 'Moderate confidence - need more verification',
                'confidence': overall_confidence
            }
        else:
            return {
                'action': 'reject_verification',
                'priority': 'high',
                'reasoning': 'Low confidence verification',
                'confidence': overall_confidence
            }
    
    def _update_timestamp(self) -> None:
        """Update the last modified timestamp"""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow state to dictionary for serialization"""
        return {
            'workflow_id': self.workflow_id,
            'intent_id': self.intent_id,
            'intent_type': self.intent_type,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat(),
            'current_step': self.current_step,
            'steps': {
                step_id: {
                    'step_id': step.step_id,
                    'name': step.name,
                    'status': step.status.value,
                    'agent_id': step.agent_id,
                    'started_at': step.started_at.isoformat() if step.started_at else None,
                    'completed_at': step.completed_at.isoformat() if step.completed_at else None,
                    'retry_count': step.retry_count
                }
                for step_id, step in self.steps.items()
            },
            'context': self.context,
            'risk_score': self.risk_score,
            'overall_confidence': self.calculate_overall_confidence(),
            'decisions_count': len(self.decisions_made),
            'errors': self.errors,
            'warnings': self.warnings,
            'metrics': self.execution_metrics
        }
    
    def is_complete(self) -> bool:
        """Check if workflow is complete"""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
    
    def can_continue(self) -> bool:
        """Check if workflow can continue execution"""
        return self.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]