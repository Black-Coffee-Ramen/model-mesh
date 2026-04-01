import random
from sqlmodel import Session, select
from src.db.session import sync_engine
from src.db.models import ProviderHealth, Budget, ProviderLearning
from loguru import logger
from typing import Optional, Tuple, List, Dict, Any

from src.core.health import compute_health_score
from src.gateway.middleware import get_budget_factor
from src.core.scoring import calculate_unified_score, calculate_cost_efficiency, generate_routing_explanation, calculate_confidence

# Mock cost table
MODEL_COSTS = {
    "gpt-3.5-turbo": 0.0005,
    "gpt-4o": 0.005,
    "claude-3-haiku-20240307": 0.00025,
    "claude-3-5-sonnet-20240620": 0.003,
    "gemini-1.5-pro-latest": 0.001
}

def select_best_provider_v4_1(user_id: str, strategy: str = "balanced", workload: str = "general", temperature: float = 0.8) -> Optional[Dict[str, Any]]:
    """
    Elite V4.1: Context-Aware, Self-Improving selector.
    """
    with Session(sync_engine) as session:
        providers = session.exec(select(ProviderHealth)).all()
        if not providers:
            return None

        budget_factor = get_budget_factor(user_id)
        
        # 1. Fetch Learning Data for this specific workload context
        specific_learning = {
            f"{r.provider}:{r.model}": (r.avg_reward, r.total_requests)
            for r in session.exec(
                select(ProviderLearning)
                .where(ProviderLearning.workload_type == workload)
            ).all()
        }
        
        # 2. Fetch General Learning Data for fallback
        general_learning = {
            f"{r.provider}:{r.model}": (r.avg_reward, r.total_requests)
            for r in session.exec(
                select(ProviderLearning)
                .where(ProviderLearning.workload_type == "general")
            ).all()
        }
        
        scored_candidates = []
        for p in providers:
            key = f"{p.provider}:{p.model}"
            
            # Context-Aware Logic
            reward_spec, count_spec = specific_learning.get(key, (0.0, 0))
            reward_gen, count_gen = general_learning.get(key, (0.0, 0))
            
            confidence = calculate_confidence(count_spec)
            effective_reward = (confidence * reward_spec) + ((1 - confidence) * reward_gen)
            
            health_score = compute_health_score(p.success_rate, p.avg_latency, p.stability_score, 0.5)
            cost_eff = calculate_cost_efficiency(p.model, MODEL_COSTS)
            
            final_score = calculate_unified_score(
                health_score=health_score, 
                budget_factor=budget_factor, 
                cost_efficiency=cost_eff,
                avg_reward=effective_reward,
                confidence=confidence
            )
            
            scored_candidates.append({
                "provider": p.provider,
                "model": p.model,
                "health_score": health_score,
                "cost_efficiency": cost_eff,
                "avg_reward": effective_reward,
                "confidence": confidence,
                "final_score": final_score
            })

        if not scored_candidates:
            return None

        # 3. Probabilistic Selection with Elite Epsilon-Greedy Exploration
        EPSILON = 0.2 # 20% Chance to explore for learning
        
        # Sort candidates for rejected analysis
        sorted_candidates = sorted(scored_candidates, key=lambda x: x["final_score"], reverse=True)
        
        if random.random() < EPSILON:
            chosen_candidate = random.choice(scored_candidates)
            explanation = {"reasons": ["Elite Exploration: Random choice for system learning"], "workload_target": workload}
            logger.info(f"V4.1 EXPLORATION: Picked {chosen_candidate['model']} at random.")
            # For exploration, rejection reasoning is simple: "Exploration system picked another model"
            rejected_models = [
                {"model": c["model"], "reason": "Higher priority: System exploration"} 
                for c in scored_candidates if c["model"] != chosen_candidate["model"]
            ]
        else:
            # Traditional Weighted Selection
            weights = [c["final_score"]**(1/temperature) for c in scored_candidates]
            weights = [max(w, 0.001) for w in weights]
            
            chosen_candidate = random.choices(scored_candidates, weights=weights, k=1)[0]
            
            # 4. Generate Explainability
            explanation = generate_routing_explanation(
                model=chosen_candidate["model"],
                health_score=chosen_candidate["health_score"],
                budget_factor=budget_factor,
                cost_efficiency=chosen_candidate["cost_efficiency"],
                final_score=chosen_candidate["final_score"],
                avg_reward=chosen_candidate["avg_reward"],
                confidence=chosen_candidate["confidence"],
                workload_type=workload
            )

            # 5. Elite Explainability: Rejected Models
            rejected_models = []
            for cand in sorted_candidates:
                if cand["model"] == chosen_candidate["model"]:
                    continue
                
                # Determine primary reason for rejection
                reason = "Lower overall score"
                if cand["cost_efficiency"] < chosen_candidate["cost_efficiency"] - 0.2:
                    reason = "Significantly higher cost"
                elif cand["health_score"] < chosen_candidate["health_score"] - 0.1:
                    reason = "Lower service reliability"
                elif cand["avg_reward"] < chosen_candidate["avg_reward"] - 0.3:
                    reason = "Sub-optimal historical reward for this workload"
                elif cand["confidence"] < chosen_candidate["confidence"] - 0.5:
                    reason = "Lower system confidence for this specific workload"
                
                rejected_models.append({
                    "model": cand["model"],
                    "reason": reason,
                    "score": round(cand["final_score"], 4)
                })
        
        return {
            "provider": chosen_candidate["provider"],
            "model": chosen_candidate["model"],
            "explanation": explanation,
            "rejected_models": rejected_models,
            "final_score": chosen_candidate["final_score"]
        }

def get_cheapest_provider() -> Optional[Tuple[str, str]]:
    """Return the model with the lowest tier/cost"""
    return "google", "gemini-1.5-pro-latest"
