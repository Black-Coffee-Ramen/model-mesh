from typing import List, Dict, Any
from sqlmodel import select, func
from src.db.models import RequestTrace, RequestAttempt
from src.db.session import AsyncSessionLocal
import litellm

class CostIntelligenceEngine:
    async def get_cost_efficiency_report(self):
        """
        Analyze recent requests to find cost saving opportunities.
        """
        async with AsyncSessionLocal() as session:
            # Get successful requests from last 24h
            statement = select(RequestTrace).where(RequestTrace.status == "success")
            result = await session.execute(statement)
            traces = result.scalars().all()
            
            total_actual_cost = sum(t.total_cost for t in traces)
            total_optimal_cost = 0.0
            
            savings_opportunities = []
            
            for t in traces:
                # Simple optimal cost: what if we used gpt-3.5-turbo for everything?
                # In a real system, we'd check if the query complexity actually required 
                # a premium model.
                
                # Assume gpt-3.5-turbo-0125 rates roughly $0.0005 / 1K tokens
                optimal_rate = 0.0005 / 1000
                optimal_cost = t.total_tokens * optimal_rate
                total_optimal_cost += optimal_cost
                
                if t.total_cost > optimal_cost * 2:
                    savings_opportunities.append({
                        "request_id": t.id,
                        "actual_cost": t.total_cost,
                        "optimal_cost": optimal_cost,
                        "potential_savings": t.total_cost - optimal_cost
                    })

            return {
                "total_requests_analyzed": len(traces),
                "total_actual_cost": total_actual_cost,
                "total_optimal_cost": total_optimal_cost,
                "potential_total_savings": max(0, total_actual_cost - total_optimal_cost),
                "savings_percentage": (1 - (total_optimal_cost / total_actual_cost)) * 100 if total_actual_cost > 0 else 0
            }

    async def detect_inefficient_usage(self) -> List[str]:
        insights = []
        report = await self.get_cost_efficiency_report()
        
        if report["savings_percentage"] > 30:
            insights.append(f"Switching to cheaper models for simple queries can save ~{report['savings_percentage']:.1f}% cost.")
            
        # Detect repeated prompts (heuristic: check most common prompt token counts)
        # In a real system, we'd hash the prompt content
        
        return insights

cost_engine = CostIntelligenceEngine()
