from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.ai.prompts import GREETING_MESSAGE
from app.bot.formatting import format_reaction_confirmation
from app.bot.keyboards import (
    deal_type_menu_keyboard,
    parse_reaction_callback,
)
from app.bot.notifications import notify_realtor
from app.bot.search_flow import present_search_results
from app.db import async_session_factory
from app.models import Property
from app.services.leads import (
    get_or_create_lead,
    handle_incoming_message,
    record_reaction,
    reset_lead_for_new_conversation,
)

logger = logging.getLogger(__name__)
router = Router(name="lead_dialogue")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    async with async_session_factory() as session:
        lead = await get_or_create_lead(
            session,
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        reset_lead_for_new_conversation(lead)
        lead.conversation_history = [{"role": "assistant", "content": GREETING_MESSAGE}]
        await session.commit()

    # A reply keyboard (e.g. "Pošalji broj" from a previous
    # conversation) and an inline keyboard can't be sent on the same
    # message, so clear any leftover reply keyboard first via a throwaway
    # message that's deleted right away — /start should always start from
    # a visually clean slate.
    clearing = await message.answer("⁣", reply_markup=ReplyKeyboardRemove())
    await clearing.delete()

    await message.answer(GREETING_MESSAGE, reply_markup=deal_type_menu_keyboard())


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message, bot: Bot) -> None:
    async with async_session_factory() as session:
        lead = await get_or_create_lead(
            session,
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        was_qualified = lead.is_qualified()

        result = await handle_incoming_message(session, lead, message.text)
        await message.answer(result.reply_text)

        should_search = lead.is_qualified() and not was_qualified

        if should_search:
            await present_search_results(message, session, lead, bot)
        else:
            await session.commit()


@router.callback_query(F.data.startswith("react:"))
async def handle_reaction(callback: CallbackQuery, bot: Bot) -> None:
    property_id, reaction = parse_reaction_callback(callback.data)

    async with async_session_factory() as session:
        lead = await get_or_create_lead(
            session,
            telegram_user_id=callback.from_user.id,
            telegram_username=callback.from_user.username,
            full_name=callback.from_user.full_name,
        )
        property_ = await session.get(Property, property_id)
        if property_ is None:
            await callback.answer("Ovaj oglas više nije dostupan.", show_alert=True)
            return

        await record_reaction(session, lead, property_, reaction)
        await session.commit()

        confirmation_text = format_reaction_confirmation(property_, reaction)

    await callback.message.edit_text(confirmation_text, parse_mode="HTML")
    await callback.answer("Zabeležio sam vašu reakciju!")

    realtor_note = (
        f"📩 Reakcija klijenta {callback.from_user.full_name}: "
        f"{reaction.value} — {property_.title}"
    )
    await notify_realtor(bot, realtor_note)
