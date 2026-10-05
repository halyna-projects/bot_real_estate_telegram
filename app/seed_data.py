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
    # Подгорица
    dict(
        title="Улица 1, 2к, 65м²",
        city="Подгорица",
        district="Центр",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=2,
        area_sqm=65,
        price=95_000,
        currency="EUR",
        description="Уютная двухкомнатная квартира в центре, евроремонт.",
    ),
    dict(
        title="Улица 2, 1к, 42м²",
        city="Подгорица",
        district="Блок 5/6",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=1,
        area_sqm=42,
        price=68_000,
        currency="EUR",
        description="Однокомнатная квартира возле новой застройки.",
    ),
    dict(
        title="Улица 3, 2к, 60м² в аренду",
        city="Подгорица",
        district="Горица",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=2,
        area_sqm=60,
        price=450,
        currency="EUR",
        description="Аренда недалеко от центра, в тихом районе.",
    ),
    # Будва
    dict(
        title="Улица 4, 2к, 55м² в аренду",
        city="Будва",
        district="Бечичи",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=2,
        area_sqm=55,
        price=650,
        currency="EUR",
        description="Аренда в 5 минутах от пляжа, полностью меблирована.",
    ),
    dict(
        title="Улица 5, 2к, 58м²",
        city="Будва",
        district="Старый город",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=2,
        area_sqm=58,
        price=110_000,
        currency="EUR",
        description="Квартира в историческом центре, вид на крепостные стены.",
    ),
    dict(
        title="Улица 6, дом 4к, 150м²",
        city="Будва",
        district="Петровац",
        property_type=PropertyType.HOUSE,
        deal_type=DealType.BUY,
        rooms=4,
        area_sqm=150,
        price=270_000,
        currency="EUR",
        description="Дом с участком и видом на море, готов к заселению.",
    ),
    # Котор
    dict(
        title="Улица 7, 3к, 88м²",
        city="Котор",
        district="Старый город",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=3,
        area_sqm=88,
        price=190_000,
        currency="EUR",
        description="Просторная трёхкомнатная квартира с видом на крепость.",
    ),
    dict(
        title="Улица 8, 1к, 35м² в аренду",
        city="Котор",
        district="Доброта",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=1,
        area_sqm=35,
        price=400,
        currency="EUR",
        description="Компактная квартира в аренду у набережной.",
    ),
    # Тиват
    dict(
        title="Улица 9, 1к, 38м² в аренду",
        city="Тиват",
        district="Доня-Ластва",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=1,
        area_sqm=38,
        price=400,
        currency="EUR",
        description="Компактная квартира в аренду рядом с центром и марина.",
    ),
    dict(
        title="Улица 10, 2к, 70м²",
        city="Тиват",
        district="Центр",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=2,
        area_sqm=70,
        price=140_000,
        currency="EUR",
        description="Квартира рядом с мариной, подходит под сдачу в аренду.",
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
