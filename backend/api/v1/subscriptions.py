"""
Subscriptions & Premium Plans API Router (/api/v1/subscriptions)
"""
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from backend.core.dependencies import get_current_user
from backend.schemas.api_responses import ApiResponse, SubscriptionCreateRequest
from shared.database.repositories.users_repo import subscriptions_repo, users_repo

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions & Premium"])

PREMIUM_PLANS = [
    {
        "plan_id": "monthly",
        "name": "1 Month Premium",
        "duration_days": 30,
        "price_stars": 150,
        "price_usd": 2.99,
        "features": ["No Ads", "Instant File Direct Delivery", "Highest 1080p Quality", "Priority Requests"]
    },
    {
        "plan_id": "quarterly",
        "name": "3 Months Premium",
        "duration_days": 90,
        "price_stars": 350,
        "price_usd": 6.99,
        "features": ["All Monthly Features", "Batch Episode Downloads", "Early Access to New Releases"]
    },
    {
        "plan_id": "yearly",
        "name": "1 Year VIP",
        "duration_days": 365,
        "price_stars": 1200,
        "price_usd": 23.99,
        "features": ["All Quarterly Features", "VIP Badge in Telegram Group", "Unlimited Fast Downloads"]
    }
]

@router.get("/plans", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_premium_plans():
    """List available subscription plans and perks"""
    return ApiResponse(success=True, data=PREMIUM_PLANS)

@router.get("/current", response_model=ApiResponse[Dict[str, Any]])
async def get_current_subscription(user: Dict[str, Any] = Depends(get_current_user)):
    """Fetch current user's active subscription status"""
    uid = user["user_id"]
    sub = await subscriptions_repo.find_one({"user_id": str(uid), "status": "active"})
    return ApiResponse(success=True, data=sub or {"is_premium": False, "status": "free"})

@router.post("", response_model=ApiResponse[Dict[str, Any]])
async def create_subscription(
    payload: SubscriptionCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Subscribe to a premium plan"""
    uid = user["user_id"]
    expiry = datetime.now(timezone.utc) + timedelta(days=payload.duration_days)
    doc = {
        "user_id": str(uid),
        "plan_id": payload.plan_id,
        "status": "active",
        "payment_method": payload.payment_method,
        "start_date": datetime.now(timezone.utc),
        "expiry_date": expiry,
        "created_at": datetime.now(timezone.utc)
    }
    created = await subscriptions_repo.create(doc)

    # Update user role to premium
    filter_q = {"telegram_id": int(uid)} if str(uid).isdigit() else {"web_id": str(uid)}
    await users_repo.update_one(filter_q, {
        "role": "premium",
        "is_premium": True,
        "premium_expires_at": expiry
    })

    return ApiResponse(success=True, data=created, message="Subscription activated successfully")
