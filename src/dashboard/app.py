import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, select
from datetime import datetime, timedelta
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.db.models import RequestTrace, RequestAttempt, ProviderHealth, SystemInsight, ProviderLearning, AnomalyLog

# Database connection for Streamlit (Sync)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./llm_router.db").replace("sqlite+aiosqlite", "sqlite")
engine = create_engine(DATABASE_URL)

st.title("LLM Infrastructure Analytics")
st.sidebar.header("Settings")
refresh_rate = st.sidebar.slider("Auto-refresh (seconds)", 5, 60, 10)

# Helpers to load data
def load_data(table_model):
    with engine.connect() as conn:
        return pd.read_sql(select(table_model), conn)

def load_attempts():
    with engine.connect() as conn:
        return pd.read_sql(select(RequestAttempt), conn)

# --- Layout ---
traces_df = load_data(RequestTrace)
attempts_df = load_attempts()
health_df = load_data(ProviderHealth)
insights_df = load_data(SystemInsight)
anomalies_df = load_data(AnomalyLog)
learning_df = load_data(ProviderLearning)

col1, col2, col3, col4, col5 = st.columns(5)

if not traces_df.empty:
    with col1:
        st.metric("Total Requests", len(traces_df))
    with col2:
        success_rate = (traces_df['status'] == 'success').mean() * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col3:
        total_cost = traces_df['total_cost'].sum()
        st.metric("Total Cost", f"${total_cost:.4f}")
    with col4:
        # Calculate savings as difference between max cost for tokens and actual
        # For demo, we use the cache_savings field + a synthetic delta
        real_savings = traces_df['cache_savings'].sum()
        st.metric("Cost Savings", f"${real_savings:.4f}")
    with col5:
        avg_reward = traces_df['reward'].mean() if 'reward' in traces_df else 0
        st.metric("Avg Reward", f"{avg_reward:.2f}")

st.markdown("---")

# --- V4.1 Context-Aware Learning ---
st.header("V4.1 Context-Aware Intelligence")
if not learning_df.empty:
    lcol1, lcol2 = st.columns(2)
    with lcol1:
        st.subheader("Best Provider per Workload")
        # Identify the best (provider, model) for each workload_type based on avg_reward
        best_per_context = learning_df.loc[learning_df.groupby('workload_type')['avg_reward'].idxmax()]
        st.dataframe(best_per_context[['workload_type', 'provider', 'model', 'avg_reward', 'total_requests']], width="stretch")
        
    with lcol2:
        st.subheader("Contextual Reward Confidence")
        # Scatter of avg_reward vs confidence (log requests)
        learning_df['confidence'] = learning_df['total_requests'].apply(lambda x: min(1.0, 0.33 * (pd.Series(x).apply(lambda v: 0 if v <=0 else (np.log(v+1)))).iloc[0]))
        fig = px.scatter(learning_df, x='workload_type', y='avg_reward', size='confidence', color='model',
                         title="Contextual Rewards (Bubble size = Confidence)")
        st.plotly_chart(fig, width="stretch")

# --- Elite V3.6+ Explainability ---
st.header("Elite Decision Explainability")
if not traces_df.empty:
    c1, c2 = st.columns(2)
    with c1:
        total_savings = traces_df['cache_savings'].sum()
        st.metric("Total Savings", f"${total_savings:.4f}", help="Cost avoided via prompt caching")
    with c2:
        hit_rate = (traces_df['is_cache_hit']).mean() * 100
        st.metric("Cache Hit Rate", f"{hit_rate:.1f}%")

# --- Insights & Anomalies ---
st.header("AI Infrastructure Insights")
ci1, ci2 = st.columns([2, 1])
with ci1:
    if not insights_df.empty:
        for idx, row in insights_df.sort_values('timestamp', ascending=False).head(5).iterrows():
            st.info(f"[{row['category'].upper()}] {row['message']}")
    else:
        st.write("No insights generated yet.")
with ci2:
    st.subheader("Recent Anomalies")
    if not anomalies_df.empty:
        for idx, row in anomalies_df.sort_values('timestamp', ascending=False).head(3).iterrows():
            st.warning(f"[{row['type'].upper()}] {row['message']}")
    else:
        st.write("System stable.")

# --- Predictive Healthy Models ---
st.header("Predictive Health Scores")
if not health_df.empty:
    # Color coding based on health score
    def color_score(val):
        color = 'green' if val > 0.8 else 'orange' if val > 0.5 else 'red'
        return f'color: {color}'
    cols_to_show = ['model', 'provider', 'health_score', 'predicted_latency', 'failure_probability', 'last_updated']
    # Filter columns to only those that exist in health_df to avoid KeyError if migration isn't fully reflected
    available_cols = [c for c in cols_to_show if c in health_df.columns]
    st.dataframe(health_df[available_cols].style.map(color_score, subset=['health_score'] if 'health_score' in available_cols else []), width="stretch")

# --- Workload Intelligence ---
st.header("Workload Intelligence")
if not traces_df.empty:
    wc1, wc2 = st.columns(2)
    with wc1:
        st.subheader("Workload Distribution")
        fig = px.pie(traces_df, names='workload_type', hole=0.4)
        st.plotly_chart(fig, width="stretch")
    with wc2:
        st.subheader("Cost per Workload")
        fig = px.bar(traces_df.groupby('workload_type')['total_cost'].sum().reset_index(), x='workload_type', y='total_cost')
        st.plotly_chart(fig, width="stretch")

# --- Failure Analysis ---
st.header("Failure Analysis")
fa1, fa2 = st.columns(2)
with fa1:
    st.subheader("Error Distribution")
    errors_df = attempts_df[attempts_df['status'] == 'error']
    if not errors_df.empty:
        fig = px.pie(errors_df, names='error_type', hole=0.4)
        st.plotly_chart(fig, width="stretch")
    else:
        st.write("No errors recorded yet.")
with fa2:
    st.subheader("Failures per Provider")
    if not errors_df.empty:
        fig = px.bar(errors_df.groupby(['provider', 'error_type']).size().reset_index(name='count'), 
                     x='provider', y='count', color='error_type', barmode='stack',
                     labels={'count': 'Error Count'})
        st.plotly_chart(fig, width="stretch")
    else:
        st.write("No errors recorded yet.")

# --- V3.6 Elite Explainability ---
st.header("Elite V3.6 Explainability")
if not traces_df.empty:
    # Filter for non-empty explanations
    explained_traces = traces_df[traces_df['routing_explanation'].notnull()]
    if not explained_traces.empty:
        # 1. Score Breakdown Visualization
        latest_trace = explained_traces.sort_values('timestamp', ascending=False).iloc[0]
        expl = latest_trace['routing_explanation']
        
        if expl and 'scores' in expl:
            st.subheader(f"Latest Decision Breakdown: {latest_trace['id']}")
            s = expl['scores']
            
            # Radar/Bar Chart for scores
            score_data = pd.DataFrame({
                'Metric': ['Health', 'Budget Factor', 'Cost Efficiency', 'Final'],
                'Score': [s['health_score'], s['budget_factor'], s['cost_efficiency'], s['final_score']]
            })
            fig = px.bar(score_data, x='Metric', y='Score', color='Metric', range_y=[0, 1])
            st.plotly_chart(fig, width="stretch")
            
            st.write("**Reasoning:**")
            for r in expl.get('reasons', []):
                st.write(f"- {r}")

        # 2. Probabilistic Selection Distribution
        st.subheader("Model Selection Distribution")
        # How many times each model was picked
        if 'model' in traces_df.columns and not traces_df['model'].isnull().all():
            model_stats = traces_df.groupby('model').size().reset_index(name='count')
            fig = px.pie(model_stats, names='model', values='count', hole=0.4)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Insufficient longitudinal data for selection distribution.")

# --- Request Trace Viewer ---
st.header("Elite Trace Viewer")
if not traces_df.empty:
    selected_request_id = st.selectbox("Select Request ID", traces_df['id'].unique()[::-1])
    trace_details = traces_df[traces_df['id'] == selected_request_id].iloc[0]
    
    st.write(f"**Workload:** {trace_details['workload_type']} | **Final Score:** {trace_details.get('final_score', 0):.4f} | **Status:** {trace_details['status']}")
    
    # Show Explanation
    if trace_details['routing_explanation']:
        st.json(trace_details['routing_explanation'])
        
    relevant_attempts = attempts_df[attempts_df['request_id'] == selected_request_id].sort_values('attempt_number')
    st.dataframe(relevant_attempts[['attempt_number', 'model', 'provider', 'status', 'latency_ms', 'error_type', 'error_message']], width="stretch")

st.sidebar.markdown("---")
if st.sidebar.button("Run Insight Generation"):
    # This would ideally call the API endpoint
    st.sidebar.text("Call POST /system/analyze")
