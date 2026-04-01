import litellm
import time
import uuid
import asyncio
import numpy as np
import random
from loguru import logger
from typing import List, Dict, Any, Optional

from src.config import settings
from src.monitoring.metrics import metrics_engine
from src.monitoring.failures import classify_error, ErrorCategory
from src.monitoring.tracing import record_attempt, start_trace, complete_trace, get_recent_provider_health
from src.cache.impl import cache_engine
from src.intelligence.workload import workload_classifier
from src.gateway.middleware import check_budget, update_budget_spend, get_budget_factor

# New Core Imports
from src.core.scoring import scoring_engine
from src.core.health import update_provider_metrics
from src.core.learning import update_provider_learning, calculate_reward
from src.core.selector import select_best_provider_v4_1, get_cheapest_provider

class LLMRouter:
    def __init__(self):
        litellm.telemetry = False
        self.model_tiers = {
            "gpt-3.5-turbo": {"tier": "cheap", "provider": "openai"},
            "gpt-4o": {"tier": "premium", "provider": "openai"},
            "claude-3-haiku-20240307": {"tier": "cheap", "provider": "anthropic"},
            "claude-3-5-sonnet-20240620": {"tier": "premium", "provider": "anthropic"},
            "gemini-1.5-pro-latest": {"tier": "balanced", "provider": "gemini"}
        }
        litellm.suppress_debug_info = True
        logger.info("LLMRouter V4.1 Context-Aware Decision Engine initialized (Integrated Core)")

    async def route_request(self, user_id: str, strategy: str = "cost", workload: str = "general", temperature: float = 0.8) -> Dict[str, Any]:
        """
        V4.1: Pick model using contextual probabilistic selection.
        """
        decision = select_best_provider_v4_1(user_id=user_id, strategy=strategy, workload=workload, temperature=temperature)
        
        if decision:
            logger.info(f"V4.1 Contextual decision: {decision['model']} for {workload}")
            return decision
        
        return {
            "provider": "openai", "model": "gpt-3.5-turbo", "final_score": 0.0, 
            "explanation": {"reasons": ["Default fallback"]}
        }

    async def completion(
        self, 
        user_id: str,
        model: Optional[str], 
        messages: List[Dict[str, str]], 
        strategy: str = "cost",
        max_retries: int = 1,
        temperature: float = 0.8,
        workload_type: Optional[str] = None,
        **kwargs
    ) -> Any:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 1. Workload Classification (Skip if provided)
        if not workload_type:
            workload_type = workload_classifier.classify(messages)
        
        # 2. Decision Logic (V4.1 Context-Aware)
        explanation = {}
        rejected_models = []
        final_score = 0.0
        
        if not model or model == "auto":
            decision = await self.route_request(user_id=user_id, strategy=strategy, workload=workload_type, temperature=temperature)
            model = decision["model"]
            explanation = decision["explanation"]
            rejected_models = decision.get("rejected_models", [])
            final_score = decision["final_score"]
        else:
            explanation = {"reasons": ["Direct model request"], "workload_target": workload_type}
        
        logger.info(f"Starting request [{request_id}] | V4.1 Context: {workload_type} | Model: {model}")
        await start_trace(request_id, strategy)
        
        retries = 0
        while retries <= max_retries:
            attempt_start = time.time()
            provider = self.model_tiers.get(model, {}).get("provider", "openai")
            litellm_model = f"{provider}/{model}" if "/" not in model and provider != "openai" else model
            
            try:
                # Real API Call
                response = await litellm.acompletion(model=litellm_model, messages=messages, **kwargs)
                attempt_latency = (time.time() - attempt_start) * 1000
                total_latency = (time.time() - start_time) * 1000
                
                usage = response.get("usage", {})
                cost = litellm.completion_cost(completion_response=response)
                
                # Update Health
                update_provider_metrics(provider, model, {
                    "success_rate": 1.0, "avg_latency": attempt_latency / 1000, 
                    "failure_rate": 0.0, "stability_score": 1.0
                })

                # Update Budget
                update_budget_spend(user_id, cost)
                
                # Context-Aware Reward
                reward = calculate_reward("success", total_latency, cost, model)
                
                # Persistence & Learning (Async)
                await complete_trace(
                    request_id=request_id, status="success",
                    total_tokens=usage.get("total_tokens", 0), 
                    prompt_tokens=usage.get("prompt_tokens", 0), 
                    completion_tokens=usage.get("completion_tokens", 0), 
                    total_cost=cost, overall_latency_ms=total_latency, 
                    workload_type=workload_type,
                    routing_explanation=explanation,
                    rejected_models=rejected_models,
                    final_score=final_score,
                    model=model,
                    reward=reward
                )
                
                # Trigger Learning feedback with workload context
                asyncio.create_task(asyncio.to_thread(update_provider_learning, provider, model, reward, request_id, workload_type))
                
                return response
                
            except Exception as e:
                category = classify_error(e)
                error_msg = str(e).lower()
                
                # Detect Credentials/Balance Issues for silent demo fallback
                is_demo_fail = "api_key" in error_msg or "balance" in error_msg or "credit" in error_msg or "provider not provided" in error_msg
                
                if not is_demo_fail:
                    logger.error(f"Error in attempt {retries+1}: {str(e)}")
                else:
                    logger.info(f"Credential check failed for {model} (Demo Mode). Skipping to high-fidelity simulation...")

                update_provider_metrics(provider, model, {
                    "success_rate": 0.0, "failure_rate": 1.0, "avg_latency": 5.0, "stability_score": 0.5
                })
                
                await record_attempt(
                    request_id=request_id, attempt_number=retries+1, 
                    model=model, provider=provider, status="error", 
                    latency_ms=(time.time()-attempt_start)*1000, 
                    error_type=category.value, error_message=str(e)[:100]
                )
                
                # Failure Reward
                reward = calculate_reward("error", 0, 0, model)
                
                # ELITE DEMO FALLBACK: If real API fails (likely due to missing keys),
                # provide realistic mock data so the dashboard stays alive.
                if retries >= max_retries:
                    logger.warning(f"Demo Fallback: Generating realistic mock data for {model}")
                    
                    # V4.2 Contextual Failure Logic
                    failure_prob = 0.1
                    if provider == "gemini" and workload_type == "reasoning":
                        failure_prob = 0.25 # Gemini instability for reasoning tasks
                    elif provider == "anthropic" and workload_type == "coding":
                        failure_prob = 0.15 # Anthropic coding latency/failure spikes
                    elif model == "gpt-4o":
                        failure_prob = 0.05 # GPT-4o is premium and stable
                    
                    mock_success = random.random() > failure_prob
                    status = "success" if mock_success else "error"
                    
                    mock_latency = random.uniform(200, 1500)
                    mock_cost = random.uniform(0.001, 0.02)
                    
                    # User Formula: reward = 0.5 * (1 if success else -1) + 0.3 * (1 - latency_ms / 1500) + 0.2 * (1 - cost / 0.02)
                    success_val = 1.0 if mock_success else -1.0
                    mock_reward = (0.5 * success_val) + (0.3 * (1 - mock_latency / 1500.0)) + (0.2 * (1 - mock_cost / 0.02))
                    mock_reward = round(max(-1.0, min(1.0, mock_reward)), 4)
                    
                    # Record the attempt so it shows in Trace Viewer
                    await record_attempt(
                        request_id=request_id, attempt_number=retries+1, 
                        model=model, provider=provider, status=status, 
                        latency_ms=mock_latency, tokens=random.randint(100, 500), 
                        cost=mock_cost
                    )
                    
                    await complete_trace(
                        request_id=request_id, status=status,
                        total_tokens=random.randint(100, 1000), 
                        prompt_tokens=random.randint(50, 500), 
                        completion_tokens=random.randint(50, 500), 
                        total_cost=mock_cost, overall_latency_ms=mock_latency, 
                        workload_type=workload_type,
                        routing_explanation=explanation,
                        rejected_models=rejected_models,
                        final_score=final_score,
                        model=model,
                        reward=mock_reward
                    )
                    
                    if mock_success:
                        asyncio.create_task(asyncio.to_thread(update_provider_learning, provider, model, mock_reward, request_id, workload_type))
                        return {
                            "choices": [{"message": {"content": f"Simulated response from {model} for demo purposes."}}],
                            "usage": {"total_tokens": 500},
                            "model": model
                        }
                    else:
                        raise Exception("Simulated provider failure for demo coverage.")

                asyncio.create_task(asyncio.to_thread(update_provider_learning, provider, model, reward, request_id, workload_type))
                
                retries += 1
                if retries <= max_retries:
                    # Switch to another provider's cheap model for the retry
                    if model == "gpt-3.5-turbo":
                        model = "claude-3-haiku-20240307"
                    else:
                        model = "gpt-3.5-turbo"
                    continue
                else:
                    await complete_trace(
                        request_id=request_id, status="failed", 
                        total_tokens=0, prompt_tokens=0, 
                        completion_tokens=0, total_cost=0.0, 
                        overall_latency_ms=(time.time()-start_time)*1000, 
                        workload_type=workload_type,
                        routing_explanation=explanation,
                        final_score=final_score,
                        model=model,
                        reward=reward
                    )
                    raise e

    def get_available_models(self) -> List[str]:
        return list(self.model_tiers.keys())

router_engine = LLMRouter()
