"""
Negotiations list routes — read endpoints for the negotiations dashboard.
"""
import asyncio
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, or_

from model.database import get_db
from model.negotiation.model import Negotiation
from model.negotiation.schemas import NegotiationRead

logger = logging.getLogger("routes.negotiations")

router = APIRouter(prefix="/negotiations", tags=["Negotiations"])

ACTIVE_STATUSES = ("ringing", "in_progress")


def _fetch_list(limit: int, offset: int) -> list:
    db = get_db()
    try:
        rows = db.execute(
            select(Negotiation)
            .order_by(Negotiation.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()
        return [NegotiationRead.model_validate(r) for r in rows]
    finally:
        db.close()


def _fetch_active() -> list:
    db = get_db()
    try:
        rows = db.execute(
            select(Negotiation)
            .where(Negotiation.status.in_(ACTIVE_STATUSES))
            .order_by(Negotiation.created_at.desc())
        ).scalars().all()
        return [NegotiationRead.model_validate(r) for r in rows]
    finally:
        db.close()


@router.get(
    "/active",
    response_model=List[NegotiationRead],
    summary="List active negotiations",
    description="Returns only negotiations with status `ringing` or `in_progress`.",
)
async def list_active_negotiations() -> List[NegotiationRead]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch_active)


@router.get(
    "",
    response_model=List[NegotiationRead],
    summary="List negotiations",
    description="Returns the most recent negotiations ordered by creation date.",
)
async def list_negotiations(
    limit: int = Query(20, ge=1, le=200, description="Max number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> List[NegotiationRead]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch_list, limit, offset)
