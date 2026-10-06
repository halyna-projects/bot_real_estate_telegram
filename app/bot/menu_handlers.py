from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import (
    budget_menu_keyboard,
    city_menu_keyboard,
    deal_type_menu_keyboard,
    district_menu_keyboard,
    parse_menu_callback,
    phone_share_keyboard,
    property_type_menu_keyboard,
    rooms_menu_keyboard,
)
from app.bot.search_flow import present_search_results
from app.db import async_session_factory
from app.models import DealType, Lead, LeadStatus, PropertyType
from app.services.leads import get_or_create_lead
from app.services.qualification import heuristic_classification

logger = logging.getLogger(__name__)
router = Router(name="menu_flow")

_CHOICE_LABELS = {
    "buy": "Kupovina",
    "rent": "Zakup",
    "sell": "Prodaja",
    "apartment": "Stan",
    "house": "Kuća",
    "commercial": "Poslovni prostor",
    "land": "Zemljište",
}


async def _apply_menu_choice(lead: Lead, field: str, value: str) -> str:
    """Apply one menu selection onto the lead and return a short label for
    the "Izabrano: ..." confirmation toast."""

    if field == "deal_type":
        lead.deal_type = DealType(value)
        label = _CHOICE_LABELS.get(value, value)
    elif field == "city":
        lead.city = value
        label = value
    elif field == "district":
        lead.district = None if value == "any" else value
        label = "Bilo koja opština" if value == "any" else value
    elif field == "property_type":
        lead.property_type = PropertyType(value)
        label = _CHOICE_LABELS.get(value, value)
    elif field == "rooms":
        lead.rooms = int(value)
        label = f"{value}+" if int(value) == 4 else value
    elif field == "budget":
        amount_str, currency = value.split("_", 1)
        lead.budget_max = int(amount_str)
        lead.budget_currency = currency
        label = f"do {int(amount_str):,} {currency}".replace(",", " ")
    else:
        label = value

    if lead.status == LeadStatus.NEW:
        lead.status = LeadStatus.QUALIFYING
    lead.temperature = heuristic_classification(lead)

    return label


async def _advance(
    field_just_set: str, target: Message, session: AsyncSession, lead: Lead, bot: Bot
) -> None:
    """Show whichever menu comes next after `field_just_set`, or run the
    search once nothing required is missing anymore."""

    if field_just_set == "city":
        await target.answer(
            f"U kojoj opštini ({lead.city}) tražimo?", reply_markup=district_menu_keyboard(lead.city)
        )
        return

    missing = lead.missing_required_fields()
    if not missing:
        await present_search_results(target, session, lead, bot)
        return

    next_field = missing[0]
    if next_field == "deal_type":
        await target.answer("Šta vas zanima?", reply_markup=deal_type_menu_keyboard())
    elif next_field == "city":
        await target.answer("U kom gradu tražimo?", reply_markup=city_menu_keyboard())
    elif next_field == "property_type":
        await target.answer("Koji tip objekta vas zanima?", reply_markup=property_type_menu_keyboard())
    elif next_field == "rooms":
        await target.answer("Koliko soba je potrebno?", reply_markup=rooms_menu_keyboard())
    elif next_field == "budget_max":
        await target.answer(
            "Koji je okvirni budžet?", reply_markup=budget_menu_keyboard(lead.deal_type)
        )
    elif next_field == "phone":
        await target.answer(
            "Ostavite, molim vas, broj telefona za kontakt — pritisnite dugme ispod "
            "ili ga otkucajte kao tekst.",
            reply_markup=phone_share_keyboard(),
        )


@router.callback_query(F.data.startswith("menu:"))
async def handle_menu_choice(callback: CallbackQuery, bot: Bot) -> None:
    field, value = parse_menu_callback(callback.data)

    async with async_session_factory() as session:
        lead = await get_or_create_lead(
            session,
            telegram_user_id=callback.from_user.id,
            telegram_username=callback.from_user.username,
            full_name=callback.from_user.full_name,
        )

        label = await _apply_menu_choice(lead, field, value)
        await session.flush()

        # Append the selection to the question itself (instead of just
        # clearing the keyboard) so the chosen answer stays visible in the
        # chat history, the same way a typed reply would -- otherwise the
        # buttons vanish and there's no permanent record of what was picked.
        try:
            original_text = callback.message.text or ""
            await callback.message.edit_text(
                f"{original_text}\n\n✅ {label}", reply_markup=None
            )
        except Exception:  # noqa: BLE001 - message may already be edited/gone, harmless
            logger.debug("Could not update menu message", exc_info=True)

        await callback.answer(f"Izabrano: {label}")
        await _advance(field, callback.message, session, lead, bot)
        await session.commit()


@router.message(F.contact)
async def handle_contact_share(message: Message, bot: Bot) -> None:
    async with async_session_factory() as session:
        lead = await get_or_create_lead(
            session,
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        lead.phone = message.contact.phone_number
        lead.temperature = heuristic_classification(lead)
        await session.flush()

        await message.answer(
            f"Hvala! Zabeležio sam vaš broj: {lead.phone}", reply_markup=ReplyKeyboardRemove()
        )

        if not lead.missing_required_fields():
            await present_search_results(message, session, lead, bot)
        else:
            await session.commit()
