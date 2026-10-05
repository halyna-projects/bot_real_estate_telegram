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
    # Podgorica
    dict(
        title="Ulica 1, 2 sobe, 65m²",
        city="Podgorica",
        district="Centar",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=2,
        area_sqm=65,
        price=95_000,
        currency="EUR",
        description="Udoban dvosoban stan u centru, novija adaptacija.",
    ),
    dict(
        title="Ulica 2, 1 soba, 42m²",
        city="Podgorica",
        district="Blok 5/6",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=1,
        area_sqm=42,
        price=68_000,
        currency="EUR",
        description="Jednosoban stan blizu nove gradnje.",
    ),
    dict(
        title="Ulica 3, 2 sobe, 60m² — izdavanje",
        city="Podgorica",
        district="Gorica",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=2,
        area_sqm=60,
        price=450,
        currency="EUR",
        description="Izdavanje nedaleko od centra, u mirnom kraju.",
    ),
    # Budva
    dict(
        title="Ulica 4, 2 sobe, 55m² — izdavanje",
        city="Budva",
        district="Bečići",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=2,
        area_sqm=55,
        price=650,
        currency="EUR",
        description="Izdavanje 5 minuta od plaže, potpuno opremljen.",
    ),
    dict(
        title="Ulica 5, 2 sobe, 58m²",
        city="Budva",
        district="Stari grad",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=2,
        area_sqm=58,
        price=110_000,
        currency="EUR",
        description="Stan u istorijskom centru, pogled na gradske zidine.",
    ),
    dict(
        title="Ulica 6, kuća 4 sobe, 150m²",
        city="Budva",
        district="Petrovac",
        property_type=PropertyType.HOUSE,
        deal_type=DealType.BUY,
        rooms=4,
        area_sqm=150,
        price=270_000,
        currency="EUR",
        description="Kuća sa placem i pogledom na more, useljiva odmah.",
    ),
    # Kotor
    dict(
        title="Ulica 7, 3 sobe, 88m²",
        city="Kotor",
        district="Stari grad",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=3,
        area_sqm=88,
        price=190_000,
        currency="EUR",
        description="Prostran trosoban stan s pogledom na tvrđavu.",
    ),
    dict(
        title="Ulica 8, 1 soba, 35m² — izdavanje",
        city="Kotor",
        district="Dobrota",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=1,
        area_sqm=35,
        price=400,
        currency="EUR",
        description="Kompaktan stan za izdavanje uz obalu.",
    ),
    # Tivat
    dict(
        title="Ulica 9, 1 soba, 38m² — izdavanje",
        city="Tivat",
        district="Donja Lastva",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=1,
        area_sqm=38,
        price=400,
        currency="EUR",
        description="Kompaktan stan za izdavanje blizu centra i marine.",
    ),
    dict(
        title="Ulica 10, 2 sobe, 70m²",
        city="Tivat",
        district="Centar",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=2,
        area_sqm=70,
        price=140_000,
        currency="EUR",
        description="Stan blizu marine, pogodan i za izdavanje.",
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
