#!/bin/bash

# Intent Orchestration Platform Startup Script
# This script starts all platform components in the correct order

echo "🚀 Starting Intent Orchestration Platform..."

# Set environment variables
export PYTHONPATH=/app/backend
export PYTHONUNBUFFERED=1

# Function to start background services
start_service() {
    local service_name=$1
    local command=$2
    echo "📦 Starting $service_name..."
    $command &
    local pid=$!
    echo "✅ $service_name started with PID $pid"
    return $pid
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service_name failed to start within timeout"
    return 1
}

# Create log directory
mkdir -p /app/logs

# Start CAMARA Mock APIs
echo "🌐 Starting CAMARA Mock APIs..."
cd /app/backend
start_service "CAMARA APIs" "python -m uvicorn camara_apis.main:app --host 0.0.0.0 --port 8001"

# Wait for CAMARA APIs to be ready
if ! wait_for_service "http://localhost:8001/health" "CAMARA APIs"; then
    echo "❌ Failed to start CAMARA APIs"
    exit 1
fi

# Start Main FastAPI Backend
echo "🔧 Starting Main FastAPI Backend..."
start_service "FastAPI Backend" "python -m uvicorn main:app --host 0.0.0.0 --port 8000"

# Wait for backend to be ready
if ! wait_for_service "http://localhost:8000/health" "FastAPI Backend"; then
    echo "❌ Failed to start FastAPI Backend"
    exit 1
fi

# Start Frontend (if in development mode)
if [ "$NODE_ENV" != "production" ]; then
    echo "🎨 Starting React Frontend..."
    cd /app/frontend
    start_service "React Frontend" "npm start"
    
    # Wait for frontend to be ready
    if ! wait_for_service "http://localhost:3000" "React Frontend"; then
        echo "❌ Failed to start React Frontend"
        exit 1
    fi
else
    echo "📦 Frontend built for production - serving via backend"
fi

# Initialize the platform
echo "⚙️  Initializing platform components..."
cd /app/backend
python -c "
import asyncio
import sys
import os
sys.path.append('/app/backend')

async def initialize_platform():
    print('🔧 Initializing agents...')
    from agents.agent_factory import agent_factory
    agents = await agent_factory.create_all_agents()
    print(f'✅ Initialized {len(agents)} agents')
    
    print('🏛️ Initializing resource registry...')
    from mcp.registry.resource_registry import ResourceRegistry
    registry = ResourceRegistry()
    print('✅ Resource registry ready')
    
    print('🧠 Initializing intent classifier...')
    from intent_analysis.intent_classifier import IntentClassifier
    classifier = IntentClassifier()
    print('✅ Intent classifier ready')
    
    print('🎼 Platform initialization complete!')

if __name__ == '__main__':
    asyncio.run(initialize_platform())
"

echo ""
echo "🎉 Intent Orchestration Platform is ready!"
echo "📊 Platform Status:"
echo "   Backend API:     http://localhost:8000"
echo "   CAMARA APIs:     http://localhost:8001"
if [ "$NODE_ENV" != "production" ]; then
    echo "   Frontend UI:     http://localhost:3000"
fi
echo "   Health Check:    http://localhost:8000/health"
echo "   API Docs:        http://localhost:8000/docs"
echo ""
echo "🎭 To run the fraud detection demo:"
echo "   docker exec -it <container_name> python demo/fraud_detection_scenario.py"
echo ""

# Keep the container running and log output
echo "📝 Monitoring services..."
tail -f /dev/null