import pytest

from app.models import DealType, Lead, Property, PropertySource, PropertyType, Reaction, ReactionType
from app.search.internal import search_internal_properties


async def _make_property(session, **overrides):
    defaults = dict(
        source=PropertySource.INTERNAL,
        title="Test apartment",
        city="Toronto",
        district="Downtown",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=2,
        area_sqm=60,
        price=90_000,
        currency="USD",
    )
    defaults.update(overrides)
    prop = Property(**defaults)
    session.add(prop)
    await session.flush()
    return prop


async def _make_lead(session, **overrides):
    defaults = dict(
        telegram_user_id=1,
        deal_type=DealType.BUY,
        city="Toronto",
        property_type=PropertyType.APARTMENT,
        rooms=2,
        budget_max=100_000,
    )
    defaults.update(overrides)
    lead = Lead(**defaults)
    session.add(lead)
    await session.flush()
    return lead


@pytest.mark.asyncio
async def test_search_matches_lead_criteria(session):
    match = await _make_property(session)
    await _make_property(session, city="Calgary", title="Different city")
    await _make_property(session, price=150_000, title="Too expensive")

    lead = await _make_lead(session)
    results = await search_internal_properties(session, lead)

    assert match in results
    assert len(results) == 1


@pytest.mark.asyncio
async def test_not_suitable_reaction_excludes_property_permanently(session):
    prop = await _make_property(session)
    lead = await _make_lead(session)

    session.add(Reaction(lead_id=lead.id, property_id=prop.id, reaction=ReactionType.NOT_SUITABLE))
    await session.flush()

    results = await search_internal_properties(session, lead)
    assert prop not in results
