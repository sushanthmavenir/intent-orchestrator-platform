from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import uuid
import logging
import sys

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger for main module
main_logger = logging.getLogger(__name__)

# Set root logger and all child loggers to INFO level
logging.getLogger().setLevel(logging.INFO)

# Explicitly configure all our module loggers
logger_names = [
    'intent_analysis.workflow_orchestrator',
    'intent_analysis.chat_processor', 
    'intent_analysis.intent_classifier',
    'intent_analysis.analyzers.semantic_analyzer',
    'intent_analysis.patterns.pattern_matcher',
    'agents.base.base_agent',
    'agents.agent_factory',
    'agents.specialized',
    'workflow.engines.langgraph_orchestrator',
    'workflow.templates.workflow_templates',
    'api.database.database',
    'camara_apis.main',
    'mcp'
]

for logger_name in logger_names:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = True

from api.routers.tmf921_router import router as tmf921_router
from intent_analysis import ChatMessageProcessor, WorkflowOrchestrator
from api.database.database import IntentDatabase


app = FastAPI(
    title="Intent Orchestrator Platform",
    description="TMF 921A Intent Management API with Chat Interface and Workflow Orchestration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tmf921_router)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.chat_history: List[Dict[str, Any]] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "Welcome to Intent Orchestrator Platform Chat"
        }))
        
        await websocket.send_text(json.dumps({
            "type": "history",
            "messages": self.chat_history[-50:]
        }))
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: dict):
        message["timestamp"] = datetime.utcnow().isoformat()
        message["id"] = str(uuid.uuid4())
        
        self.chat_history.append(message)
        
        if len(self.chat_history) > 100:
            self.chat_history = self.chat_history[-100:]
        
        message_json = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()
print("Initializing components...")

chat_processor = ChatMessageProcessor()
workflow_orchestrator = WorkflowOrchestrator()
intent_db = IntentDatabase()

print("Components initialized successfully")
main_logger.info("Application components initialized successfully")


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "chat_message":
                # Broadcast user message immediately
                user_message = {
                    "type": "user_message",
                    "content": message_data.get("content", ""),
                    "user": message_data.get("user", "User"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.broadcast(user_message)
                
                # Process chat message into intent and start workflow
                chat_content = message_data.get("content", "")
                user_id = message_data.get("user", "User")
                
                # Send processing status
                processing_message = {
                    "type": "processing_status",
                    "content": "🔄 Processing your message and creating intent...",
                    "user": "System",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.broadcast(processing_message)
                
                # Process chat message into intent with analysis
                main_logger.info(f"Processing chat message from user {user_id}: {chat_content[:50]}...")
                processing_result = await chat_processor.process_chat_message(chat_content, user_id)
                main_logger.info(f"Chat processing result status: {processing_result.get('status')}")
                
                if processing_result["status"] == "success":
                    # Save intent to database
                    intent_data = processing_result["intent"]
                    try:
                        created_intent = intent_db.create_intent(intent_data)
                        
                        # Send intent creation confirmation
                        intent_message = {
                            "type": "intent_created",
                            "content": f"✅ Intent created: {intent_data['name']}",
                            "user": "Intent Engine",
                            "timestamp": datetime.utcnow().isoformat(),
                            "intent_id": intent_data["id"],
                            "analysis": processing_result["analysis"]
                        }
                        await manager.broadcast(intent_message)
                        
                        # Execute workflow
                        workflow_message = {
                            "type": "workflow_starting",
                            "content": f"🚀 Starting {processing_result['workflow']['workflow_type']} workflow...",
                            "user": "Workflow Engine",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await manager.broadcast(workflow_message)
                        
                        # Execute workflow asynchronously
                        main_logger.info(f"Starting workflow execution for intent {intent_data['id']}")
                        asyncio.create_task(
                            execute_chat_workflow(
                                created_intent, 
                                processing_result["workflow"],
                                manager
                            )
                        )
                        
                    except Exception as e:
                        error_message = {
                            "type": "error",
                            "content": f"❌ Error creating intent: {str(e)}",
                            "user": "System",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await manager.broadcast(error_message)
                        
                else:
                    error_message = {
                        "type": "error",
                        "content": f"❌ Error processing message: {processing_result.get('error', 'Unknown error')}",
                        "user": "System",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.broadcast(error_message)
                
            elif message_data.get("type") == "intent_submission":
                intent_message = {
                    "type": "intent_submitted",
                    "intent_data": message_data.get("intent_data"),
                    "user": message_data.get("user", "User"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await manager.broadcast(intent_message)
                
                processing_response = await process_intent_submission(message_data.get("intent_data"))
                await manager.broadcast(processing_response)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def execute_chat_workflow(intent: Dict[str, Any], workflow_plan: Dict[str, Any], connection_manager: ConnectionManager):
    """Execute workflow for chat-originated intent and send real-time updates"""
    
    try:
        main_logger.info(f"Inside execute_chat_workflow for intent {intent.get('id')}")
        main_logger.info(f"Workflow plan: {workflow_plan.get('workflow_type')}")
        # Execute the workflow
        main_logger.info("Calling workflow_orchestrator.execute_workflow...")
        workflow_result = await workflow_orchestrator.execute_workflow(intent, workflow_plan)
        main_logger.info(f"Workflow result: {workflow_result.get('status')}")
        
        if workflow_result["status"] == "success":
            # Send workflow completion message
            completion_message = {
                "type": "workflow_completed",
                "content": f"✅ Workflow completed successfully!",
                "user": "Workflow Engine",
                "timestamp": datetime.utcnow().isoformat(),
                "workflow_id": workflow_result["workflow_id"],
                "results": workflow_result["results"],
                "recommendations": workflow_result.get("recommendations", [])
            }
            await connection_manager.broadcast(completion_message)
            
            # Send detailed analysis results if available
            if "risk_assessment" in workflow_result:
                risk_assessment = workflow_result["risk_assessment"]
                risk_message = {
                    "type": "risk_assessment",
                    "content": f"🎯 Risk Assessment: {risk_assessment['risk_level'].upper()} risk ({risk_assessment['overall_risk_score']:.2%})",
                    "user": "Risk Analyzer",
                    "timestamp": datetime.utcnow().isoformat(),
                    "risk_assessment": risk_assessment
                }
                await connection_manager.broadcast(risk_message)
            
            # Send recommendations
            if workflow_result.get("recommendations"):
                for i, recommendation in enumerate(workflow_result["recommendations"]):
                    rec_message = {
                        "type": "recommendation",
                        "content": recommendation,
                        "user": "Advisory System",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await connection_manager.broadcast(rec_message)
                    await asyncio.sleep(0.5)  # Small delay between recommendations
            
        else:
            # Send workflow error message
            error_message = {
                "type": "workflow_error",
                "content": f"❌ Workflow execution failed: {workflow_result.get('error', 'Unknown error')}",
                "user": "Workflow Engine",
                "timestamp": datetime.utcnow().isoformat()
            }
            await connection_manager.broadcast(error_message)
            
    except Exception as e:
        error_message = {
            "type": "workflow_error",
            "content": f"❌ Workflow execution error: {str(e)}",
            "user": "System",
            "timestamp": datetime.utcnow().isoformat()
        }
        await connection_manager.broadcast(error_message)


async def process_chat_message(content: str) -> Dict[str, Any]:
    """Process chat message and generate bot response"""
    
    await asyncio.sleep(1)
    
    if "fraud" in content.lower():
        response_content = "I can help you with fraud detection! I can analyze transactions, check device patterns, and coordinate with various security agents. Would you like me to start a fraud investigation workflow?"
    elif "intent" in content.lower():
        response_content = "I can help you create and manage intents using TMF 921A specification. You can describe what you want to achieve, and I'll help structure it as a formal intent."
    elif "help" in content.lower():
        response_content = """I can assist you with:
• Creating and managing TMF 921A intents
• Fraud detection and analysis
• Workflow orchestration
• Agent coordination
• CAMARA API interactions

What would you like to work on?"""
    else:
        response_content = f"I understand you said: '{content}'. How can I help you with intent management or fraud detection?"
    
    return {
        "type": "bot_message",
        "content": response_content,
        "user": "Intent Orchestrator",
        "timestamp": datetime.utcnow().isoformat()
    }


async def process_intent_submission(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process intent submission and start workflow orchestration"""
    
    await asyncio.sleep(2)
    
    intent_name = intent_data.get("name", "Unnamed Intent")
    
    return {
        "type": "workflow_status",
        "content": f"Intent '{intent_name}' has been submitted for processing. Analyzing requirements and selecting appropriate agents...",
        "user": "Workflow Engine",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "processing",
        "intent_id": intent_data.get("id")
    }


@app.get("/")
async def root():
    return {
        "message": "Intent Orchestrator Platform",
        "version": "1.0.0",
        "apis": {
            "tmf921": "/tmf-api/intent/v4/",
            "docs": "/api/docs",
            "websocket": "/ws/chat"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational",
            "database": "operational",
            "websocket": "operational"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )