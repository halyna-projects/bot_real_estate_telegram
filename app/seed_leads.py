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
        full_name="Елена К.",
        phone="+38267111111",
        deal_type=DealType.BUY,
        city="Подгорица",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=90_000,
        budget_currency="EUR",
        temperature=Temperature.HOT,
        urgency="срочно",
        status=LeadStatus.QUALIFYING,
    ),
    dict(
        telegram_user_id=-2,
        full_name="Иван П.",
        phone="+38267222222",
        deal_type=DealType.RENT,
        city="Будва",
        property_type=PropertyType.APARTMENT,
        rooms=1,
        budget_max=600,
        budget_currency="EUR",
        temperature=Temperature.WARM,
        status=LeadStatus.OFFERS_SENT,
    ),
    dict(
        telegram_user_id=-3,
        full_name="Мария С.",
        city="Котор",
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
        full_name="Дмитрий Р.",
        phone="+38267444444",
        deal_type=DealType.BUY,
        city="Тиват",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=140_000,
        budget_currency="EUR",
        temperature=Temperature.HOT,
        status=LeadStatus.NEGOTIATION,
        assigned_to="Александр",
        next_action="Подготовить договор",
    ),
    dict(
        telegram_user_id=-5,
        full_name="Ольга В.",
        phone="+38267555555",
        deal_type=DealType.RENT,
        city="Подгорица",
        district="Горица",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=450,
        budget_currency="EUR",
        temperature=Temperature.WARM,
        status=LeadStatus.VIEWING_SCHEDULED,
        assigned_to="Александр",
        next_action="Назначить просмотр: Улица 3, 2к, 60м²",
    ),
    dict(
        telegram_user_id=-6,
        full_name="Сергей Н.",
        phone="+38267666666",
        deal_type=DealType.BUY,
        city="Будва",
        property_type=PropertyType.HOUSE,
        rooms=4,
        budget_max=270_000,
        budget_currency="EUR",
        temperature=Temperature.HOT,
        status=LeadStatus.DEAL,
        assigned_to="Александр",
    ),
    dict(
        telegram_user_id=-7,
        full_name="Анна Т.",
        phone="+38267777777",
        deal_type=DealType.BUY,
        city="Тиват",
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
