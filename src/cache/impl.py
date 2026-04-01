import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlmodel import select
from src.db.models import PromptCache
from src.db.session import AsyncSessionLocal
from loguru import logger

class CacheEngine:
    def __init__(self):
        self.in_memory_cache: Dict[str, Dict[str, Any]] = {}
        logger.info("CacheEngine V3 initialized")

    def _generate_hash(self, messages: List[Dict[str, str]]) -> str:
        """Generate a deterministic hash for a set of messages."""
        normalized = json.dumps(messages, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def get(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        prompt_hash = self._generate_hash(messages)
        
        # 1. Check in-memory
        if prompt_hash in self.in_memory_cache:
            logger.info(f"Cache hit (in-memory) for {prompt_hash}")
            return self.in_memory_cache[prompt_hash]
            
        # 2. Check DB
        async with AsyncSessionLocal() as session:
            statement = select(PromptCache).where(PromptCache.prompt_hash == prompt_hash)
            result = await session.execute(statement)
            record = result.scalar_one_or_none()
            
            if record:
                logger.info(f"Cache hit (DB) for {prompt_hash}")
                response_data = json.loads(record.response_json)
                # Populate in-memory for faster subsequent access
                self.in_memory_cache[prompt_hash] = response_data
                return response_data
                
        return None

    async def set(self, messages: List[Dict[str, str]], response: Any, model: str, tokens: int, cost: float):
        prompt_hash = self._generate_hash(messages)
        response_json = json.dumps(response)
        
        # 1. Update in-memory
        self.in_memory_cache[prompt_hash] = response
        
        # 2. Update DB
        async with AsyncSessionLocal() as session:
            # Check if exists to avoid duplicates
            statement = select(PromptCache).where(PromptCache.prompt_hash == prompt_hash)
            result = await session.execute(statement)
            if not result.scalar_one_or_none():
                cache_record = PromptCache(
                    prompt_hash=prompt_hash,
                    response_json=response_json,
                    model=model,
                    tokens=tokens,
                    estimated_cost=cost
                )
                session.add(cache_record)
                await session.commit()
                logger.info(f"Cached response for {prompt_hash}")

cache_engine = CacheEngine()
