"""
Analytics API Router (/api/v1/analytics)
High-level platform search queries, user trends, and request metrics.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Query, Depends
from backend.core.dependencies import require_admin
from backend.services.admin_service import admin_service
from backend.schemas.api_responses import ApiResponse
from shared.database.repositories.requests_repo import drama_requests_repo

router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(require_admin)])

@router.get("/overview", response_model=ApiResponse[Dict[str, Any]])
async def get_analytics_overview():
    """Retrieve summarized platform activity analytics"""
    system_stats = await admin_service.get_system_overview()
    top_searches = await admin_service.get_search_analytics(limit=10)
    
    # Request status distribution
    pending_count = await drama_requests_repo.count({"status": "pending"})
    approved_count = await drama_requests_repo.count({"status": "approved"})
    available_count = await drama_requests_repo.count({"status": "available"})
    rejected_count = await drama_requests_repo.count({"status": "rejected"})

    return ApiResponse(
        success=True,
        data={
            "metrics": system_stats,
            "top_searches": top_searches,
            "request_funnel": {
                "pending": pending_count,
                "approved": approved_count,
                "available": available_count,
                "rejected": rejected_count
            }
        }
    )

@router.get("/searches", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_popular_searches(limit: int = Query(25, ge=1, le=100)):
    """Top user search queries and hit counts"""
    data = await admin_service.get_search_analytics(limit=limit)
    return ApiResponse(success=True, data=data)
