import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlmodel import select
from src.db.models import RequestAttempt, ProviderHealth
from src.db.session import AsyncSessionLocal
from loguru import logger

class ScoringEngine:
    async def get_health_score(self, model: str) -> float:
        """
        Calculate a health score for a given model based on:
        - Recent success rate (failure_rate)
        - Latency stability (predicted_latency)
        - Historical performance
        """
        async with AsyncSessionLocal() as session:
            # Get last 50 attempts for this model
            statement = select(RequestAttempt).where(RequestAttempt.model == model).order_by(RequestAttempt.timestamp.desc()).limit(50)
            result = await session.execute(statement)
            attempts = result.scalars().all()
            
            if not attempts:
                return 1.0 # Default High
            
            # 1. Success Rate Score
            successes = [1 if a.status == "success" else 0 for a in attempts]
            success_rate = np.mean(successes)
            
            # 2. Latency Stability Score
            latencies = [a.latency_ms for a in attempts if a.status == "success"]
            latency_score = 1.0
            if latencies:
                avg_latency = np.mean(latencies)
                std_latency = np.std(latencies)
                stability_ratio = std_latency / avg_latency if avg_latency > 0 else 0
                latency_score = max(0.0, 1.0 - stability_ratio)
            
            # 3. Trend analysis (Weighted: more recent is more important)
            recent_successes = successes[:10]
            recent_rate = np.mean(recent_successes)
            
            health_score = (success_rate * 0.6) + (latency_score * 0.25) + (recent_rate * 0.15)
            
            # Update Provider Health summary
            health_statement = select(ProviderHealth).where(ProviderHealth.model == model)
            h_result = await session.execute(health_statement)
            health_record = h_result.scalar_one_or_none()
            
            if health_record:
                health_record.health_score = health_score
                health_record.predicted_latency = np.mean(latencies) if latencies else 0.0
                health_record.failure_probability = 1.0 - recent_rate
                health_record.last_updated = datetime.now()
                session.add(health_record)
                await session.commit()
                
            return health_score

scoring_engine = ScoringEngine()

def calculate_cost_efficiency(model: str, model_costs: Dict[str, float]) -> float:
    """
    Elite V3.6: cost_efficiency = min(provider_costs) / provider_cost
    Higher is better (cheaper).
    """
    provider_cost = model_costs.get(model, 1.0)
    min_cost = min(model_costs.values())
    if provider_cost == 0:
        return 1.0
    return min_cost / provider_cost

def calculate_confidence(total_requests: int) -> float:
    """
    V4.1: Log-based confidence metric.
    """
    if total_requests <= 0:
        return 0.0
    return min(1.0, math.log(total_requests + 1) / 3.0)

def calculate_unified_score(
    health_score: float, 
    budget_factor: float, 
    cost_efficiency: float,
    avg_reward: float = 0.0,
    confidence: float = 0.0
) -> float:
    """
    Elite V4.1 Context-Aware decision formula.
    """
    reward_factor = 1.0 + (avg_reward * 0.5)
    learning_factor = (confidence * reward_factor) + ((1 - confidence) * 1.0)
    
    # Balanced cost logic: Cost is a nudger, not a dominator
    # (0.7 + 0.3 * cost_eff) ensures cost only affects 30% of the base score
    balanced_cost = 0.7 + (0.3 * cost_efficiency)
    
    base_score = health_score * budget_factor * balanced_cost
    return round(base_score * learning_factor, 4)

def generate_routing_explanation(
    model: str,
    health_score: float,
    budget_factor: float,
    cost_efficiency: float,
    final_score: float,
    learning_factor: float = 1.0,
    avg_reward: float = 0.0,
    confidence: float = 0.0,
    workload_type: str = "general"
) -> Dict[str, Any]:
    """
    Generate structured explainability data for V4.1 context-aware decision.
    """
    reasons = []
    
    if confidence > 0.5:
        if avg_reward > 0.2:
            reasons.append(f"High historical reward for {workload_type} tasks (Rel. Reward: {avg_reward:.2f})")
        elif avg_reward < -0.2:
            reasons.append(f"Performance bottleneck detected for {workload_type} workload")
    else:
        reasons.append(f"Insufficient historical data for {workload_type} - using global baseline")

    if health_score > 0.8:
        reasons.append("High service reliability")
    elif health_score < 0.5:
        reasons.append("Low health score (risky choice)")
        
    if budget_factor < 0.7:
        reasons.append("Severe budget pressure - favoring cheaper models")
        
    if cost_efficiency > 0.9:
        reasons.append("Optimal cost efficiency")
    else:
        reasons.append("Premium model selection")

    return {
        "chosen_model": model,
        "workload_target": workload_type,
        "scores": {
            "health_score": round(health_score, 4),
            "budget_factor": round(budget_factor, 4),
            "cost_efficiency": round(cost_efficiency, 4),
            "learning_factor": round(learning_factor, 4),
            "confidence": round(confidence, 4),
            "final_score": round(final_score, 4)
        },
        "reasons": reasons
    }
