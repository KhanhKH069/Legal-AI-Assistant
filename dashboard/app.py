import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
import time

st.set_page_config(page_title="Legal AI Agent Dashboard", page_icon="🤖", layout="wide")

API_URL = os.getenv("API_URL", "http://localhost:8000")


def fetch_metrics():
    try:
        response = requests.get(f"{API_URL}/metrics/summary", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Cannot connect to Backend API at {API_URL}: {e}")
    return None


st.title("🤖 Paraline Legal AI Agent - Command Center")
st.markdown("Live metrics and real-time monitoring of AI Agents.")

metrics_data = fetch_metrics()

if metrics_data:
    # 1. Top Level KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Requests", metrics_data["total_requests"])
    col2.metric("Cache Hit Rate", f"{metrics_data['cache_hit_rate']}%")
    col3.metric("Avg Response Time", f"{metrics_data['avg_response_time_ms']} ms")
    uptime_min = round(metrics_data["uptime_seconds"] / 60, 1)
    col4.metric("Uptime", f"{uptime_min} mins")

    st.divider()

    # 2. Charts
    col_chart1, col_chart2 = st.columns(2)

    agent_stats = metrics_data.get("by_agent", {})
    if agent_stats:
        # Prepare DataFrames
        agents = []
        counts = []
        avg_times = []
        for agent_name, stats in agent_stats.items():
            agents.append(agent_name)
            counts.append(stats["count"])
            avg_times.append(stats["avg_ms"])

        df_workload = pd.DataFrame({"Agent": agents, "Count": counts})
        df_speed = pd.DataFrame({"Agent": agents, "Avg_MS": avg_times})

        with col_chart1:
            st.subheader("Workload Distribution")
            fig_pie = px.pie(df_workload, names="Agent", values="Count", hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_chart2:
            st.subheader("Average Response Time (ms)")
            fig_bar = px.bar(df_speed, x="Agent", y="Avg_MS", color="Agent")
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # 3. Live Logs
    st.subheader("Recent Agent Interactions (Live Log)")
    recent_requests = metrics_data.get("recent_requests", [])
    if recent_requests:
        df_logs = pd.DataFrame(recent_requests)
        # Convert timestamp to human readable
        df_logs["timestamp"] = pd.to_datetime(
            df_logs["timestamp"], unit="s"
        ).dt.strftime("%Y-%m-%d %H:%M:%S")
        df_logs = df_logs[
            [
                "timestamp",
                "user_id",
                "agent_name",
                "response_time_ms",
                "cached",
                "message_preview",
            ]
        ]
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("No requests recorded yet.")

    if st.button("Refresh Data"):
        st.rerun()

else:
    st.warning("Waiting for data... Please ensure the backend is running.")
    time.sleep(2)
    st.rerun()
