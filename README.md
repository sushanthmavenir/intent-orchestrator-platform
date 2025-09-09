# Intent Orchestration Platform

A comprehensive TMF 921A-compliant intent management platform with integrated CAMARA APIs, multi-agent fraud detection, and LangGraph workflow orchestration.

## 🎯 Overview

The Intent Orchestration Platform is a cutting-edge system that combines telecommunications industry standards (TMF 921A) with modern AI-powered fraud detection capabilities. It demonstrates real-time intent classification, multi-agent orchestration, and social engineering attack prevention through a sophisticated chat interface and comprehensive API ecosystem.

### Key Features

- **TMF 921A Compliance**: Full implementation of TM Forum's Intent Management API specification v4.0.0
- **CAMARA API Integration**: Mock implementations of all major CAMARA APIs for telecommunications fraud detection
- **Multi-Agent Architecture**: Specialized agents for different aspects of fraud detection and analysis
- **LangGraph Orchestration**: Advanced workflow management with state-based routing and decision trees
- **Real-time Chat Interface**: WebSocket-powered chat for interactive intent submission and analysis
- **Comprehensive Fraud Detection**: Multi-layered approach combining pattern recognition, semantic analysis, and risk assessment
- **Social Engineering Detection**: Advanced analysis of communication patterns to identify manipulation tactics
- **Workflow Automation**: Intelligent routing and execution of complex fraud detection workflows

## Architecture

```
intent-orchestrator-platform/
├── backend/                 # FastAPI backend
│   ├── api/                # TMF 921A API implementation
│   │   ├── models/         # Pydantic data models
│   │   ├── routers/        # FastAPI route handlers
│   │   └── database/       # SQLite database layer
│   ├── intent_analysis/    # NLP and intent classification
│   ├── mcp/               # MCP resource registry
│   ├── workflow/          # LangGraph workflow orchestration
│   ├── agents/            # Specialized agent implementations
│   └── camara_apis/       # Mock CAMARA API implementations
├── frontend/              # React chat interface
├── data/                  # SQLite database files
└── docs/                  # Documentation
```

## Quick Start

### Prerequisites

- Python 3.8+ 
- Node.js 16+ (for frontend)
- Git

### Backend Setup

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd intent-orchestrator-platform
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\\Scripts\\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Start the backend:**
   ```bash
   python start_server.py
   ```
   
   This will automatically:
   - Install all Python dependencies
   - Download the spaCy English model
   - Create necessary directories
   - Start the FastAPI server on http://localhost:8000

### Frontend Setup

1. **In a new terminal, start the frontend:**
   ```bash
   # On Windows:
   start_frontend.bat
   
   # On macOS/Linux:
   cd frontend
   npm install
   npm start
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

## API Endpoints

### TMF 921A Intent Management API

Base URL: `http://localhost:8000/tmf-api/intent/v4`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/intent` | Create a new intent |
| GET | `/intent` | List all intents |
| GET | `/intent/{id}` | Get specific intent |
| PATCH | `/intent/{id}` | Update intent |
| DELETE | `/intent/{id}` | Delete intent |
| GET | `/intent/{intentId}/intentReport` | List intent reports |
| GET | `/intent/{intentId}/intentReport/{id}` | Get specific intent report |
| DELETE | `/intent/{intentId}/intentReport/{id}` | Delete intent report |
| POST | `/hub` | Register event listener |
| DELETE | `/hub/{id}` | Unregister event listener |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/chat` | Real-time chat and intent submission |

## Intent Creation Examples

### Via REST API

```json
POST /tmf-api/intent/v4/intent
{
  "name": "Fraud Detection Intent",
  "description": "Detect potential fraud in customer transaction",
  "expression": {
    "@type": "JsonLdExpression",
    "expressionLanguage": "JSON-LD",
    "expressionValue": "{\"@context\": {\"tio\": \"https://tmforum.org/ontology/\"}, \"@type\": \"tio:FraudDetectionIntent\", \"tio:customerId\": \"12345\", \"tio:threshold\": 0.8}"
  }
}
```

### Via Chat Interface

Simply type natural language in the chat:
```
"I need to check if customer 12345 has suspicious activity"
```

The system will:
1. Analyze the message using spaCy NLP
2. Extract relevant entities (customer ID, intent type)
3. Create a formal TMF 921A intent
4. Initiate appropriate workflow orchestration

## Development Features

### Database

- SQLite database for development
- Automatic schema creation and migration
- Support for intent versioning and history

### Real-time Communication

- WebSocket-based chat interface
- Live intent status updates
- Event-driven architecture with TMF 921A event types

### Testing

```bash
# Run backend tests
cd backend
python -m pytest

# Run frontend tests
cd frontend
npm test
```

### API Documentation

- Interactive Swagger UI: http://localhost:8000/api/docs
- ReDoc documentation: http://localhost:8000/api/redoc

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite:///./data/intents.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# WebSocket Configuration
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws/chat
```

### Logging

Logs are written to:
- Console output (development)
- `logs/app.log` (production)

## Workflow Orchestration

The platform supports complex workflow orchestration using LangGraph:

1. **Intent Analysis**: NLP processing to understand user requirements
2. **Agent Selection**: Choose appropriate agents based on capabilities
3. **Parallel Execution**: Run multiple agents concurrently
4. **Result Aggregation**: Combine and correlate agent outputs
5. **Decision Making**: Apply business rules and thresholds
6. **Reporting**: Generate TMF 921A compliant intent reports

## Mock CAMARA APIs

For demonstration purposes, the platform includes mock implementations of:

- **Device Swap API**: Detect SIM card changes
- **SIM Swap API**: Identify suspicious SIM activities
- **KYC Match API**: Verify customer identity
- **Device Location API**: Track device location patterns
- **Scam Signal API**: Detect social engineering attempts

## Fraud Detection Demo

The platform includes a comprehensive fraud detection scenario:

1. **Customer Sarah receives a suspicious call**
2. **Multiple agents analyze different aspects:**
   - Device patterns (recent SIM swap)
   - Location anomalies (device in different country)
   - Transaction patterns (unusual amounts/recipients)
   - Social engineering indicators
3. **Coordinated response based on risk score**
4. **Real-time dashboard updates**

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit with descriptive messages
5. Push to your fork and create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- GitHub Issues: Report bugs and request features
- Documentation: Check the `/docs` directory
- API Reference: http://localhost:8000/api/docs

## Acknowledgments

- TMF Forum for the Intent Management API specification
- FastAPI for the excellent web framework
- React for the frontend framework
- spaCy for natural language processing capabilities