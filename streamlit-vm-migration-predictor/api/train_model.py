import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import os

def create_sample_data():
    """Generate sample training data"""
    np.random.seed(42)
    n_samples = 1000

    # Generate features
    cpu_load = np.random.uniform(10, 100, n_samples)
    memory_usage = np.random.uniform(20, 95, n_samples)
    disk_io = np.random.uniform(5, 1000, n_samples)
    network_bandwidth = np.random.uniform(50, 1000, n_samples)

    # Calculate realistic downtime
    base_downtime = 50  # Base 50ms
    cpu_impact = cpu_load * 0.8
    memory_impact = memory_usage * 0.6
    disk_impact = disk_io * 0.4
    network_impact = (1000 - network_bandwidth) * 0.1
    noise = np.random.normal(0, 10, n_samples)

    downtime = base_downtime + cpu_impact + memory_impact + disk_impact + network_impact + noise
    downtime = np.maximum(downtime, 10)  # Minimum 10ms

    return np.column_stack([cpu_load, memory_usage, disk_io, network_bandwidth]), downtime

def train_model():
    """Train and save the model"""
    print("Generating sample data...")
    X, y = create_sample_data()

    print("Training model...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    score = model.score(X_test, y_test)
    print(f"Model R2 Score: {score:.3f}")

    # Ensure directory exists
    model_dir = "/app/model"
    os.makedirs(model_dir, exist_ok=True)

    # Save model
    model_path = os.path.join(model_dir, "model.joblib")
    joblib.dump(model, model_path)
    print(f"[OK] Model saved to {model_path}")

    return model

if __name__ == "__main__":
    train_model()
    print("Model training complete.")