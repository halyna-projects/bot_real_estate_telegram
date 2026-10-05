from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import async_session_factory
from app.models import Lead, LeadStatus, Reaction
from app.web.auth import require_realtor

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


@router.get("/")
async def dashboard(request: Request, session: AsyncSession = Depends(get_session), _: str = Depends(require_realtor)):
    result = await session.execute(select(Lead).order_by(Lead.updated_at.desc()).limit(50))
    leads = list(result.scalars().all())

    counts: dict[str, int] = {}
    for lead in leads:
        counts[lead.status.value] = counts.get(lead.status.value, 0) + 1

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "leads": leads, "counts": counts},
    )


@router.get("/leads/{lead_id}")
async def lead_detail(
    lead_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_realtor),
):
    lead = await session.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead nije pronađen")

    result = await session.execute(
        select(Reaction)
        .where(Reaction.lead_id == lead_id)
        .options(selectinload(Reaction.property))
        .order_by(Reaction.created_at.desc())
    )
    reactions = list(result.scalars().all())

    return templates.TemplateResponse(
        "lead_detail.html",
        {
            "request": request,
            "lead": lead,
            "reactions": reactions,
            "statuses": list(LeadStatus),
        },
    )


@router.post("/leads/{lead_id}")
async def update_lead(
    lead_id: int,
    status_value: str = Form(alias="status"),
    assigned_to: str = Form(default=""),
    next_action: str = Form(default=""),
    next_action_due: str = Form(default=""),
    notes: str = Form(default=""),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_realtor),
):
    lead = await session.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead nije pronađen")

    lead.status = LeadStatus(status_value)
    lead.assigned_to = assigned_to or None
    lead.next_action = next_action or None
    lead.notes = notes or None
    if next_action_due:
        try:
            lead.next_action_due = datetime.fromisoformat(next_action_due)
        except ValueError:
            lead.next_action_due = None
    else:
        lead.next_action_due = None

    await session.commit()
    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)
