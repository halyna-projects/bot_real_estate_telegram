"""Populate the CRM with example leads so the funnel/dashboard looks
populated for a demo, without waiting for real Telegram conversations.
These are clearly fake (negative telegram_user_id, which no real Telegram
account ever has) and separate from anything a real client creates. Run
with:

    python -m app.seed_leads
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db import async_session_factory, init_db
from app.models import DealType, Lead, LeadStatus, PropertyType, Temperature

# Negative IDs so these can never collide with a real Telegram user id.
SAMPLE_LEADS = [
    dict(
        telegram_user_id=-1,
        full_name="Emma K.",
        phone="+14165551111",
        deal_type=DealType.BUY,
        city="Toronto",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=650_000,
        budget_currency="CAD",
        temperature=Temperature.HOT,
        urgency="urgent",
        status=LeadStatus.QUALIFYING,
    ),
    dict(
        telegram_user_id=-2,
        full_name="James P.",
        phone="+14165552222",
        deal_type=DealType.RENT,
        city="Calgary",
        property_type=PropertyType.APARTMENT,
        rooms=1,
        budget_max=1_800,
        budget_currency="CAD",
        temperature=Temperature.WARM,
        status=LeadStatus.OFFERS_SENT,
    ),
    dict(
        telegram_user_id=-3,
        full_name="Olivia S.",
        city="Toronto",
        deal_type=DealType.SELL,
        property_type=PropertyType.APARTMENT,
        rooms=3,
        budget_max=900_000,
        budget_currency="CAD",
        temperature=Temperature.COLD,
        status=LeadStatus.NEW,
    ),
    dict(
        telegram_user_id=-4,
        full_name="Liam R.",
        phone="+14035554444",
        deal_type=DealType.BUY,
        city="Calgary",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=550_000,
        budget_currency="CAD",
        temperature=Temperature.HOT,
        status=LeadStatus.NEGOTIATION,
        assigned_to="Alex",
        next_action="Prepare the contract",
    ),
    dict(
        telegram_user_id=-5,
        full_name="Ava V.",
        phone="+14165555555",
        deal_type=DealType.RENT,
        city="Toronto",
        district="North York",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=2_800,
        budget_currency="CAD",
        temperature=Temperature.WARM,
        status=LeadStatus.VIEWING_SCHEDULED,
        assigned_to="Alex",
        next_action="Schedule a viewing: 17 Main St, 2 bed, 56m²",
    ),
    dict(
        telegram_user_id=-6,
        full_name="Noah N.",
        phone="+14035556666",
        deal_type=DealType.BUY,
        city="Calgary",
        property_type=PropertyType.HOUSE,
        rooms=4,
        budget_max=1_200_000,
        budget_currency="CAD",
        temperature=Temperature.HOT,
        status=LeadStatus.DEAL,
        assigned_to="Alex",
    ),
    dict(
        telegram_user_id=-7,
        full_name="Sophia T.",
        phone="+14165557777",
        deal_type=DealType.BUY,
        city="Toronto",
        property_type=PropertyType.APARTMENT,
        rooms=1,
        budget_max=500_000,
        budget_currency="CAD",
        temperature=Temperature.COLD,
        status=LeadStatus.LOST,
    ),
]


async def seed() -> None:
    await init_db()
    async with async_session_factory() as session:
        existing = await session.execute(
            select(Lead).where(Lead.telegram_user_id < 0)
        )
        if existing.scalars().first() is not None:
            print("Example leads already seeded, skipping.")
            return

        for data in SAMPLE_LEADS:
            session.add(Lead(**data))

        await session.commit()
        print(f"Seeded {len(SAMPLE_LEADS)} example leads.")


if __name__ == "__main__":
    asyncio.run(seed())
