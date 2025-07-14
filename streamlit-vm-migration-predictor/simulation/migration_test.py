#!/usr/bin/env python3
"""
Simple migration test script
"""

import requests
import time
import random

def test_api():
    """Test API endpoints"""
    base_url = "http://localhost:8001"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # Test prediction endpoint
    test_data = {
        "cpu_load": 75.5,
        "memory_usage": 68.2,
        "disk_io": 45.8,
        "network_bandwidth": 850.0
    }
    
    try:
        response = requests.post(f"{base_url}/predict", json=test_data)
        print(f"Prediction test: {response.json()}")
    except Exception as e:
        print(f"Prediction test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("[INFO] Testing VM Migration Predictor API...")
    if test_api():
        print("[OK] All tests passed!")
    else:
        print("[ERROR] Some tests failed!")
