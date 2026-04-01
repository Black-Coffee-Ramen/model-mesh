from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import litellm
from loguru import logger

@dataclass
class UsageRecord:
    request_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.now)

class ObservabilityEngine:
    def __init__(self):
        self.usage_history: List[UsageRecord] = []
        logger.info("ObservabilityEngine initialized")

    def record_usage(self, response_obj: Any, latency_ms: float, request_id: str = "unknown"):
        """
        Extract usage and cost from a LiteLLM response object and record it.
        """
        try:
            model = response_obj.get("model", "unknown")
            usage = response_obj.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            # Use LiteLLM to calculate cost
            cost = litellm.completion_cost(completion_response=response_obj)
            
            record = UsageRecord(
                request_id=request_id,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                latency_ms=latency_ms
            )
            
            self.usage_history.append(record)
            logger.info(f"Recorded usage for {model}: {total_tokens} tokens, ${cost:.6f}")
            return record
        except Exception as e:
            logger.error(f"Error recording usage: {str(e)}")
            return None

    def get_total_usage(self) -> Dict[str, Any]:
        total_tokens = sum(r.total_tokens for r in self.usage_history)
        total_cost = sum(r.cost for r in self.usage_history)
        return {
            "total_requests": len(self.usage_history),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "history_count": len(self.usage_history)
        }

    def get_usage_by_model(self) -> Dict[str, Dict[str, Any]]:
        by_model = {}
        for r in self.usage_history:
            if r.model not in by_model:
                by_model[r.model] = {"tokens": 0, "cost": 0, "count": 0, "total_latency_ms": 0}
            by_model[r.model]["tokens"] += r.total_tokens
            by_model[r.model]["cost"] += r.cost
            by_model[r.model]["count"] += 1
            by_model[r.model]["total_latency_ms"] += r.latency_ms
        
        # Calculate averages
        for model in by_model:
            count = by_model[model]["count"]
            by_model[model]["avg_latency_ms"] = by_model[model]["total_latency_ms"] / count if count > 0 else 0
            
        return by_model

metrics_engine = ObservabilityEngine()
