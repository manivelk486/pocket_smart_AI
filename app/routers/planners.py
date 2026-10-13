import json
from datetime import timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Plan, User
from app.schemas import PlannerRequest, PlanResponse
from app.services.recommendation import RecommendationService


router = APIRouter(prefix="/api", tags=["AI Planners"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

recommendation_service = RecommendationService()


def plan_to_response(plan: Plan) -> PlanResponse:
    created = plan.created_at

    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    return PlanResponse(
        id=plan.id,
        plan_type=plan.plan_type,
        title=plan.title,
        budget=plan.budget,
        request_data=json.loads(plan.request_data),
        result=json.loads(plan.result_data),
        ai_provider=plan.ai_provider,
        created_at=created.isoformat(),
    )


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "application": "PocketSmart AI",
    }


@router.post("/planners", response_model=PlanResponse)
def create_plan(
    data: PlannerRequest,
    db: DbSession,
    user: CurrentUser,
):
    request_data = data.model_dump()

    try:
        result, provider = recommendation_service.generate(
            request_data
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="The recommendation service failed. Please try again.",
        )

    plan = Plan(
        user_id=user.id,
        plan_type=data.plan_type,
        title=result.get("title", "Your PocketSmart Plan")[:200],
        budget=data.budget,
        request_data=json.dumps(request_data),
        result_data=json.dumps(result),
        ai_provider=provider,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan_to_response(plan)


@router.get("/planners", response_model=list[PlanResponse])
def list_plans(
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    plans = db.scalars(
        select(Plan)
        .where(Plan.user_id == user.id)
        .order_by(Plan.id.desc())
        .limit(limit)
    ).all()

    return [plan_to_response(plan) for plan in plans]


@router.get("/planners/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    db: DbSession,
    user: CurrentUser,
):
    plan = db.scalar(
        select(Plan).where(
            Plan.id == plan_id,
            Plan.user_id == user.id,
        )
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found.",
        )

    return plan_to_response(plan)


@router.delete("/planners/{plan_id}")
def delete_plan(
    plan_id: int,
    db: DbSession,
    user: CurrentUser,
):
    plan = db.scalar(
        select(Plan).where(
            Plan.id == plan_id,
            Plan.user_id == user.id,
        )
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found.",
        )

    db.delete(plan)
    db.commit()

    return {"message": "Plan deleted successfully."}