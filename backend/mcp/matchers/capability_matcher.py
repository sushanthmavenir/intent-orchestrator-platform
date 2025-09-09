from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..registry.resource_registry import ResourceRegistry, AgentResource, CapabilityType, AgentStatus


class MatchingStrategy(Enum):
    BEST_PERFORMANCE = "best_performance"
    FASTEST_RESPONSE = "fastest_response"
    LOWEST_COST = "lowest_cost"
    HIGHEST_CONFIDENCE = "highest_confidence"
    LOAD_BALANCED = "load_balanced"


@dataclass
class CapabilityRequirement:
    """Represents a requirement for a specific capability"""
    capability_type: CapabilityType
    min_confidence: float = 0.0
    max_response_time: Optional[int] = None  # milliseconds
    max_cost: Optional[float] = None
    required_data: Optional[List[str]] = None
    preferred_agents: Optional[List[str]] = None  # Preferred agent IDs
    excluded_agents: Optional[List[str]] = None   # Excluded agent IDs
    priority: int = 1  # Higher numbers = higher priority


@dataclass
class AgentMatch:
    """Represents a matched agent with scoring information"""
    agent: AgentResource
    capability_type: CapabilityType
    match_score: float
    confidence_score: float
    performance_score: float
    cost_score: float
    availability_score: float
    reasons: List[str]


class CapabilityMatcher:
    """
    Advanced capability matching system that selects the best agents
    based on requirements, performance, and availability
    """
    
    def __init__(self, resource_registry: ResourceRegistry):
        self.logger = logging.getLogger(__name__)
        self.registry = resource_registry
        
        # Scoring weights for different criteria
        self.scoring_weights = {
            'confidence': 0.3,
            'performance': 0.25,
            'cost': 0.2,
            'availability': 0.15,
            'preference': 0.1
        }
        
        self.logger.info("Capability matcher initialized")
    
    def find_best_agents(self, requirements: List[CapabilityRequirement],
                        strategy: MatchingStrategy = MatchingStrategy.BEST_PERFORMANCE,
                        max_agents: int = 5) -> List[AgentMatch]:
        """
        Find the best agents that match the given requirements
        
        Args:
            requirements: List of capability requirements
            strategy: Matching strategy to use
            max_agents: Maximum number of agents to return
            
        Returns:
            List of AgentMatch objects sorted by match score
        """
        self.logger.info(f"Finding agents with strategy: {strategy.value}")
        
        all_matches = []
        
        for requirement in requirements:
            matches = self._find_agents_for_requirement(requirement, strategy)
            all_matches.extend(matches)
        
        # Remove duplicates and sort by score
        unique_matches = self._deduplicate_matches(all_matches)
        sorted_matches = sorted(unique_matches, key=lambda m: m.match_score, reverse=True)
        
        # Apply strategy-specific filtering
        final_matches = self._apply_strategy_filtering(sorted_matches, strategy, max_agents)
        
        self.logger.info(f"Found {len(final_matches)} matching agents")
        return final_matches[:max_agents]
    
    def _find_agents_for_requirement(self, requirement: CapabilityRequirement,
                                   strategy: MatchingStrategy) -> List[AgentMatch]:
        """Find agents that match a specific requirement"""
        # Get candidates from registry
        candidates = self.registry.find_agents_by_capability(
            requirement.capability_type,
            {
                'min_confidence': requirement.min_confidence,
                'max_response_time': requirement.max_response_time,
                'max_cost': requirement.max_cost,
                'required_data': requirement.required_data or []
            }
        )
        
        # Filter out excluded agents
        if requirement.excluded_agents:
            candidates = [
                agent for agent in candidates 
                if agent.agent_id not in requirement.excluded_agents
            ]
        
        matches = []
        for agent in candidates:
            match = self._create_agent_match(agent, requirement, strategy)
            if match:
                matches.append(match)
        
        return matches
    
    def _create_agent_match(self, agent: AgentResource, 
                          requirement: CapabilityRequirement,
                          strategy: MatchingStrategy) -> Optional[AgentMatch]:
        """Create an AgentMatch with scoring"""
        
        # Find the relevant capability
        relevant_capability = None
        for capability in agent.capabilities:
            if capability.capability_type == requirement.capability_type:
                relevant_capability = capability
                break
        
        if not relevant_capability:
            return None
        
        # Calculate individual scores
        confidence_score = self._calculate_confidence_score(
            relevant_capability.confidence_level, requirement.min_confidence
        )
        
        performance_score = self._calculate_performance_score(
            agent, relevant_capability, requirement
        )
        
        cost_score = self._calculate_cost_score(
            relevant_capability.cost_per_request, requirement.max_cost
        )
        
        availability_score = self._calculate_availability_score(agent)
        
        preference_score = self._calculate_preference_score(
            agent.agent_id, requirement.preferred_agents
        )
        
        # Calculate overall match score
        match_score = (
            confidence_score * self.scoring_weights['confidence'] +
            performance_score * self.scoring_weights['performance'] +
            cost_score * self.scoring_weights['cost'] +
            availability_score * self.scoring_weights['availability'] +
            preference_score * self.scoring_weights['preference']
        )
        
        # Apply priority multiplier
        match_score *= (1 + (requirement.priority - 1) * 0.1)
        
        reasons = self._generate_match_reasons(
            agent, relevant_capability, requirement,
            confidence_score, performance_score, cost_score, availability_score
        )
        
        return AgentMatch(
            agent=agent,
            capability_type=requirement.capability_type,
            match_score=match_score,
            confidence_score=confidence_score,
            performance_score=performance_score,
            cost_score=cost_score,
            availability_score=availability_score,
            reasons=reasons
        )
    
    def _calculate_confidence_score(self, agent_confidence: float, 
                                  min_required: float) -> float:
        """Calculate confidence score (0.0 to 1.0)"""
        if agent_confidence < min_required:
            return 0.0
        
        # Normalize to 0-1 range, with higher confidence getting higher scores
        return min(agent_confidence / max(min_required, 0.1), 1.0)
    
    def _calculate_performance_score(self, agent: AgentResource,
                                   capability, requirement: CapabilityRequirement) -> float:
        """Calculate performance score based on metrics and SLA"""
        base_score = 0.5
        
        # Check response time SLA
        if requirement.max_response_time:
            if capability.response_time_sla <= requirement.max_response_time:
                # Better score for faster response times
                ratio = capability.response_time_sla / requirement.max_response_time
                base_score += (1 - ratio) * 0.3
            else:
                base_score -= 0.2  # Penalty for exceeding SLA
        
        # Factor in historical performance
        metrics = agent.performance_metrics
        success_rate = metrics.get('success_rate', 0.5)
        base_score += (success_rate - 0.5) * 0.3
        
        # Factor in average response time if available
        avg_response = metrics.get('avg_response_time')
        if avg_response and requirement.max_response_time:
            if avg_response <= requirement.max_response_time:
                base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_cost_score(self, agent_cost: float, max_cost: Optional[float]) -> float:
        """Calculate cost score (lower cost = higher score)"""
        if max_cost is None or max_cost <= 0:
            return 1.0  # Cost not a factor
        
        if agent_cost > max_cost:
            return 0.0  # Exceeds budget
        
        if agent_cost == 0:
            return 1.0  # Free is best
        
        # Invert cost ratio so lower cost gets higher score
        return max(0.0, 1.0 - (agent_cost / max_cost))
    
    def _calculate_availability_score(self, agent: AgentResource) -> float:
        """Calculate availability score based on status and load"""
        status_scores = {
            AgentStatus.AVAILABLE: 1.0,
            AgentStatus.BUSY: 0.6,
            AgentStatus.OFFLINE: 0.0,
            AgentStatus.ERROR: 0.1,
            AgentStatus.MAINTENANCE: 0.0
        }
        
        base_score = status_scores.get(agent.status, 0.0)
        
        # Factor in current load if available
        current_load = agent.performance_metrics.get('current_load', 0)
        if current_load > 0.8:  # High load
            base_score *= 0.7
        elif current_load > 0.5:  # Medium load
            base_score *= 0.85
        
        return base_score
    
    def _calculate_preference_score(self, agent_id: str, 
                                  preferred_agents: Optional[List[str]]) -> float:
        """Calculate preference score"""
        if not preferred_agents:
            return 0.5  # Neutral
        
        if agent_id in preferred_agents:
            # Higher score for earlier position in preference list
            index = preferred_agents.index(agent_id)
            return 1.0 - (index / len(preferred_agents) * 0.5)
        
        return 0.3  # Slight penalty for non-preferred agents
    
    def _generate_match_reasons(self, agent: AgentResource, capability,
                              requirement: CapabilityRequirement,
                              confidence_score: float, performance_score: float,
                              cost_score: float, availability_score: float) -> List[str]:
        """Generate human-readable reasons for the match"""
        reasons = []
        
        if confidence_score > 0.8:
            reasons.append(f"High confidence level ({capability.confidence_level:.2f})")
        elif confidence_score < 0.5:
            reasons.append(f"Low confidence level ({capability.confidence_level:.2f})")
        
        if performance_score > 0.8:
            reasons.append("Excellent performance metrics")
        elif performance_score < 0.5:
            reasons.append("Below average performance")
        
        if cost_score > 0.8:
            reasons.append("Cost-effective option")
        elif cost_score == 0:
            reasons.append("Exceeds cost budget")
        
        if availability_score == 1.0:
            reasons.append("Fully available")
        elif availability_score < 0.5:
            reasons.append("Limited availability")
        
        if agent.status == AgentStatus.BUSY:
            reasons.append("Currently busy but can handle request")
        
        success_rate = agent.performance_metrics.get('success_rate', 0)
        if success_rate > 0.95:
            reasons.append("Very high success rate")
        
        return reasons
    
    def _deduplicate_matches(self, matches: List[AgentMatch]) -> List[AgentMatch]:
        """Remove duplicate matches, keeping the best score for each agent"""
        agent_matches = {}
        
        for match in matches:
            agent_id = match.agent.agent_id
            if (agent_id not in agent_matches or 
                match.match_score > agent_matches[agent_id].match_score):
                agent_matches[agent_id] = match
        
        return list(agent_matches.values())
    
    def _apply_strategy_filtering(self, matches: List[AgentMatch],
                                strategy: MatchingStrategy,
                                max_agents: int) -> List[AgentMatch]:
        """Apply strategy-specific filtering and sorting"""
        
        if strategy == MatchingStrategy.FASTEST_RESPONSE:
            # Sort by performance score (which factors in response time)
            matches.sort(key=lambda m: m.performance_score, reverse=True)
        
        elif strategy == MatchingStrategy.LOWEST_COST:
            # Sort by cost score (higher score = lower cost)
            matches.sort(key=lambda m: m.cost_score, reverse=True)
        
        elif strategy == MatchingStrategy.HIGHEST_CONFIDENCE:
            # Sort by confidence score
            matches.sort(key=lambda m: m.confidence_score, reverse=True)
        
        elif strategy == MatchingStrategy.LOAD_BALANCED:
            # Prefer agents with lower current load
            available_matches = [m for m in matches if m.availability_score > 0.8]
            busy_matches = [m for m in matches if m.availability_score <= 0.8]
            
            # Return available agents first, then busy ones
            matches = available_matches + busy_matches
        
        # BEST_PERFORMANCE strategy uses the default match_score sorting
        
        return matches
    
    def get_capability_recommendations(self, intent_type: str, 
                                     entities: Dict[str, Any]) -> List[CapabilityRequirement]:
        """Generate capability requirements based on intent type and entities"""
        recommendations = []
        
        if intent_type == 'fraud_detection':
            recommendations.extend([
                CapabilityRequirement(
                    capability_type=CapabilityType.FRAUD_DETECTION,
                    min_confidence=0.8,
                    max_response_time=5000,
                    priority=3,
                    required_data=['customer_id']
                ),
                CapabilityRequirement(
                    capability_type=CapabilityType.RISK_SCORING,
                    min_confidence=0.7,
                    max_response_time=3000,
                    priority=2
                )
            ])
            
            # Add device verification if phone number available
            if entities.get('phone_numbers'):
                recommendations.append(
                    CapabilityRequirement(
                        capability_type=CapabilityType.DEVICE_VERIFICATION,
                        min_confidence=0.6,
                        max_response_time=4000,
                        priority=2,
                        required_data=['phone_number']
                    )
                )
        
        elif intent_type == 'customer_verification':
            recommendations.append(
                CapabilityRequirement(
                    capability_type=CapabilityType.KYC_VERIFICATION,
                    min_confidence=0.85,
                    max_response_time=8000,
                    priority=3,
                    required_data=['customer_id']
                )
            )
        
        elif intent_type == 'sim_swap_detection':
            recommendations.append(
                CapabilityRequirement(
                    capability_type=CapabilityType.SIM_SWAP_DETECTION,
                    min_confidence=0.75,
                    max_response_time=3000,
                    priority=3,
                    required_data=['phone_number']
                )
            )
        
        elif intent_type == 'device_location':
            recommendations.append(
                CapabilityRequirement(
                    capability_type=CapabilityType.LOCATION_TRACKING,
                    min_confidence=0.7,
                    max_response_time=4000,
                    priority=2,
                    required_data=['device_id']
                )
            )
        
        return recommendations
    
    def validate_agent_selection(self, matches: List[AgentMatch]) -> Dict[str, Any]:
        """Validate the selected agents and provide feedback"""
        validation = {
            'is_valid': True,
            'warnings': [],
            'suggestions': [],
            'coverage_analysis': {}
        }
        
        if not matches:
            validation['is_valid'] = False
            validation['warnings'].append("No agents found matching requirements")
            return validation
        
        # Check for low confidence matches
        low_confidence_matches = [m for m in matches if m.confidence_score < 0.6]
        if low_confidence_matches:
            validation['warnings'].append(
                f"{len(low_confidence_matches)} agents have low confidence scores"
            )
        
        # Check for high-cost selections
        high_cost_matches = [m for m in matches if m.cost_score < 0.3]
        if high_cost_matches:
            validation['suggestions'].append("Consider reviewing cost requirements")
        
        # Analyze capability coverage
        covered_capabilities = set(m.capability_type for m in matches)
        validation['coverage_analysis']['covered_capabilities'] = len(covered_capabilities)
        
        return validation