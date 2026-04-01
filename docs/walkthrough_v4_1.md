# V4.1 Context-Aware Self-Improving Platform

I have successfully upgraded the system to **V4.1**, transforming it into a context-aware intelligence layer that learns the optimal provider for every specific workload type (coding, reasoning, extraction, etc.).

## 🧠 Workload-Specific Intelligence
The system no longer just asks "Which provider is best overall?" but "Which provider is best for **this specific task**?"

- **Contextual Learning**: The `ProviderLearning` table now tracks `avg_reward` and `total_requests` independently for every `(provider, model, workload_type)` triplet.
- **Global Fallback**: The system still maintains a "general" baseline context to ensure stability when switching to a completely new or rare workload.

## ⚖️ Relative Reward (Actual vs. Expected)
I've implemented a **Relative Reward** system. The reward is no longer an absolute score but a comparison against model-tier benchmarks.
- **Cheap Models**: High reward when they achieve low latency (exceeding expectations).
- **Premium Models**: Higher bar for reward; they must provide exceptional speed and reliability to justify their cost.
- **Formula**: `reward = (0.6 * relative_latency) + (0.4 * relative_cost)`.

## 📈 Log-Based Confidence Weighting
To prevent "Overfitting" or "Greedy" behavior with limited data, I've introduced a **Log-Based Confidence** metric.
- **The Formula**: `confidence = log(count + 1) / 3.0` (capped at 1.0).
- **The Weighting**: 
  - **Low Confidence**: System behaves neutrally, relying on global health scores.
  - **High Confidence**: System heavily weights the learned contextual reward, aggressively favoring proven providers for that workload.

## 📊 Contextual Dashboard
The dashboard has been completely revamped for contextual intelligence:
- **Best Provider per Workload**: A dynamic table showing the top-ranked model for every detected workload type.
- **Confidence Heatmap**: A scatter plot where bubble sizes represent how much "experience" the system has accumulated for each context.
- **Enhanced Explainability**: Decision logs now include the `workload_target` and the `confidence` score used in the selection.

---

## 🛠️ How to Verify V4.1

### 1. Initialize the V4.1 Database
The schema has changed. Run the initialization script to update your local DB:
```bash
python init_db_v4.py
```

### 2. Run the Contextual Simulation
```bash
python simulate_v4_1.py
```
This script runs targeted training batches for specific workloads (coding, translation, etc.) and demonstrates how the selection confidence grows independently for each.

### 3. Explore the Intelligence
Open the dashboard to see the new **Context-Aware Intelligence** tab:
```bash
streamlit run src/dashboard/app.py
```

## 📂 Key Changes
- **`src/db/models.py`**: Added `workload_type` to `ProviderLearning`.
- **`src/router/learning_engine.py`**: Added model benchmarks and relative reward logic.
- **`src/router/unified_scoring.py`**: Integrated the log-based confidence engine.
- **`src/router/selector.py`**: Refactored for contextual fallback and blending.
