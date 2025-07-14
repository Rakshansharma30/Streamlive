import requests
import time
import random
import json
from datetime import datetime
import psutil

API_URL = "http://localhost:8001"

class MigrationSimulator:
    def __init__(self):
        self.results = []
        self.running = False
    
    def get_real_metrics(self):
        """Get real system metrics using psutil"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            
            # Calculate rates
            if hasattr(self, 'last_disk_io'):
                disk_read_rate = (disk_io.read_bytes - self.last_disk_io.read_bytes) / (1024 * 1024)  # MB/s
                disk_write_rate = (disk_io.write_bytes - self.last_disk_io.write_bytes) / (1024 * 1024)
            else:
                disk_read_rate = 0
                disk_write_rate = 0
                
            if hasattr(self, 'last_net_io'):
                net_sent_rate = (net_io.bytes_sent - self.last_net_io.bytes_sent) / (1024 * 1024)  # MB/s
                net_recv_rate = (net_io.bytes_recv - self.last_net_io.bytes_recv) / (1024 * 1024)
            else:
                net_sent_rate = 0
                net_recv_rate = 0
                
            self.last_disk_io = disk_io
            self.last_net_io = net_io
            
            return {
                "cpu_load": cpu_percent,
                "memory_usage": memory.percent,
                "disk_io": disk_read_rate + disk_write_rate,
                "network_bandwidth": (net_sent_rate + net_recv_rate) * 8  # Convert to Mbps
            }
        except Exception as e:
            print(f"Error getting real metrics: {e}")
            return {
                "cpu_load": random.uniform(20, 95),
                "memory_usage": random.uniform(30, 90),
                "disk_io": random.uniform(10, 100),
                "network_bandwidth": random.uniform(50, 1000)
            }
    
    def run_simulation(self):
        """Run full migration simulation"""
        print("Starting migration simulation...")
        
        # Get real metrics
        metrics = self.get_real_metrics()
        print(f"Current system metrics: {metrics}")
        
        # Make prediction
        response = requests.post(f"{API_URL}/predict", json=metrics)
        if response.status_code != 200:
            print(f"Prediction failed: {response.text}")
            return
            
        prediction = response.json()
        print(f"Predicted downtime: {prediction['predicted_downtime']} ms")
        
        # Start migration
        response = requests.get(f"{API_URL}/simulate")
        if response.status_code != 200:
            print(f"Migration start failed: {response.text}")
            return
            
        print("Migration started...")
        
        # Monitor migration status
        while True:
            status = requests.get(f"{API_URL}/migration-status").json()
            print(f"Migration status: {status['status']}")
            
            if status["status"] == "completed":
                print(f"Migration completed! Actual downtime: {status['actual_downtime']} ms")
                accuracy = 100 - abs(prediction['predicted_downtime'] - status['actual_downtime']) / prediction['predicted_downtime'] * 100
                print(f"Prediction accuracy: {accuracy:.1f}%")
                break
                
            time.sleep(1)
        
        print("Simulation complete.")

if __name__ == "__main__":
    simulator = MigrationSimulator()
    simulator.run_simulation()