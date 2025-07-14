import requests
import time
import random
import threading
import json
from datetime import datetime
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("[WARNING] psutil not available, using mock system metrics")

API_URL = "http://localhost:8001"

class MigrationSimulator:
    def __init__(self):
        self.results = []
        self.running = False
    
    def get_system_metrics(self):
        """Get real system metrics"""
        if PSUTIL_AVAILABLE:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                return {
                    "cpu_load": cpu_percent,
                    "memory_usage": memory.percent,
                    "disk_io": random.uniform(10, 100),  # Simplified
                    "network_bandwidth": random.uniform(100, 1000)  # Mbps
                }
            except:
                pass
        
        # Fallback to random values
        return {
            "cpu_load": random.uniform(20, 95),
            "memory_usage": random.uniform(30, 90),
            "disk_io": random.uniform(10, 100),
            "network_bandwidth": random.uniform(50, 1000)
        }
    
    def simulate_single_migration(self, metrics=None):
        """Simulate a single VM migration"""
        if metrics is None:
            metrics = self.get_system_metrics()
        
        try:
            # Get prediction from API
            response = requests.post(
                f"{API_URL}/predict",
                json=metrics,
                timeout=5
            )
            
            if response.status_code == 200:
                prediction_data = response.json()
                predicted_downtime = prediction_data["predicted_downtime"]
                confidence = prediction_data.get("confidence", 0.0)
            else:
                print(f"[ERROR] API Error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Connection Error: {e}")
            return None
        
        # Simulate actual migration process
        print(f"[INFO] Starting migration simulation...")
        print(f"   CPU: {metrics['cpu_load']:.1f}%")
        print(f"   Memory: {metrics['memory_usage']:.1f}%")
        print(f"   Disk I/O: {metrics['disk_io']:.1f} MB/s")
        print(f"   Network: {metrics['network_bandwidth']:.1f} Mbps")
        print(f"   Predicted Downtime: {predicted_downtime:.2f} ms")
        
        # Simulate migration delay (more realistic)
        start_time = time.time()
        
        # Variable delay based on system load
        base_delay = 0.1  # 100ms base
        load_factor = (metrics['cpu_load'] + metrics['memory_usage']) / 200
        actual_delay = base_delay + (load_factor * 0.3) + random.uniform(0, 0.1)
        
        time.sleep(actual_delay)
        actual_downtime = (time.time() - start_time) * 1000
        
        # Calculate accuracy
        accuracy = 100 - abs(predicted_downtime - actual_downtime) / max(predicted_downtime, actual_downtime) * 100
        accuracy = max(0, accuracy)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "predicted_downtime": predicted_downtime,
            "actual_downtime": actual_downtime,
            "accuracy": accuracy,
            "confidence": confidence
        }
        
        print(f"[OK] Migration completed!")
        print(f"   Actual Downtime: {actual_downtime:.2f} ms")
        print(f"   Accuracy: {accuracy:.1f}%")
        print(f"   Confidence: {confidence:.1f}%")
        print("-" * 50)
        
        self.results.append(result)
        return result
    
    def run_continuous_simulation(self, duration_minutes=5, interval_seconds=30):
        """Run continuous migration simulations"""
        print(f"[INFO] Starting continuous simulation for {duration_minutes} minutes...")
        print(f"   Interval: {interval_seconds} seconds")
        print("=" * 50)
        
        self.running = True
        start_time = time.time()
        simulation_count = 0
        
        while self.running and (time.time() - start_time) < (duration_minutes * 60):
            simulation_count += 1
            print(f"\n[INFO] Simulation #{simulation_count}")
            
            result = self.simulate_single_migration()
            if result:
                # Brief summary
                avg_accuracy = sum(r["accuracy"] for r in self.results) / len(self.results)
                print(f"[INFO] Running Average Accuracy: {avg_accuracy:.1f}%")
            
            time.sleep(interval_seconds)
        
        self.running = False
        self.print_summary()
    
    def print_summary(self):
        """Print simulation summary"""
        if not self.results:
            print("[ERROR] No results to summarize")
            return
        
        print("\n" + "=" * 60)
        print("[INFO] SIMULATION SUMMARY")
        print("=" * 60)
        print(f"Total Simulations: {len(self.results)}")
        
        accuracies = [r["accuracy"] for r in self.results]
        predicted_times = [r["predicted_downtime"] for r in self.results]
        actual_times = [r["actual_downtime"] for r in self.results]
        
        print(f"Average Accuracy: {sum(accuracies) / len(accuracies):.1f}%")
        print(f"Best Accuracy: {max(accuracies):.1f}%")
        print(f"Worst Accuracy: {min(accuracies):.1f}%")
        print(f"Average Predicted Downtime: {sum(predicted_times) / len(predicted_times):.2f} ms")
        print(f"Average Actual Downtime: {sum(actual_times) / len(actual_times):.2f} ms")
        
        # Save results
        filename = f"simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"[OK] Results saved to {filename}")
    
    def stress_test(self):
        """Run stress test with high system load"""
        print("[INFO] Starting stress test...")
        
        # Simulate high load scenarios
        high_load_scenarios = [
            {"cpu_load": 95, "memory_usage": 85, "disk_io": 90, "network_bandwidth": 200},
            {"cpu_load": 80, "memory_usage": 95, "disk_io": 75, "network_bandwidth": 150},
            {"cpu_load": 90, "memory_usage": 90, "disk_io": 95, "network_bandwidth": 100},
        ]
        
        for i, scenario in enumerate(high_load_scenarios, 1):
            print(f"\n[INFO] Stress Test Scenario {i}")
            self.simulate_single_migration(scenario)
            time.sleep(2)

def main():
    simulator = MigrationSimulator()
    
    print("[INFO] VM Migration Predictor - Simulation Suite")
    print("=" * 50)
    
    # Check API health
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"[OK] API is healthy: {health_data}")
        else:
            print(f"[WARNING] API health check failed: {response.status_code}")
    except:
        print("[ERROR] Cannot connect to API. Make sure it's running on http://localhost:8001")
        return
    
    print("\nChoose simulation mode:")
    print("1. Single migration test")
    print("2. Continuous simulation (5 minutes)")
    print("3. Stress test")
    print("4. Custom continuous simulation")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            simulator.simulate_single_migration()
        elif choice == "2":
            simulator.run_continuous_simulation(5, 30)
        elif choice == "3":
            simulator.stress_test()
        elif choice == "4":
            duration = int(input("Duration (minutes): "))
            interval = int(input("Interval (seconds): "))
            simulator.run_continuous_simulation(duration, interval)
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\n[INFO] Simulation stopped by user")
        simulator.running = False
        simulator.print_summary()
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    main()
