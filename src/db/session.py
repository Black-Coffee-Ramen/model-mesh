import os
from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config import settings

# Database URL - default to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./llm_router.db")
SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")

# Async engine for FastAPI
async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Sync engine for scripts/init
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

def init_db():
    from src.db.models import RequestTrace, RequestAttempt, ProviderHealth, SystemInsight, ProviderLearning, AnomalyLog, PromptCache, Budget
    SQLModel.metadata.create_all(sync_engine)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Helper for manual session (outside FastAPI)
async def get_async_session():
    async with AsyncSessionLocal() as session:
        return session
