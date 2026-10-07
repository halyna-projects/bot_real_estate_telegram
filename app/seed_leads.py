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
        full_name="Олена К.",
        phone="+380501111111",
        deal_type=DealType.BUY,
        city="Київ",
        district="Печерський",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=90_000,
        budget_currency="USD",
        temperature=Temperature.HOT,
        urgency="терміново",
        status=LeadStatus.QUALIFYING,
    ),
    dict(
        telegram_user_id=-2,
        full_name="Іван П.",
        phone="+380502222222",
        deal_type=DealType.RENT,
        city="Львів",
        district="Залізничний",
        property_type=PropertyType.APARTMENT,
        rooms=1,
        budget_max=15_000,
        budget_currency="UAH",
        temperature=Temperature.WARM,
        status=LeadStatus.OFFERS_SENT,
    ),
    dict(
        telegram_user_id=-3,
        full_name="Марія С.",
        city="Київ",
        district="Солом'янський",
        deal_type=DealType.SELL,
        property_type=PropertyType.APARTMENT,
        rooms=3,
        budget_max=190_000,
        budget_currency="USD",
        temperature=Temperature.COLD,
        status=LeadStatus.NEW,
    ),
    dict(
        telegram_user_id=-4,
        full_name="Дмитро Р.",
        phone="+380504444444",
        deal_type=DealType.BUY,
        city="Львів",
        district="Галицький",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=140_000,
        budget_currency="USD",
        temperature=Temperature.HOT,
        status=LeadStatus.NEGOTIATION,
        assigned_to="Олександр",
        next_action="Підготувати договір",
    ),
    dict(
        telegram_user_id=-5,
        full_name="Ольга В.",
        phone="+380505555555",
        deal_type=DealType.RENT,
        city="Київ",
        district="Оболонський",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=20_000,
        budget_currency="UAH",
        temperature=Temperature.WARM,
        status=LeadStatus.VIEWING_SCHEDULED,
        assigned_to="Олександр",
        next_action="Призначити перегляд: вул. Центральна 3, 2к, 60м²",
    ),
    dict(
        telegram_user_id=-6,
        full_name="Сергій Н.",
        phone="+380506666666",
        deal_type=DealType.BUY,
        city="Львів",
        district="Сихівський",
        property_type=PropertyType.HOUSE,
        rooms=4,
        budget_max=270_000,
        budget_currency="USD",
        temperature=Temperature.HOT,
        status=LeadStatus.DEAL,
        assigned_to="Олександр",
    ),
    dict(
        telegram_user_id=-7,
        full_name="Анна Т.",
        phone="+380507777777",
        deal_type=DealType.BUY,
        city="Київ",
        district="Дарницький",
        property_type=PropertyType.APARTMENT,
        rooms=1,
        budget_max=68_000,
        budget_currency="USD",
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
