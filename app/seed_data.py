"""Populate the internal property inventory with sample listings so the bot
has something to match against out of the box. Run with:

    python -m app.seed_data

The search filter (app/search/internal.py) matches on exact city, exact
rooms count and price <= budget_max, so a sparse sample set makes it very
easy for a live demo to hit "no results" just by picking an unlucky
rooms/budget combination in the button menu. To avoid that, every
(rooms x budget-bracket) combination from the menu's own options
(keyboards.ROOMS_OPTIONS x keyboards.BUDGET_RANGES) is covered by at least
one apartment listing per city and deal type.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db import async_session_factory, init_db
from app.models import DealType, Property, PropertySource, PropertyType

_DISTRICTS = {
    "Podgorica": ["Centar", "Gorica", "Zapad", "Stari aerodrom", "Blok 5/6"],
    "Budva": ["Stari grad", "Bečići", "Rafailovići", "Petrovac"],
    "Kotor": ["Stari grad", "Dobrota", "Muo", "Perast"],
    "Tivat": ["Centar", "Donja Lastva", "Krašići"],
}

_ROOMS = [1, 2, 3, 4]

# One price per budget bracket from keyboards.BUDGET_RANGES, safely under
# each bracket's upper bound, so every bracket button finds a match.
_RENT_PRICES = [280, 550, 900, 1800]  # brackets: <=300, <=600, <=1000, <=2000
_BUY_PRICES = [45_000, 95_000, 180_000, 280_000]  # brackets: <=50k, <=100k, <=200k, <=300k

SAMPLE_PROPERTIES: list[dict] = []

_street = 0
for city, districts in _DISTRICTS.items():
    for rooms in _ROOMS:
        for price in _RENT_PRICES:
            _street += 1
            area = 25 + rooms * 18
            SAMPLE_PROPERTIES.append(
                dict(
                    title=f"Ulica {_street}, {rooms} sobe, {area}m² — izdavanje",
                    city=city,
                    district=districts[_street % len(districts)],
                    property_type=PropertyType.APARTMENT,
                    deal_type=DealType.RENT,
                    rooms=rooms,
                    area_sqm=area,
                    price=price,
                    currency="EUR",
                    description="Stan za izdavanje, useljiv odmah.",
                )
            )
        for price in _BUY_PRICES:
            _street += 1
            area = 28 + rooms * 20
            SAMPLE_PROPERTIES.append(
                dict(
                    title=f"Ulica {_street}, {rooms} sobe, {area}m²",
                    city=city,
                    district=districts[_street % len(districts)],
                    property_type=PropertyType.APARTMENT,
                    deal_type=DealType.BUY,
                    rooms=rooms,
                    area_sqm=area,
                    price=price,
                    currency="EUR",
                    description="Stan na prodaju, dobra lokacija.",
                )
            )

# A couple of houses per city too (rent/buy, mid rooms counts) so that
# menu path isn't a dead end either, without going for full coverage.
for city, districts in _DISTRICTS.items():
    for rooms, price in [(3, 160_000), (4, 260_000)]:
        _street += 1
        SAMPLE_PROPERTIES.append(
            dict(
                title=f"Ulica {_street}, kuća {rooms} sobe, {rooms * 40}m²",
                city=city,
                district=districts[0],
                property_type=PropertyType.HOUSE,
                deal_type=DealType.BUY,
                rooms=rooms,
                area_sqm=rooms * 40,
                price=price,
                currency="EUR",
                description="Kuća sa placem, useljiva odmah.",
            )
        )


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
