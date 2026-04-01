from sqlmodel import Session, select
from src.db.session import sync_engine
from src.db.models import Budget
from loguru import logger

def check_budget(user_id: str, estimated_cost: float):
    """
    Check if the user has enough daily budget for the requested operation.
    Returns:
        "ok": Budget within limits.
        "downgrade": Daily budget exceeded, suggest switching to cheapest provider.
    """
    with Session(sync_engine) as session:
        budget = session.exec(
            select(Budget).where(Budget.user_id == user_id)
        ).first()

        if not budget:
            # If no budget record found, allow the request but log it.
            # In a real system, you might want to create a default budget.
            logger.warning(f"No budget record found for user_id: {user_id}")
            return "ok"

        # Check if daily limit is already exceeded
        if budget.current_daily_spend >= budget.daily_limit:
            logger.info(f"User {user_id} has exceeded daily budget (${budget.current_daily_spend:.4f} / ${budget.daily_limit:.4f})")
            return "downgrade"

        # Check if this request would exceed the limit
        if (budget.current_daily_spend + estimated_cost) > budget.daily_limit:
            logger.info(f"User {user_id} would exceed daily budget with this request. Switching to fallback.")
            return "downgrade"

        return "ok"

def get_budget_factor(user_id: str) -> float:
    """
    Elite V3.6: Calculate adaptive budget factor (0.5 to 1.0).
    As user approaches their limit, the factor decreases, 
    making expensive models less likely to be chosen.
    """
    with Session(sync_engine) as session:
        budget = session.exec(select(Budget).where(Budget.user_id == user_id)).first()
        if not budget or budget.daily_limit <= 0:
            return 1.0
        
        usage_ratio = budget.current_daily_spend / budget.daily_limit
        
        if usage_ratio < 0.7:
            return 1.0
        elif usage_ratio < 0.9:
            # 70-90% usage -> 0.8 factor (slight bias to cheap)
            return 0.8
        elif usage_ratio < 1.0:
            # 90-100% usage -> 0.6 factor (heavy bias to cheap)
            return 0.6
        else:
            # Over budget -> 0.4 factor (force cheapest)
            return 0.4

def update_budget_spend(user_id: str, cost: float):
    """Update the actual spend for a user after a successful request."""
    with Session(sync_engine) as session:
        budget = session.exec(
            select(Budget).where(Budget.user_id == user_id)
        ).first()
        
        if budget:
            budget.current_daily_spend += cost
            budget.current_monthly_spend += cost
            session.add(budget)
            session.commit()
            logger.info(f"Updated budget for {user_id}: +${cost:.6f} (Daily Total: ${budget.current_daily_spend:.4f})")
