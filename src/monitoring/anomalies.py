import numpy as np
from datetime import datetime, timedelta
from sqlmodel import select, func
from src.db.models import RequestTrace, RequestAttempt, AnomalyLog
from src.db.session import AsyncSessionLocal
from loguru import logger

class AnomalyDetector:
    def __init__(self):
        self.latency_threshold_ms = 5000.0
        self.cost_threshold_hourly = 10.0 # $10/hr
        self.failure_threshold_rate = 0.2 # 20%

    async def check_for_anomalies(self):
        """
        Scan recent request data for statistically significant spikes.
        """
        async with AsyncSessionLocal() as session:
            now = datetime.now()
            last_5m = now - timedelta(minutes=5)
            
            # 1. Latency Anomaly Detection
            statement = select(RequestTrace).where(RequestTrace.timestamp > last_5m)
            result = await session.execute(statement)
            recent_traces = result.scalars().all()
            
            if len(recent_traces) > 10:
                latencies = [t.overall_latency_ms for t in recent_traces]
                avg = np.mean(latencies)
                std = np.std(latencies)
                
                # Anomaly if avg > threshold or many outliers (3 sigma)
                if avg > self.latency_threshold_ms:
                    await self._record_anomaly(session, "latency", "warning", 
                                             f"Average latency spike: {avg:.0f}ms", avg, self.latency_threshold_ms)

            # 2. Failure Burst Detection
            stmt_attempts = select(RequestAttempt).where(RequestAttempt.timestamp > last_5m)
            res_attempts = await session.execute(stmt_attempts)
            recent_attempts = res_attempts.scalars().all()
            
            if len(recent_attempts) > 5:
                fail_rate = len([a for a in recent_attempts if a.status == "error"]) / len(recent_attempts)
                if fail_rate > self.failure_threshold_rate:
                    await self._record_anomaly(session, "failure", "critical", 
                                             f"High failure rate detected: {fail_rate*100:.0f}%", fail_rate, self.failure_threshold_rate)

            # 3. Cost Spike Detection
            stmt_cost = select(func.sum(RequestTrace.total_cost)).where(RequestTrace.timestamp > now - timedelta(hours=1))
            res_cost = await session.execute(stmt_cost)
            hourly_cost = res_cost.scalar() or 0.0
            if hourly_cost > self.cost_threshold_hourly:
                await self._record_anomaly(session, "cost", "info", 
                                         f"Hourly cost spike: ${hourly_cost:.2f}", hourly_cost, self.cost_threshold_hourly)

            await session.commit()

    async def _record_anomaly(self, session, type: str, severity: str, message: str, value: float, threshold: float):
        # Avoid redundant logs
        check_stmt = select(AnomalyLog).where(
            AnomalyLog.type == type, 
            AnomalyLog.timestamp > datetime.now() - timedelta(minutes=15)
        )
        existing = await session.execute(check_stmt)
        if not existing.scalar_one_or_none():
            logger.warning(f"ANOMALY DETECTED: {message}")
            log = AnomalyLog(
                type=type, severity=severity, message=message, 
                observed_value=value, threshold_value=threshold
            )
            session.add(log)

anomaly_detector = AnomalyDetector()
