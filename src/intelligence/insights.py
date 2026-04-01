from datetime import datetime, timedelta
from sqlmodel import select, func
from src.db.models import RequestAttempt, ProviderHealth, SystemInsight
from src.db.session import AsyncSessionLocal
from src.intelligence.cost import cost_engine
from loguru import logger

class InsightGenerationLayer:
    async def generate_system_insights(self):
        """
        Periodically scan the system for performance and health anomalies.
        """
        insights = []
        
        async with AsyncSessionLocal() as session:
            # 1. Performance Insights (Latency Spikes)
            # Scan last 15 minutes of attempts vs last 24h
            recent_threshold = datetime.now() - timedelta(minutes=15)
            
            # Simple latency spike check
            statement = select(ProviderHealth)
            result = await session.execute(statement)
            health_records = result.scalars().all()
            
            for health in health_records:
                if health.last_status == "degraded":
                    insights.append(SystemInsight(
                        category="reliability",
                        severity="warning",
                        message=f"Stability issues detected for model: {health.model} ({health.provider})."
                    ))
                
                # In a real system, we'd check avg_latency_10m vs historical
                    
            # 2. Cost Insights
            cost_insights = await cost_engine.detect_inefficient_usage()
            for msg in cost_insights:
                insights.append(SystemInsight(
                    category="cost",
                    severity="info",
                    message=msg
                ))
            
            # 3. Persistence
            for ins in insights:
                # Check for duplicate recent identical insight
                existing_statement = select(SystemInsight).where(
                    SystemInsight.message == ins.message,
                    SystemInsight.timestamp > datetime.now() - timedelta(hours=1)
                )
                existing = await session.execute(existing_statement)
                if not existing.scalar_one_or_none():
                    session.add(ins)
            
            await session.commit()
            return insights

    async def get_latest_insights(self, limit: int = 5):
        async with AsyncSessionLocal() as session:
            statement = select(SystemInsight).order_by(SystemInsight.timestamp.desc()).limit(limit)
            result = await session.execute(statement)
            return result.scalars().all()

insight_layer = InsightGenerationLayer()
