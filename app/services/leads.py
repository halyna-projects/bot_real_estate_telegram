from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.claude_client import DialogueEngine, DialogueResult
from app.models import Lead, LeadStatus, Property, Reaction, ReactionType
from app.services.qualification import (
    apply_classification,
    apply_profile_updates,
    heuristic_classification,
)

_dialogue_engine: DialogueEngine | None = None


def get_dialogue_engine() -> DialogueEngine:
    global _dialogue_engine
    if _dialogue_engine is None:
        _dialogue_engine = DialogueEngine()
    return _dialogue_engine


async def get_or_create_lead(
    session: AsyncSession,
    telegram_user_id: int,
    telegram_username: str | None = None,
    full_name: str | None = None,
) -> Lead:
    result = await session.execute(select(Lead).where(Lead.telegram_user_id == telegram_user_id))
    lead = result.scalar_one_or_none()
    if lead is None:
        lead = Lead(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            full_name=full_name,
            status=LeadStatus.NEW,
            conversation_history=[],
        )
        session.add(lead)
        await session.flush()
    return lead


def reset_lead_for_new_conversation(lead: Lead) -> None:
    """Clear a lead's qualification profile so /start always begins a fresh
    guided flow, instead of an already-qualified lead (from earlier testing
    or a past search) jumping straight to search results on the first menu
    click."""

    lead.deal_type = None
    lead.city = None
    lead.district = None
    lead.property_type = None
    lead.rooms = None
    lead.budget_min = None
    lead.budget_max = None
    lead.budget_currency = "EUR"
    lead.phone = None
    lead.temperature = None
    lead.urgency = None
    lead.status = LeadStatus.NEW
    lead.conversation_history = []


_KNOWN_FIELD_KEYS = ("deal_type", "city", "property_type", "rooms", "budget_max", "phone")


def _known_fields_from_lead(lead: Lead) -> dict[str, Any]:
    """Fields already set directly on the lead (e.g. via the button menu),
    so a free-text reply later in the same conversation doesn't re-ask for
    them — the dialogue engines otherwise only know what's in
    conversation_history, which the button menu never writes to."""

    known: dict[str, Any] = {}
    for key in _KNOWN_FIELD_KEYS:
        value = getattr(lead, key, None)
        if value is None:
            continue
        known[key] = value.value if hasattr(value, "value") else value
    return known


async def handle_incoming_message(session: AsyncSession, lead: Lead, text: str) -> DialogueResult:
    """Run one AI dialogue turn for the lead, persist extracted profile data,
    classification and conversation history."""

    engine = get_dialogue_engine()
    result = engine.next_reply(lead.conversation_history, text, _known_fields_from_lead(lead))

    apply_profile_updates(lead, result.profile_updates)
    if result.classification:
        apply_classification(lead, result.classification)
    elif lead.temperature is None:
        lead.temperature = heuristic_classification(lead)

    lead.conversation_history = result.conversation_history
    if lead.status == LeadStatus.NEW and result.profile_updates:
        lead.status = LeadStatus.QUALIFYING

    await session.flush()
    return result


async def record_reaction(
    session: AsyncSession, lead: Lead, property_: Property, reaction: ReactionType
) -> Reaction:
    entry = Reaction(lead_id=lead.id, property_id=property_.id, reaction=reaction)
    session.add(entry)

    if reaction == ReactionType.WANT_VIEWING:
        lead.status = LeadStatus.VIEWING_SCHEDULED
        lead.next_action = f"Назначить просмотр: {property_.title}"
    elif reaction == ReactionType.INTERESTED and lead.status in (
        LeadStatus.NEW,
        LeadStatus.QUALIFYING,
    ):
        lead.status = LeadStatus.OFFERS_SENT

    await session.flush()
    return entry


async def list_recent_leads(session: AsyncSession, limit: int = 20) -> list[Lead]:
    result = await session.execute(
        select(Lead).order_by(Lead.updated_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_lead_with_reactions(session: AsyncSession, lead_id: int) -> Lead | None:
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()
