from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, JSON, Relationship

class RequestTrace(SQLModel, table=True):
    id: str = Field(primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    strategy: str
    workload_type: str = "general" # simple, coding, reasoning, extraction
    is_cache_hit: bool = False
    cache_savings: float = 0.0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    status: str = "pending" # success, failed
    overall_latency_ms: float = 0.0
    model: Optional[str] = Field(default=None)
    
    # Elite V3.6 Explainability
    routing_explanation: Dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
    rejected_models: List[Dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    final_score: float = 0.0
    
    # Self-Improving V4 Learning
    reward: float = 0.0
    
    attempts: List["RequestAttempt"] = Relationship(back_populates="request")

class ProviderLearning(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    model: str
    workload_type: str = Field(default="general", index=True) # coding, reasoning, extraction, simple, etc.
    avg_reward: float = 0.0
    total_requests: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class RequestAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: str = Field(foreign_key="requesttrace.id")
    attempt_number: int
    model: str
    provider: str
    status: str # success, error
    error_type: Optional[str] = None # rate_limit, timeout, provider_error, etc.
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)

    request: RequestTrace = Relationship(back_populates="attempts")

class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(index=True)
    daily_limit: float
    monthly_limit: float
    current_daily_spend: float = 0.0
    current_monthly_spend: float = 0.0
    last_reset: datetime = Field(default_factory=datetime.utcnow)


class ProviderHealth(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    model: str
    success_rate: float = 1.0
    failure_rate: float = 0.0
    avg_latency: float = 0.0
    stability_score: float = 1.0
    health_score: float = 1.0
    predicted_latency: float = 0.0
    failure_probability: float = 0.0
    last_status: str = Field(default="active")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class PromptCache(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_hash: str = Field(index=True)
    response_json: str
    model: str
    tokens: int
    estimated_cost: float
    timestamp: datetime = Field(default_factory=datetime.now)

class AnomalyLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    type: str # latency, cost, failure
    severity: str # info, warning, critical
    message: str
    observed_value: float
    threshold_value: float

class SystemInsight(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    category: str # cost, performance, reliability
    severity: str # info, warning, critical
    message: str
    data: Dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
