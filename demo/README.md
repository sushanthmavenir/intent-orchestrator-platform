# Intent Orchestration Platform - Fraud Detection Demo

## Overview

This demo showcases the comprehensive fraud detection capabilities of the Intent Orchestration Platform through a realistic social engineering attack scenario. The demo features Sarah Johnson, a bank customer who receives a suspicious phone call from someone claiming to be from her bank's security department.

## Scenario: Sarah's Social Engineering Attack

### Background
Sarah Johnson receives a phone call from someone claiming to be "Michael from the bank security department." The caller uses sophisticated social engineering tactics to attempt to steal her banking credentials and personal information.

### Attack Characteristics
- **Authority Impersonation**: Caller claims to be from bank security
- **Urgency Creation**: 10-minute deadline to "protect" the account
- **Fear Tactics**: Claims of "unusual activity" and "foreign IP address"
- **Information Harvesting**: Requests account number, SSN, and security codes
- **Trust Exploitation**: Uses security language to appear legitimate

## Demo Flow

### Phase 1: Initial Contact
- Presentation of the suspicious call scenario
- Display of customer information and call details
- Analysis of the social engineering setup

### Phase 2: Intent Detection & Classification
- Real-time analysis of the call content using NLP
- Intent classification and entity extraction
- Threat indicator identification
- Urgency and risk scoring

### Phase 3: Multi-Agent Fraud Analysis
- **SIM Swap Agent**: Checks for recent SIM card changes
- **Device Location Agent**: Analyzes location patterns and risks
- **KYC Match Agent**: Verifies customer identity
- **Scam Signal Agent**: Detects social engineering tactics

### Phase 4: Workflow Orchestration
- LangGraph-powered workflow execution
- Coordinated analysis across multiple agents
- Step-by-step fraud detection process
- Performance and timing metrics

### Phase 5: Risk Assessment & Recommendations
- Comprehensive fraud risk scoring
- Consolidated analysis from all agents
- Attack classification and threat level assessment
- Actionable security recommendations

## Key Technologies Demonstrated

### TMF 921A Intent Management
- Standards-compliant intent processing
- Real-time intent detection and classification
- Entity extraction and context analysis

### CAMARA API Integration
- Device Swap API for SIM change detection
- SIM Swap API for fraud pattern analysis
- Device Location API for geospatial risk assessment
- KYC Match API for identity verification
- Scam Signal API for social engineering detection

### Multi-Agent Architecture
- Specialized agents for different fraud detection aspects
- Agent factory for lifecycle management
- Health monitoring and performance metrics
- Capability-based agent selection

### Workflow Orchestration
- LangGraph state management
- Parallel and sequential execution flows
- Decision-based routing
- Comprehensive result aggregation

### Natural Language Processing
- spaCy-powered semantic analysis
- Pattern-based intent classification
- Entity recognition and extraction
- Threat indicator detection

## Running the Demo

### Prerequisites
1. Python 3.8+ environment
2. All dependencies installed (see requirements.txt)
3. Mock CAMARA APIs running on localhost:8001
4. Backend services initialized

### Execution
```bash
# Navigate to demo directory
cd demo

# Run the fraud detection scenario
python fraud_detection_scenario.py
```

### Interactive Demo
The demo is designed to be interactive:
- Press Enter to advance through each phase
- Review detailed analysis results at each step
- Observe real-time agent coordination
- See comprehensive risk assessment output

## Expected Outcomes

### Successful Detection
The platform should successfully:
- ✅ Identify the social engineering attempt
- ✅ Classify attack tactics (urgency, authority, fear)
- ✅ Detect information harvesting attempts
- ✅ Provide HIGH risk assessment
- ✅ Generate appropriate security recommendations

### Risk Factors Identified
- Authority impersonation detected
- Urgency pressure tactics identified
- Information harvesting requests found
- Trust exploitation patterns recognized
- Suspicious caller behavior patterns

### Recommendations Generated
- Block further communication from caller
- Verify customer identity through alternative channels
- Implement enhanced account monitoring
- Educate customer about social engineering tactics
- Review and update security protocols

## Technical Insights

### Agent Coordination
The demo showcases how multiple specialized agents work together:
- Each agent provides domain-specific analysis
- Results are aggregated for comprehensive assessment
- Agents communicate through standardized interfaces
- Performance metrics are tracked across all agents

### Workflow Intelligence
LangGraph orchestration demonstrates:
- Dynamic workflow adaptation based on analysis results
- Parallel processing for improved performance
- Conditional routing based on risk factors
- State management across complex decision trees

### Real-time Processing
The platform processes the fraud scenario in real-time:
- Intent classification happens immediately
- Agent analysis runs concurrently
- Results are available within seconds
- Interactive feedback provides immediate insights

## Educational Value

This demo serves as:
- **Training Material**: Understanding social engineering tactics
- **Technical Showcase**: Platform capabilities demonstration
- **Security Awareness**: Real-world attack pattern recognition
- **Integration Example**: Multi-system coordination

## Customization

The demo can be customized by:
- Modifying the scenario details in `fraud_detection_scenario.py`
- Adjusting agent sensitivity thresholds
- Adding new social engineering tactics
- Incorporating additional CAMARA APIs
- Extending workflow orchestration logic

## Metrics and Analytics

The demo provides comprehensive metrics:
- Processing time for each analysis phase
- Agent performance and response times
- Risk scoring breakdown by category
- Confidence levels for each detection
- Overall system performance indicators

## Production Considerations

For production deployment:
- Replace mock CAMARA APIs with real implementations
- Implement proper authentication and authorization
- Add audit logging and compliance tracking
- Scale agents based on actual load requirements
- Integrate with existing fraud prevention systems

This demo effectively demonstrates the power of intent-driven orchestration for fraud detection, showcasing how modern telecommunications APIs, AI-powered analysis, and workflow orchestration can work together to protect customers from sophisticated social engineering attacks.