from __future__ import annotations

from typing import Protocol

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.formatting import format_lead_summary_for_realtor, format_property_card
from app.bot.keyboards import property_reaction_keyboard
from app.bot.notifications import notify_realtor
from app.models import Lead
from app.search.hybrid import hybrid_search


class Answerable(Protocol):
    async def answer(self, *args: object, **kwargs: object) -> object: ...


async def present_search_results(
    target: Answerable, session: AsyncSession, lead: Lead, bot: Bot
) -> None:
    """Run the hybrid search and send results (or a not-found message) to
    `target` — a Message or a CallbackQuery's `.message`, anything with an
    async `.answer()` — then notify the realtor. Shared between the
    free-text AI dialogue flow and the button-menu flow so both trigger the
    exact same search/notify behavior once a lead is fully qualified."""

    properties = await hybrid_search(session, lead)
    await session.commit()

    if not properties:
        await target.answer(
            "К сожалению, сейчас нет вариантов под ваш запрос. Риелтор свяжется "
            "с вами, как только появится что-то подходящее."
        )
    else:
        await target.answer(f"Нашёл {len(properties)} вариант(ов) под ваш запрос:")
        for prop in properties:
            await target.answer(
                format_property_card(prop),
                reply_markup=property_reaction_keyboard(prop),
                parse_mode="HTML",
            )
    await notify_realtor(bot, format_lead_summary_for_realtor(lead))
