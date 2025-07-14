import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import numpy as np
import os
from typing import Dict, List, Optional, Any

# Page configuration
st.set_page_config(
    page_title="VM Migration Predictor Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .status-healthy {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .debug-panel {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ddd;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Configuration - Using environment variables
API_BASE_URL = os.getenv("API_URL", "http://api:8001")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

class VMDashboard:
    def __init__(self):
        self.api_url = API_BASE_URL
        self.prometheus_url = PROMETHEUS_URL
        
    def check_api_health(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                return {"status": "healthy", "data": response.json()}
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_prometheus_metrics(self, query: str) -> Optional[Dict]:
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}", "status": "error"}
        except Exception as e:
            return {"error": str(e), "status": "exception"}
    
    def get_prometheus_range(self, query: str, hours: int = 1) -> Optional[Dict]:
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params={
                    "query": query,
                    "start": start_time.timestamp(),
                    "end": end_time.timestamp(),
                    "step": "30s"
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}", "status": "error"}
        except Exception as e:
            return {"error": str(e), "status": "exception"}
    
    def make_prediction(self, cpu: float, memory: float, disk_io: float, network: float) -> Dict:
        try:
            data = {
                "cpu_load": cpu,
                "memory_usage": memory,
                "disk_io": disk_io,
                "network_bandwidth": network
            }
            response = requests.post(f"{self.api_url}/predict", json=data, timeout=10)
            if response.status_code == 200:
                return {"status": "success", "data": response.json()}
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

def display_metric_with_debug(name: str, data: Optional[Dict], unit: str = "%", delta_ref: float = None):
    """Helper function to display metrics with debug information"""
    if data is None:
        st.metric(name, "N/A", help="No response from Prometheus")
        return
    
    if "error" in data:
        st.metric(name, "N/A", help=f"Error: {data['error']}")
        return
    
    if not data.get("data", {}).get("result"):
        st.metric(name, "N/A", help="No metrics found")
        return
    
    try:
        value = float(data["data"]["result"][0]["value"][1])
        delta = None
        if delta_ref is not None:
            delta = f"{value-delta_ref:.1f}{unit}"
        st.metric(name, f"{value:.1f}{unit}", delta=delta)
    except (IndexError, ValueError, KeyError) as e:
        st.metric(name, "N/A", help=f"Data format error: {str(e)}")

def main():
    dashboard = VMDashboard()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 VM Migration Predictor Dashboard</h1>
        <p>Real-time monitoring and prediction of VM migration downtime</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar with debug tools
    st.sidebar.title("🎛️ Control Panel")
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
    if auto_refresh:
        time.sleep(30)
        st.experimental_rerun()
    if st.sidebar.button("🔄 Refresh Now"):
        st.experimental_rerun()

    # Debug tools in sidebar
    st.sidebar.subheader("🛠️ Debug Tools")
    debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=False)
    if st.sidebar.button("Test Prometheus Connection"):
        test_query = "up"
        test_data = dashboard.get_prometheus_metrics(test_query)
        if test_data:
            st.sidebar.json(test_data, expanded=False)
        else:
            st.sidebar.error("No response from Prometheus")

    # System Health
    st.sidebar.subheader("🏥 System Health")
    health_status = dashboard.check_api_health()
    if health_status["status"] == "healthy":
        st.sidebar.markdown('<p class="status-healthy">✅ API Healthy</p>', unsafe_allow_html=True)
        api_data = health_status["data"]
        st.sidebar.write(f"Model Loaded: {'✅' if api_data.get('model_loaded') else '❌'}")
        st.sidebar.write(f"Model Path: {api_data.get('model_path', 'N/A')}")
    else:
        st.sidebar.markdown('<p class="status-error">❌ API Offline</p>', unsafe_allow_html=True)
        st.sidebar.error(f"Error: {health_status.get('message', 'Unknown error')}")

    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 System Metrics Overview")
        tab1, tab2, tab3 = st.tabs(["Real-time Metrics", "Historical Data", "Prediction Analysis"])
        
        with tab1:
            metrics_col1, metrics_col2 = st.columns(2)
            with metrics_col1:
                # CPU Usage with multiple query options
                cpu_query = '100 * (1 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])))'
                cpu_data = dashboard.get_prometheus_metrics(cpu_query)
                display_metric_with_debug("CPU Usage", cpu_data, delta_ref=50)
                
                if debug_mode and cpu_data:
                    with st.expander("Debug CPU Query"):
                        st.code(cpu_query)
                        st.json(cpu_data, expanded=False)

                # Memory Usage
                mem_query = '(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100'
                mem_data = dashboard.get_prometheus_metrics(mem_query)
                display_metric_with_debug("Memory Usage", mem_data, delta_ref=60)
                
            with metrics_col2:
                # API Requests
                api_requests_data = dashboard.get_prometheus_metrics('api_requests_total')
                display_metric_with_debug("Total API Requests", api_requests_data, unit="")
                
                # Migration Predictions
                predictions_data = dashboard.get_prometheus_metrics('vm_migration_predictions_total')
                display_metric_with_debug("Migration Predictions", predictions_data, unit="")
        
        with tab2:
            st.subheader("📈 Historical Trends")
            time_range = st.selectbox("Select Time Range", ["1 hour", "6 hours", "24 hours"], index=0)
            selected_hours = {"1 hour": 1, "6 hours": 6, "24 hours": 24}[time_range]
            
            # Allow custom metric selection for historical data
            hist_query = st.text_input(
                "Metric Query", 
                value='100 * (1 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])))'
            )
            
            if st.button("Load Historical Data"):
                hist_data = dashboard.get_prometheus_range(hist_query, selected_hours)
                
                if hist_data and hist_data.get("data", {}).get("result"):
                    result = hist_data["data"]["result"][0]
                    timestamps = [datetime.fromtimestamp(float(point[0])) for point in result["values"]]
                    values = [float(point[1]) for point in result["values"]]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=timestamps, y=values, mode='lines+markers',
                        name='Metric Value',
                        line=dict(color='#667eea', width=2),
                        marker=dict(size=4)
                    ))
                    
                    fig.update_layout(
                        title=f"Metric Over Time: {hist_query[:30]}...",
                        xaxis_title="Time", yaxis_title="Value",
                        hovermode='x unified', template="plotly_white"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if debug_mode:
                        with st.expander("Debug Historical Data"):
                            st.json(hist_data, expanded=False)
                else:
                    st.error("Failed to load historical data")
                    if debug_mode and hist_data:
                        st.json(hist_data)

        with tab3:
            st.subheader("🔮 Prediction Analysis")
            if st.button("Generate Sample Analysis"):
                dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
                accuracy_data = np.random.normal(85, 10, len(dates))
                accuracy_data = np.clip(accuracy_data, 60, 99)
                
                df = pd.DataFrame({
                    'timestamp': dates,
                    'accuracy': accuracy_data,
                    'predictions_count': np.random.poisson(3, len(dates))
                })
                
                fig_acc = px.line(df, x='timestamp', y='accuracy', 
                                title='Prediction Accuracy Over Time',
                                labels={'accuracy': 'Accuracy (%)', 'timestamp': 'Time'})
                fig_acc.update_traces(line_color='#28a745')
                st.plotly_chart(fig_acc, use_container_width=True)
                
                fig_vol = px.bar(df, x='timestamp', y='predictions_count',
                               title='Prediction Volume Over Time',
                               labels={'predictions_count': 'Number of Predictions', 'timestamp': 'Time'})
                fig_vol.update_traces(marker_color='#667eea')
                st.plotly_chart(fig_vol, use_container_width=True)

    with col2:
        st.subheader("🎯 Migration Predictor")
        with st.form("prediction_form"):
            st.write("Enter system metrics to predict migration downtime:")
            cpu_load = st.slider("CPU Load (%)", 0.0, 100.0, 75.0, step=0.1)
            memory_usage = st.slider("Memory Usage (%)", 0.0, 100.0, 68.0, step=0.1)
            disk_io = st.slider("Disk I/O (MB/s)", 0.0, 1000.0, 45.0, step=0.1)
            network_bandwidth = st.slider("Network Bandwidth (Mbps)", 0.0, 1000.0, 850.0, step=1.0)
            
            predict_button = st.form_submit_button("🚀 Predict Migration Time")
            
            if predict_button:
                with st.spinner("Making prediction..."):
                    result = dashboard.make_prediction(cpu_load, memory_usage, disk_io, network_bandwidth)
                    
                    if result["status"] == "success":
                        pred_data = result["data"]
                        downtime = pred_data["predicted_downtime"]
                        confidence = pred_data["confidence"]
                        
                        st.success(f"**Predicted Downtime: {downtime:.2f} ms**")
                        st.info(f"Confidence: {confidence:.1%}")
                        
                        # Visual indicator
                        if downtime < 100:
                            st.success("✅ Excellent - Very low downtime expected")
                        elif downtime < 200:
                            st.warning("⚠️ Good - Moderate downtime expected")
                        else:
                            st.error("🚨 High - Significant downtime expected")
                        
                        # Recommendations
                        st.subheader("💡 Recommendations")
                        if cpu_load > 80:
                            st.write("• Reduce CPU load before migration")
                        if memory_usage > 80:
                            st.write("• High memory usage may increase downtime")
                        if network_bandwidth < 200:
                            st.write("• Low network bandwidth may cause delays")
                        if disk_io > 80:
                            st.write("• High disk I/O activity detected")
                            
                    else:
                        st.error(f"Prediction failed: {result.get('message', 'Unknown error')}")

        st.subheader("⚡ Quick Actions")
        if st.button("🔄 Simulate Migration"):
            with st.spinner("Running simulation..."):
                try:
                    response = requests.get(f"{dashboard.api_url}/simulate", timeout=10)
                    if response.status_code == 200:
                        st.success("Migration simulation started!")
                        st.json(response.json())
                    else:
                        st.error(f"Simulation failed: HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        st.subheader("📡 System Status")
        if health_status["status"] == "healthy":
            st.write(f"🤖 ML Model: {'✅ Loaded' if health_status['data'].get('model_loaded', False) else '❌ Not Loaded'}")
        
        prometheus_status = dashboard.get_prometheus_metrics("up{job='prometheus'}")
        if prometheus_status and prometheus_status.get("data", {}).get("result"):
            st.write("📊 Prometheus: ✅ Connected")
        else:
            st.write("📊 Prometheus: ❌ Disconnected")
        
        st.write(f"🔌 API: {'✅ Online' if health_status['status'] == 'healthy' else '❌ Offline'}")

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>VM Migration Predictor Dashboard v1.1 | Built with Streamlit + FastAPI + Prometheus</p>
        <p>Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
