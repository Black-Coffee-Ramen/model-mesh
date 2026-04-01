from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlmodel import select, func
from src.db.models import RequestTrace, RequestAttempt, ProviderHealth
from src.db.session import AsyncSessionLocal
from loguru import logger

async def start_trace(request_id: str, strategy: str) -> RequestTrace:
    async with AsyncSessionLocal() as session:
        trace = RequestTrace(id=request_id, strategy=strategy)
        session.add(trace)
        await session.commit()
        await session.refresh(trace)
        return trace

async def record_attempt(
    request_id: str,
    attempt_number: int,
    model: str,
    provider: str,
    status: str,
    latency_ms: float = 0.0,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    tokens: int = 0,
    cost: float = 0.0
):
    async with AsyncSessionLocal() as session:
        attempt = RequestAttempt(
            request_id=request_id,
            attempt_number=attempt_number,
            model=model,
            provider=provider,
            status=status,
            latency_ms=latency_ms,
            error_type=error_type,
            error_message=error_message,
            tokens_used=tokens,
            cost=cost
        )
        session.add(attempt)
        
        # Update provider health
        await update_provider_health(session, model, provider, status, latency_ms)
        
        await session.commit()
        return attempt

async def complete_trace(
    request_id: str,
    status: str,
    total_tokens: int,
    prompt_tokens: int,
    completion_tokens: int,
    total_cost: float,
    overall_latency_ms: float,
    workload_type: str = "general",
    is_cache_hit: bool = False,
    cache_savings: float = 0.0,
    routing_explanation: Dict[str, Any] = None,
    final_score: float = 0.0,
    model: Optional[str] = None,
    reward: float = 0.0,
    rejected_models: List[Dict[str, Any]] = None
):
    async with AsyncSessionLocal() as session:
        statement = select(RequestTrace).where(RequestTrace.id == request_id)
        result = await session.execute(statement)
        trace = result.scalar_one_or_none()
        
        if trace:
            trace.status = status
            trace.total_tokens = total_tokens
            trace.prompt_tokens = prompt_tokens
            trace.completion_tokens = completion_tokens
            trace.total_cost = total_cost
            trace.overall_latency_ms = overall_latency_ms
            trace.workload_type = workload_type
            trace.is_cache_hit = is_cache_hit
            trace.cache_savings = cache_savings
            trace.routing_explanation = routing_explanation or {}
            trace.rejected_models = rejected_models or []
            trace.final_score = final_score
            trace.model = model
            trace.reward = reward
            session.add(trace)
            await session.commit()

async def update_provider_health(session, model: str, provider: str, status: str, latency_ms: float):
    statement = select(ProviderHealth).where(ProviderHealth.model == model)
    result = await session.execute(statement)
    health = result.scalar_one_or_none()
    
    now = datetime.now()
    if not health:
        health = ProviderHealth(model=model, provider=provider)
    
    health.last_updated = now
    
    # Simple moving average logic or just recent failure check
    # In a real system, we'd query the last 10 minutes of attempts
    # For now, let's just mark status
    if status == "error":
        health.last_status = "degraded"
    else:
        health.last_status = "active"
        
    session.add(health)

async def get_recent_provider_health() -> List[ProviderHealth]:
    async with AsyncSessionLocal() as session:
        statement = select(ProviderHealth)
        result = await session.execute(statement)
        return result.scalars().all()
