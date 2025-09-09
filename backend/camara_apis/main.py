"""
CAMARA APIs Main Application
============================

FastAPI application serving mock implementations of CAMARA APIs
for telecommunications fraud detection and verification.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import CAMARA API routers
from .mock_apis.device_swap_api import router as device_swap_router
from .mock_apis.sim_swap_api import router as sim_swap_router
from .mock_apis.location_api import router as location_router
from .mock_apis.kyc_match_api import router as kyc_router
from .mock_apis.scam_signal_api import router as scam_signal_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CAMARA Mock APIs",
    description="Mock implementations of CAMARA telecommunications APIs for fraud detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CAMARA Mock APIs",
        "version": "1.0.0",
        "apis": [
            "Device Swap API",
            "SIM Swap API", 
            "Device Location API",
            "KYC Match API",
            "Scam Signal API"
        ]
    }

# Include CAMARA API routers
app.include_router(device_swap_router, tags=["Device Swap"])
app.include_router(sim_swap_router, tags=["SIM Swap"])
app.include_router(location_router, tags=["Device Location"])
app.include_router(kyc_router, tags=["KYC Match"])
app.include_router(scam_signal_router, tags=["Scam Signal"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "CAMARA Mock APIs",
        "documentation": "/docs",
        "health": "/health",
        "apis": {
            "device_swap": "/camara/device-swap",
            "sim_swap": "/camara/sim-swap", 
            "device_location": "/camara/device-location",
            "kyc_match": "/camara/kyc-match",
            "scam_signal": "/camara/scam-signal"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)