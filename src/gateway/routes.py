from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from src.core import router_engine
from src.monitoring.metrics import metrics_engine
from loguru import logger

router = APIRouter(prefix="/v1", tags=["v1"])

@router.get("/usage")
async def get_usage():
    return metrics_engine.get_total_usage()

@router.get("/usage/models")
async def get_usage_by_model():
    return metrics_engine.get_usage_by_model()

class ChatCompletionRequest(BaseModel):
    user_id: Optional[str] = "default_user"
    model: Optional[str] = "auto"
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    strategy: Optional[str] = "cost"
    workload_type: Optional[str] = None

@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.
    """
    try:
        response = await router_engine.completion(
            user_id=request.user_id,
            model=request.model,
            messages=request.messages,
            strategy=request.strategy,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
            workload_type=request.workload_type
        )
        return response
    except Exception as e:
        logger.error(f"Gateway error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models():
    return {"models": router_engine.get_available_models()}
