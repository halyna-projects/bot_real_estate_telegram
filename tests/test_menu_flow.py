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
    assert "городе" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "city", "Подгорица")
    await _advance("city", target, session, lead, bot)
    assert "районе" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "district", "any")
    assert lead.district is None
    await _advance("district", target, session, lead, bot)
    assert "тип объекта" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "property_type", "apartment")
    await _advance("property_type", target, session, lead, bot)
    assert "комнат" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "rooms", "2")
    assert lead.rooms == 2
    await _advance("rooms", target, session, lead, bot)
    assert "бюджет" in target.messages[-1].lower()

    await _apply_menu_choice(lead, "budget", "100000_EUR")
    assert lead.budget_max == 100000
    assert lead.budget_currency == "EUR"
    await _advance("budget", target, session, lead, bot)
    assert "телефон" in target.messages[-1].lower()

    assert lead.missing_required_fields() == ["phone"]
    lead.phone = "+380501234567"
    assert lead.is_qualified()


@pytest.mark.asyncio
async def test_district_choice_stores_specific_value(session):
    lead = Lead(telegram_user_id=2)
    session.add(lead)
    await session.flush()

    await _apply_menu_choice(lead, "city", "Котор")
    await _apply_menu_choice(lead, "district", "Доброта")
    assert lead.district == "Доброта"


@pytest.mark.asyncio
async def test_rooms_four_plus_stores_as_four(session):
    lead = Lead(telegram_user_id=3)
    session.add(lead)
    await session.flush()

    await _apply_menu_choice(lead, "rooms", "4")
    assert lead.rooms == 4
