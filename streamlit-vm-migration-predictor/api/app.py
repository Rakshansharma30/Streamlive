from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Counter, Gauge
from pydantic import BaseModel
import joblib
import numpy as np
import os
from typing import Dict, Any
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VM Migration Predictor API",
    description="Predicts VM migration downtime based on system metrics",
    version="1.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

vm_migration_predictions_total = Counter("vm_migration_predictions_total", "Total VM migration predictions")
api_requests_total = Counter("api_requests_total", "Total API requests")
vm_migration_accuracy = Gauge("vm_migration_accuracy", "Accuracy of VM migration predictions")

# Global model variable
model = None

def load_model():
    """Load the ML model"""
    global model
    model_path = '/app/model/model.joblib'
    if os.path.exists(model_path):
        try:
            model = joblib.load(model_path)
            logger.info("[OK] Model loaded successfully from %s", model_path)
        except Exception as e:
            logger.error("[ERROR] Error loading model: %s", str(e))
            model = None
    else:
        logger.warning("[WARNING] Model file not found at %s", model_path)

# Load model on startup
load_model()

class MigrationData(BaseModel):
    cpu_load: float
    memory_usage: float
    disk_io: float
    network_bandwidth: float

    class Config:
        json_schema_extra = {
            "example": {
                "cpu_load": 75.5,
                "memory_usage": 68.2,
                "disk_io": 45.8,
                "network_bandwidth": 850.0
            }
        }

class PredictionResponse(BaseModel):
    predicted_downtime: float
    confidence: float
    status: str

@app.get("/")
async def root():
    api_requests_total.inc()
    return {
        "message": "VM Migration Predictor API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "health": "/health",
            "simulate": "/simulate",
            "metrics": "/metrics"
        }
    }

@app.get("/health")
async def health_check():
    api_requests_total.inc()
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_path": "/app/model/model.joblib",
        "timestamp": np.datetime64('now').item().isoformat()
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_downtime(data: MigrationData):
    api_requests_total.inc()
    try:
        features = np.array([[
            data.cpu_load, 
            data.memory_usage, 
            data.disk_io, 
            data.network_bandwidth
        ]])

        if model is not None:
            prediction = model.predict(features)[0]
            confidence = 0.85  # Mock confidence score
            vm_migration_accuracy.set(confidence)
        else:
            # Mock prediction based on simple heuristics
            complexity_score = (data.cpu_load + data.memory_usage) / 2
            base_downtime = 100  # Base 100ms
            prediction = base_downtime + (complexity_score * 2)
            confidence = 0.75
            vm_migration_accuracy.set(confidence)

        vm_migration_predictions_total.inc()

        return PredictionResponse(
            predicted_downtime=round(prediction, 2),
            confidence=round(confidence, 2),
            status="success"
        )

    except Exception as e:
        logger.error("Prediction error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/simulate")
async def simulate_migration():
    api_requests_total.inc()
    """Trigger migration simulation"""
    return {
        "status": "Simulation started",
        "metrics_port": 9100,
        "prometheus_url": "http://prometheus:9090",
        "grafana_url": "http://grafana:3000"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
