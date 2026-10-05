"""Populate the internal property inventory with sample listings so the bot
has something to match against out of the box. Run with:

    python -m app.seed_data
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db import async_session_factory, init_db
from app.models import DealType, Property, PropertySource, PropertyType

SAMPLE_PROPERTIES = [
    dict(
        title="ул. Владимирская, 2к, 65м²",
        city="Киев",
        district="Шевченковский",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=2,
        area_sqm=65,
        price=95_000,
        currency="USD",
        description="Уютная двухкомнатная квартира в центре, евроремонт.",
    ),
    dict(
        title="просп. Победы, 1к, 42м²",
        city="Киев",
        district="Соломенский",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=1,
        area_sqm=42,
        price=68_000,
        currency="USD",
        description="Однокомнатная квартира возле метро, новостройка.",
    ),
    dict(
        title="ул. Лычаковская, 3к, 88м²",
        city="Львов",
        district="Лычаковский",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=3,
        area_sqm=88,
        price=99_000,
        currency="USD",
        description="Просторная трёхкомнатная квартира с видом на парк.",
    ),
    dict(
        title="ул. Крещатик, 2к, 55м² в аренду",
        city="Киев",
        district="Печерский",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=2,
        area_sqm=55,
        price=25_000,
        currency="UAH",
        description="Аренда в центре, полностью меблирована.",
    ),
    dict(
        title="ул. Городоцкая, 1к, 38м² в аренду",
        city="Львов",
        district="Железнодорожный",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=1,
        area_sqm=38,
        price=12_000,
        currency="UAH",
        description="Компактная квартира в аренду рядом с центром.",
    ),
    dict(
        title="Дом в пригороде Киева, 4к, 150м²",
        city="Киев",
        district="Обуховский р-н",
        property_type=PropertyType.HOUSE,
        deal_type=DealType.BUY,
        rooms=4,
        area_sqm=150,
        price=99_500,
        currency="USD",
        description="Дом с участком 6 соток, готов к заселению.",
    ),
]


async def seed() -> None:
    await init_db()
    async with async_session_factory() as session:
        existing = await session.execute(
            select(Property).where(Property.source == PropertySource.INTERNAL)
        )
        if existing.scalars().first() is not None:
            print("Internal properties already seeded, skipping.")
            return

        for data in SAMPLE_PROPERTIES:
            session.add(Property(source=PropertySource.INTERNAL, **data))

        await session.commit()
        print(f"Seeded {len(SAMPLE_PROPERTIES)} internal properties.")


if __name__ == "__main__":
    asyncio.run(seed())
