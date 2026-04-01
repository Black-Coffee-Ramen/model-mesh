import os
from src.db.session import sync_engine
from src.db.models import SQLModel
# Import all models to ensure they are registered with SQLModel.metadata
from src.db.models import RequestTrace, RequestAttempt, Budget, ProviderHealth, PromptCache, AnomalyLog, SystemInsight, ProviderLearning

def init_db():
    # Remove existing DB file to allow fresh schema generation
    db_file = "llm_router.db"
    if os.path.exists(db_file):
        print(f"Removing existing database file: {db_file}")
        os.remove(db_file)
        
    print("Initializing Multi-Provider Database...")
    SQLModel.metadata.create_all(sync_engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()
