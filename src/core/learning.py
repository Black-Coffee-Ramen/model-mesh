from sqlmodel import Session, select
from src.db.session import sync_engine
from src.db.models import ProviderLearning, RequestTrace
from datetime import datetime, timezone
from loguru import logger

# Cost/Latency benchmarks per model (V4.1 Relative Reward)
MODEL_BENCHMARKS = {
    "gpt-3.5-turbo": {"cost": 0.0005, "latency": 1000},
    "gpt-4o": {"cost": 0.005, "latency": 5000},
    "claude-3-haiku-20240307": {"cost": 0.00025, "latency": 800},
    "claude-3-5-sonnet-20240620": {"cost": 0.003, "latency": 3000},
    "gemini-1.5-pro-latest": {"cost": 0.001, "latency": 2000}
}

def calculate_reward(status: str, latency_ms: float, cost: float, model: str) -> float:
    """
    Elite V4.1 Context-Aware: reward = f(success, latency, cost).
    Higher is better.
    """
    if status != "success":
        return -1.0
        
    # Improved formula as suggested for demo realism
    # reward = 0.5 * success + 0.3 * (1 - latency_ms/1500) + 0.2 * (1 - cost/0.02)
    success_val = 1.0
    latency_score = 1.0 - (latency_ms / 1500.0)
    cost_score = 1.0 - (cost / 0.02)
    
    total_reward = (0.5 * success_val) + (0.3 * latency_score) + (0.2 * cost_score)
    return round(max(-1.0, min(1.0, total_reward)), 4)

def update_provider_learning(provider: str, model: str, reward: float, request_id: str, workload: str = "general"):
    """
    Update context-aware reward for (provider, model, workload).
    """
    alpha = 0.2 # Smoothing factor for EMA
    
    with Session(sync_engine) as session:
        # 1. Update Specific Contextual Record
        record = session.exec(
            select(ProviderLearning)
            .where(ProviderLearning.provider == provider)
            .where(ProviderLearning.model == model)
            .where(ProviderLearning.workload_type == workload)
        ).first()
        
        if record:
            record.avg_reward = ((1 - alpha) * record.avg_reward) + (alpha * reward)
            record.total_requests += 1
            record.last_updated = datetime.now(timezone.utc)
        else:
            record = ProviderLearning(
                provider=provider, model=model, workload_type=workload,
                avg_reward=reward, total_requests=1,
                last_updated=datetime.now(timezone.utc)
            )
        
        # 3. Always update "general" record as well for global fallback/baseline
        if workload != "general":
            general_record = session.exec(
                select(ProviderLearning)
                .where(ProviderLearning.provider == provider)
                .where(ProviderLearning.model == model)
                .where(ProviderLearning.workload_type == "general")
            ).first()
            if general_record:
                general_record.avg_reward = ((1 - alpha) * general_record.avg_reward) + (alpha * reward)
                general_record.total_requests += 1
                session.add(general_record)
        
        session.add(record)
        session.commit()
