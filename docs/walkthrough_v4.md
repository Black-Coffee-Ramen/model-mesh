# V4 Self-Improving AI Infrastructure Platform

I have successfully transformed the system from an adaptive router into a **Self-Improving AI Infrastructure Platform** that learns from real-world outcomes.

## 🔁 Post-Completion Feedback Loop
The system now treats every request as a learning opportunity.

- **Reward Function**: After a request completes, the `learning_engine` calculates a **Reward Score** ([-1, 1]):
  - **Success**: +0.5 baseline.
  - **Failures**: -1.0 penalty.
  - **Latency/Cost**: Penalties are applied if the performance deviates significantly from benchmarks.
- **Asynchronous Learning**: The feedback loop runs in a background task, ensuring that learning does not add any overhead to the user's response time.

## 🧠 Provider Performance Learning
I've added a **`ProviderLearning`** layer that persists the learned performance of every model.
- **Exponential Moving Average (EMA)**: The system uses EMA to update a model's `avg_reward`. This ensures the system:
  - Learns quickly from new successes/failures.
  - Remains stable against one-off outliers.
  - Forgets old performance over time as models and providers fluctuate.

## ⚙️ Learning-Adjusted Scoring (V4)
The unified scoring formula has been upgraded to be "Feedback-Aware":
`final_score = (health_score * budget_factor * cost_efficiency) * learning_factor`
- **Learning Factor**: A multiplier (0.5 to 1.5) derived from the model's historical `avg_reward`.
- **Dynamic Adaptability**: Models that perform well in *your specific environment* get a boost, while consistently slow or expensive models are naturally shifted down.

## ⚡ Exploration vs. Exploitation
The probabilistic selection now supports a **`temperature`** parameter:
- **T < 1.0 (Exploitation)**: The system aggressively favors the proven best models.
- **T > 1.0 (Exploration)**: The selection becomes more uniform, allowing the system to "test" other models to see if their performance has improved.

## 📊 Self-Improving Dashboard
The dashboard now explicitly visualizes the "Self-Improving" nature of the platform:
- **Provider Reward Leaderboard**: A ranking of models based on their *learned* performance, not just static specs.
- **Learning Confidence**: A scatter plot showing the relationship between request volume and reward stability.
- **Avg Reward Metric**: A high-level system-wide aggregate of performance.

---

## 🛠️ How to Verify V4 Learning

### 1. Run the V4 Simulation
```bash
python simulate_v4.py
```
This script will:
- Run a training batch of 20 requests to populate initial rewards.
- Demonstrate how the system's final decision is influenced by these learned rewards.

### 2. Monitor the Dashboard
```bash
streamlit run src/dashboard/app.py
```
Check the **"🧠 V4 Self-Improving Learning"** section. You'll see the rewards update in real-time as the simulation runs.

## 📂 Key Files Added/Updated
- **`src/router/learning_engine.py`**: The core logic for reward calculation and EMA tracking.
- **`src/router/engine.py`**: Integrating the asynchronous feedback loop.
- **`src/router/selector.py`**: Upgrading the selection math to include `learning_factor` and `temperature`.
- **`src/db/models.py`**: Added the `ProviderLearning` table.
