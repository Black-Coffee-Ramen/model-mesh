# V3.6 Elite AI Infrastructure Layer

I have successfully upgraded the system from a deterministic router to an **Adaptive, Probabilistic, and Explainable AI Infrastructure Layer**.

## 🧠 Elite Adaptive Decision-Making
The system no longer simply picks the "best" model based on health. It now evaluates every request through a **Unified Scoring Engine**.

- **Unified Scoring Formula**:
  `final_score = health_score * budget_factor * cost_efficiency`
  - **Health Score**: Reliability, Latency, and Stability.
  - **Budget Factor**: Adaptive soft guardrails (1.0 down to 0.4 based on usage).
  - **Cost Efficiency**: Relative cost compared to the cheapest available model.

## ⚡ Probabilistic Routing (Exploration vs. Exploitation)
To prevent overfitting to a single provider and to adapt faster to real-time changes, I implemented **Weighted Probabilistic Sampling**.
- Models with higher scores are significantly more likely to be chosen.
- The system occasionally "explores" other healthy models to keep its performance metadata fresh.
- Squared scores are used as weights to ensure the "Exploit" bias remains strong for production stability.

## 📊 Routing Explainability Layer
Every decision is now transparent and auditable.
- **Score Breakdown**: For every request, we store the individual components (Health, Budget, Cost) and the final combined score.
- **Natural Language Reasoning**: The system generates human-readable reasons for its choice (e.g., "Severe budget pressure - favoring cheaper models", "Optimal cost efficiency").
- **Persistence**: These insights are stored in the `RequestTrace` table in the database.

## 📈 Elite Dashboard Upgrades
The dashboard has been enhanced with "Elite" level observability:
- **Score Breakdown Visualization**: Bar charts showing the latest decision's score components.
- **Reasoning Viewer**: Real-time display of the decision reasons for the latest trace.
- **Model Selection Mix**: A pie chart showing the distribution of models picked via probabilistic routing.
- **V3.6 Elite Trace Viewer**: Full JSON view of the explainability payload for every request.

---

## 🛠️ How to Verify V3.6 Elite

### 1. Run the Elite Simulation
```bash
python simulate_elite_v3_6.py
```
This script will:
- Send requests under low vs. high budget pressure.
- Demonstrate the probabilistic distribution of model picks over 10 requests.

### 2. Check the Dashboard
```bash
streamlit run src/dashboard/app.py
```
Monitor the **🧠 Elite V3.6 Explainability** section to see the real-time reasoning behind the decision engine.

## 📂 Key Files Added/Updated
- **`src/router/unified_scoring.py`**: The "brain" of the V3.6 decision logic.
- **`src/router/selector.py`**: Implementing probabilistic weighted sampling.
- **`src/gateway/middleware.py`**: Added adaptive budget factor logic.
- **`src/db/models.py`**: Added explainability fields to `RequestTrace`.
