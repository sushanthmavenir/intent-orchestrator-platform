#!/usr/bin/env python3
"""
Intent Orchestrator Platform Startup Script
This script starts the FastAPI backend server.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)


def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)


def download_spacy_model():
    """Download spaCy English model if not already present"""
    print("Checking spaCy English model...")
    try:
        import spacy
        try:
            spacy.load("en_core_web_sm")
            print("spaCy model already installed!")
        except OSError:
            print("Downloading spaCy English model...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            print("spaCy model downloaded successfully!")
    except ImportError:
        print("spaCy not installed yet, will be handled by requirements installation")


def create_data_directory():
    """Create data directory if it doesn't exist"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print(f"Data directory ready: {data_dir.absolute()}")


def start_backend():
    """Start the FastAPI backend server"""
    print("Starting Intent Orchestrator Platform backend...")
    print("Backend will be available at: http://localhost:8000")
    print("API documentation will be available at: http://localhost:8000/api/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        os.chdir("backend")
        subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except FileNotFoundError:
        print("Error: Could not find uvicorn. Make sure requirements are installed.")
        sys.exit(1)


def main():
    """Main startup function"""
    print("Intent Orchestrator Platform - Startup Script")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"Working directory: {project_dir.absolute()}")
    
    # Install requirements
    if not Path("venv").exists():
        print("Tip: Consider creating a virtual environment with 'python -m venv venv'")
    
    install_requirements()
    
    # Download spaCy model
    download_spacy_model()
    
    # Create data directory
    create_data_directory()
    
    # Start backend
    start_backend()


if __name__ == "__main__":
    main()