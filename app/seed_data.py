"""Populate the internal property inventory with sample listings so the bot
has something to match against out of the box. Run with:

    python -m app.seed_data

The search filter (app/search/internal.py) matches on exact deal type,
exact property type, exact rooms count and price <= budget_max, so a
sparse sample set makes it very easy for a live demo to hit "no results"
just by picking an unlucky combination of menu buttons. To avoid that,
every (deal type x property type x rooms x budget bracket) combination
the menu itself can produce is covered by at least one listing per city —
built directly from keyboards.py's own DEAL_TYPE's options, ROOMS_OPTIONS
and BUDGET_RANGES so this can't drift out of sync with the menu again.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.bot.keyboards import BUDGET_RANGES, CITY_OPTIONS, DISTRICTS_BY_CITY, ROOMS_OPTIONS
from app.db import async_session_factory, init_db
from app.models import DealType, Property, PropertySource, PropertyType

_PROPERTY_TYPES = [
    PropertyType.APARTMENT,
    PropertyType.HOUSE,
    PropertyType.COMMERCIAL,
    PropertyType.LAND,
]
_DEAL_TYPES = [DealType.BUY, DealType.RENT, DealType.SELL]

SAMPLE_PROPERTIES: list[dict] = []

_street = 0
for city in CITY_OPTIONS:
    districts = DISTRICTS_BY_CITY[city]
    for property_type in _PROPERTY_TYPES:
        for deal_type in _DEAL_TYPES:
            # Same lookup the menu itself uses in keyboards.budget_menu_keyboard,
            # so buy/sell share the "default" brackets exactly like the real UI.
            ranges = BUDGET_RANGES.get(deal_type, BUDGET_RANGES["default"])
            for rooms in ROOMS_OPTIONS:
                for amount, _label, currency in ranges:
                    _street += 1
                    price = int(amount * 0.9)  # safely under this bracket's upper bound
                    area = 20 + rooms * 18
                    title = f"Улица {_street}, {rooms}к, {area}м²"
                    if deal_type == DealType.RENT:
                        title += " в аренду"
                    SAMPLE_PROPERTIES.append(
                        dict(
                            title=title,
                            city=city,
                            district=districts[_street % len(districts)],
                            property_type=property_type,
                            deal_type=deal_type,
                            rooms=rooms,
                            area_sqm=area,
                            price=price,
                            currency=currency,
                            description="Демо-объект для презентации.",
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
