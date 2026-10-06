import pytest

from app.bot.menu_handlers import _advance, _apply_menu_choice
from app.models import Lead, LeadStatus


class FakeTarget:
    def __init__(self):
        self.messages: list[str] = []

    async def answer(self, text, **kwargs):
        self.messages.append(text)


class FakeBot:
    pass


@pytest.mark.asyncio
async def test_button_menu_flow_qualifies_lead_step_by_step(session):
    lead = Lead(telegram_user_id=1)
    session.add(lead)
    await session.flush()

    target = FakeTarget()
    bot = FakeBot()

    await _apply_menu_choice(lead, "deal_type", "buy")
    assert lead.status == LeadStatus.QUALIFYING
    await _advance("deal_type", target, session, lead, bot)
    assert "city" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "city", "Toronto")
    await _advance("city", target, session, lead, bot)
    assert "neighborhood" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "district", "any")
    assert lead.district is None
    await _advance("district", target, session, lead, bot)
    assert "property" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "property_type", "apartment")
    await _advance("property_type", target, session, lead, bot)
    assert "bedrooms" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "rooms", "2")
    assert lead.rooms == 2
    await _advance("rooms", target, session, lead, bot)
    assert "budget" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "budget", "650000_CAD")
    assert lead.budget_max == 650000
    assert lead.budget_currency == "CAD"
    await _advance("budget", target, session, lead, bot)
    assert "phone" in target.messages[-1].lower()

    assert lead.missing_required_fields() == ["phone"]
    lead.phone = "+14165551234"
    assert lead.is_qualified()


@pytest.mark.asyncio
async def test_district_choice_stores_specific_value(session):
    lead = Lead(telegram_user_id=2)
    session.add(lead)
    await session.flush()

    await _apply_menu_choice(lead, "city", "Calgary")
    await _apply_menu_choice(lead, "district", "Kensington")
    assert lead.district == "Kensington"


@pytest.mark.asyncio
async def test_rooms_four_plus_stores_as_four(session):
    lead = Lead(telegram_user_id=3)
    session.add(lead)
    await session.flush()

    await _apply_menu_choice(lead, "rooms", "4")
    assert lead.rooms == 4
