# LLM Infra Platform Architecture

The system is designed as a production-grade, context-aware LLM infrastructure layer that provides a unified gateway for multiple AI providers (OpenAI, Anthropic, Google).

## Key Components

### 1. Unified Gateway (src/gateway/)
- FastAPI Core: OpenAI-compatible /v1/chat/completions endpoint.
- Middleware: Integrated budget guardrails and health-checking.
- Failover Logic: Multi-provider retry and downgrade mechanisms.

### 2. Core Decision Engine (src/core/)
- Scoring System: Multi-factor scoring (Health x Budget x Cost x Learning).
- Context-Aware Learning: Specialized performance tracking for distinct workloads (coding, translation, etc.).
- Probabilistic Selector: Weighted sampling for balanced exploration and exploitation.

### 3. Intelligence Layer (src/intelligence/)
- Workload Classifier: Heuristic-based classification of incoming messages.
- Insight Generation: Automated scanning for system anomalies and cost optimization opportunities.

### 4. Observability & Persistence (src/db/, src/monitoring/)
- Request Tracing: Detailed execution traces with multi-attempt recording.
- EMA-based Learning: Moving average reward calculation per provider/model/workload.
- SQLModel Persistence: SQLite-backed storage for health, learning, and insights.

## Request Lifecycle
1. Request Received: Gateway receives a chat completion request.
2. Workload Classification: WorkloadClassifier determines the task type (e.g., "coding").
3. Routing Decision: Selector computes scores for all healthy models, blending global performance with workload-specific rewards based on confidence.
4. Execution: Request is sent to the chosen provider via LiteLLM.
5. Outcome Processing:
   - Updates health metrics (success, latency, stability).
   - Computes Relative Reward (Actual performance vs. Benchmark).
   - Updates EMA-based ProviderLearning records.
6. Insight Generation: Background task periodically evaluates system performance for automated insights.
