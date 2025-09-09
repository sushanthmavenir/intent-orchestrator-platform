# CLAUDE.md - Intent Orchestration Platform

## Quick Start Guide

This is a TMF 921A-compliant Intent Orchestration Platform with CAMARA API integration and multi-agent fraud detection capabilities.

### Current System Status: OPERATIONAL ✅

## 🚀 Running the Platform

### Prerequisites
- Python 3.11+ installed
- All dependencies installed (`pip install -r requirements.txt`)
- spaCy English model downloaded (`python -m spacy download en_core_web_sm`)

### Start the Services

**1. Start CAMARA Mock APIs (Terminal 1):**
```bash
cd backend
python -m uvicorn camara_apis.main:app --host 127.0.0.1 --port 8003
```

**2. Start Main Application (Terminal 2):**
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8002
```

### Verify System is Running

**Health Checks:**
```bash
# Main Application
curl http://localhost:8002/health

# CAMARA APIs  
curl http://localhost:8003/health
```

## 📊 Working API Endpoints

### Main Application (Port 8002)

**TMF 921A Intent Management:**
```bash
# List all intents
curl http://localhost:8002/tmf-api/intent/v4/intent

# Create a new intent
curl -X POST "http://localhost:8002/tmf-api/intent/v4/intent" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fraud Detection Intent",
    "description": "Detect fraudulent activities",
    "expression": {
      "expressionLanguage": "JSON-LD",
      "expressionValue": "{\"@type\": \"FraudDetectionIntent\", \"action\": \"detect_fraud\"}"
    },
    "category": "security",
    "priority": 1
  }'
```

**WebSocket Chat:**
- Endpoint: `ws://localhost:8002/ws/chat`
- Real-time intent submission and processing

### CAMARA APIs (Port 8003)

**SIM Swap Detection:**
```bash
curl -X POST "http://localhost:8003/camara/sim-swap/v1/check" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1-555-0123", "max_age": 240}'
```

**Device Location:**
```bash
curl -X POST "http://localhost:8003/camara/location/v1/retrieve" \
  -H "Content-Type: application/json" \
  -d '{"device": {"phone_number": "+1-555-0123"}}'
```

**KYC Identity Verification:**
```bash
curl -X POST "http://localhost:8003/camara/kyc-match/v1/verify" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1-555-0123", "name": "John Doe"}'
```

**Scam Signal Analysis:**
```bash
curl -X POST "http://localhost:8003/camara/scam-signal/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1-555-0123", "communication_content": "Urgent: Your account will be suspended"}'
```

**Device Swap Detection:**
```bash
curl -X POST "http://localhost:8003/camara/device-swap/v1/check" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1-555-0123"}'
```

## 🎭 Fraud Detection Demo

**Run the comprehensive fraud detection scenario:**
```bash
python demo/fraud_detection_scenario.py
```

This demonstrates Sarah's social engineering attack scenario with:
- Real-time intent classification
- Multi-agent fraud analysis
- Risk assessment and recommendations
- Workflow orchestration

## 🧪 Testing

**Run Integration Tests:**
```bash
python test_integration.py
```

**Manual API Testing:**
- **API Documentation**: http://localhost:8002/api/docs
- **CAMARA API Docs**: http://localhost:8003/docs

## 🏗️ Architecture Overview

### Core Components
- **TMF 921A API**: Complete intent management specification
- **CAMARA APIs**: 5 telecommunications fraud detection APIs
- **Multi-Agent System**: Specialized fraud detection agents
- **WebSocket Chat**: Real-time communication interface
- **SQLite Database**: Intent and report storage

### Agent Framework
- **Fraud Detection Agent**: Comprehensive fraud analysis
- **SIM Swap Agent**: Telecom fraud detection
- **KYC Match Agent**: Identity verification
- **Device Location Agent**: Geospatial analysis
- **Scam Signal Agent**: Social engineering detection

## 📁 Project Structure

```
intent-orchestrator-platform/
├── backend/
│   ├── main.py                    # Main FastAPI application
│   ├── api/                       # TMF 921A API implementation
│   │   ├── models/               # Pydantic data models
│   │   ├── routers/              # API route handlers
│   │   └── database/             # SQLite operations
│   ├── camara_apis/              # Mock CAMARA APIs
│   │   ├── main.py              # CAMARA FastAPI app
│   │   └── mock_apis/           # Individual API implementations
│   ├── agents/                   # Multi-agent framework
│   │   ├── base/                # Base agent class
│   │   └── specialized/         # Fraud detection agents
│   ├── intent_analysis/          # NLP and classification
│   ├── workflow/                 # LangGraph orchestration
│   └── mcp/                     # Resource registry
├── frontend/                     # React chat interface
├── demo/                        # Fraud detection demo
├── data/                        # SQLite database files
└── docs/                        # Documentation
```

## 🔧 Configuration

### Environment Variables
```bash
export PYTHONPATH=./backend
export LOG_LEVEL=INFO
```

### Database
- **Type**: SQLite (development)
- **Location**: `./data/intents.db`
- **Auto-created**: Yes

### Ports
- **Main App**: 8002
- **CAMARA APIs**: 8003
- **Frontend**: 3000 (when running)

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using the port
netstat -ano | grep :8002

# Kill process if needed (Windows)
taskkill /PID <process_id> /F
```

**Import Errors:**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=./backend

# Verify all dependencies installed
pip install -r requirements.txt
```

**spaCy Model Missing:**
```bash
python -m spacy download en_core_web_sm
```

### Logs and Debugging
- Check server console output for errors
- API documentation available at `/docs` endpoints
- Health checks available at `/health` endpoints

## 📈 Performance Metrics

- **Response Times**: < 1 second for most operations
- **Concurrent Requests**: Handles 10+ concurrent requests
- **Database**: Efficient SQLite operations
- **Memory Usage**: Optimized for development

## 🔒 Security Features

- Input validation on all endpoints
- TMF 921A specification compliance
- Comprehensive fraud detection algorithms
- Real-time threat assessment
- Social engineering pattern recognition

## 📚 API Documentation

- **Main API**: http://localhost:8002/api/docs
- **CAMARA APIs**: http://localhost:8003/docs
- **TMF 921A Compliance**: Full specification implementation
- **Interactive Testing**: Available via Swagger UI

## 🎯 Use Cases

### 1. Intent Management
Create, manage, and process telecommunications intents according to TMF 921A standards.

### 2. Fraud Detection
Detect and prevent fraud using multiple CAMARA API data sources:
- SIM swap fraud
- Device location anomalies
- Identity verification failures
- Social engineering attempts

### 3. Customer Protection
Real-time analysis of customer communications to identify and prevent social engineering attacks.

### 4. Workflow Orchestration
Coordinate multiple fraud detection agents to provide comprehensive risk assessment.

## 🚀 Production Deployment

For production deployment, see:
- `DEPLOYMENT.md` - Comprehensive deployment guide
- `docker-compose.yml` - Container orchestration
- `Dockerfile` - Application containerization

## 📞 Support

- Check health endpoints for system status
- Review console logs for error details  
- Consult API documentation for endpoint details
- Run integration tests to verify functionality

---

**Status**: OPERATIONAL AND READY FOR USE
**Version**: 1.0.0
**Last Updated**: 2025-09-09