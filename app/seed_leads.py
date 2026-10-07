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
        full_name="Jelena K.",
        phone="+38267111111",
        deal_type=DealType.BUY,
        city="Podgorica",
        district="Centar",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=90_000,
        budget_currency="EUR",
        temperature=Temperature.HOT,
        urgency="hitno",
        status=LeadStatus.QUALIFYING,
    ),
    dict(
        telegram_user_id=-2,
        full_name="Ivan P.",
        phone="+38267222222",
        deal_type=DealType.RENT,
        city="Budva",
        district="Stari grad",
        property_type=PropertyType.APARTMENT,
        rooms=1,
        budget_max=600,
        budget_currency="EUR",
        temperature=Temperature.WARM,
        status=LeadStatus.OFFERS_SENT,
    ),
    dict(
        telegram_user_id=-3,
        full_name="Marija S.",
        city="Kotor",
        district="Dobrota",
        deal_type=DealType.SELL,
        property_type=PropertyType.APARTMENT,
        rooms=3,
        budget_max=190_000,
        budget_currency="EUR",
        temperature=Temperature.COLD,
        status=LeadStatus.NEW,
    ),
    dict(
        telegram_user_id=-4,
        full_name="Dušan R.",
        phone="+38267444444",
        deal_type=DealType.BUY,
        city="Tivat",
        district="Centar",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=140_000,
        budget_currency="EUR",
        temperature=Temperature.HOT,
        status=LeadStatus.NEGOTIATION,
        assigned_to="Aleksandar",
        next_action="Pripremiti ugovor",
    ),
    dict(
        telegram_user_id=-5,
        full_name="Olga V.",
        phone="+38267555555",
        deal_type=DealType.RENT,
        city="Podgorica",
        district="Gorica",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=450,
        budget_currency="EUR",
        temperature=Temperature.WARM,
        status=LeadStatus.VIEWING_SCHEDULED,
        assigned_to="Aleksandar",
        next_action="Zakazati razgledanje: Ulica 3, 2 sobe, 60m²",
    ),
    dict(
        telegram_user_id=-6,
        full_name="Srđan N.",
        phone="+38267666666",
        deal_type=DealType.BUY,
        city="Budva",
        district="Bečići",
        property_type=PropertyType.HOUSE,
        rooms=4,
        budget_max=270_000,
        budget_currency="EUR",
        temperature=Temperature.HOT,
        status=LeadStatus.DEAL,
        assigned_to="Aleksandar",
    ),
    dict(
        telegram_user_id=-7,
        full_name="Ana T.",
        phone="+38267777777",
        deal_type=DealType.BUY,
        city="Tivat",
        district="Donja Lastva",
        property_type=PropertyType.APARTMENT,
        rooms=1,
        budget_max=68_000,
        budget_currency="EUR",
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
