@echo off
echo Intent Orchestrator Platform - Frontend Startup Script
echo ==================================================

cd frontend

echo Checking if node_modules exists...
if not exist node_modules (
    echo Installing npm dependencies...
    npm install
) else (
    echo Dependencies already installed!
)

echo.
echo Starting React development server...
echo Frontend will be available at: http://localhost:3000
echo Press Ctrl+C to stop the server
echo --------------------------------------------------

npm start