from sqlmodel import Session, select
from src.db.session import sync_engine, init_db
from src.db.models import Budget, ProviderHealth
from datetime import datetime, timezone

def seed_data():
    print("Initializing Database...")
    init_db()
    
    with Session(sync_engine) as session:
        # 1. Seed Budgets
        test_user = session.exec(select(Budget).where(Budget.user_id == "test_user")).first()
        if not test_user:
            print("Seeding test_user budget...")
            budget = Budget(
                user_id="test_user",
                daily_limit=0.05,  # Very low for testing downgrade
                monthly_limit=10.0,
                current_daily_spend=0.0,
                current_monthly_spend=0.0
            )
            session.add(budget)
        
        # 2. Seed initial Provider Health
        models_to_seed = [
            ("openai", "gpt-3.5-turbo"),
            ("openai", "gpt-4o"),
            ("anthropic", "claude-3-haiku-20240307"),
            ("gemini", "gemini-1.5-pro-latest")
        ]
        
        for provider, model in models_to_seed:
            exists = session.exec(
                select(ProviderHealth)
                .where(ProviderHealth.provider == provider)
                .where(ProviderHealth.model == model)
            ).first()
            if not exists:
                print(f"Seeding health record for {model}...")
                health = ProviderHealth(
                    provider=provider,
                    model=model,
                    success_rate=1.0,
                    avg_latency=0.2,
                    stability_score=1.0,
                    last_updated=datetime.now(timezone.utc)
                )
                session.add(health)
        
        session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    seed_data()
