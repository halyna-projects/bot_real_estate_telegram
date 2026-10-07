"""A minimal rule-based stand-in for the Claude dialogue engine.

Used when ANTHROPIC_API_KEY is not configured, so the bot, the qualification
pipeline and the web cabinet remain testable and runnable end-to-end without
a live LLM key. It intentionally does *not* try to replicate the natural
conversation quality of the real AI agent — only extracts the same
structured fields via simple regular expressions.
"""

from __future__ import annotations

import re
from typing import Any

from app.ai.claude_client import DialogueResult

_DEAL_TYPE_PATTERNS = {
    "rent": re.compile(r"орен|зня(ти|ла)|найм", re.IGNORECASE),
    "sell": re.compile(r"продат|продаж", re.IGNORECASE),
    "buy": re.compile(r"купит|купівл|придбат", re.IGNORECASE),
}

_PROPERTY_TYPE_PATTERNS = {
    "house": re.compile(r"буд(инок|инку)|котедж", re.IGNORECASE),
    "commercial": re.compile(r"комерц|офіс|магазин", re.IGNORECASE),
    "land": re.compile(r"землі|ділянк", re.IGNORECASE),
    "apartment": re.compile(r"квартир", re.IGNORECASE),
}

_CITY_PATTERNS = {
    "Київ": re.compile(r"ки[їє]в|kyiv|kiev", re.IGNORECASE),
    "Львів": re.compile(r"льв[іоа]в|lviv", re.IGNORECASE),
}

_ROOMS_RE = re.compile(r"(\d+)\s*[-]?\s*к(імн|імнат|)")
_PHONE_RE = re.compile(r"(\+?380\d{9}|0\d{9})")
_BUDGET_RE = re.compile(
    r"(?P<amount>\d[\d\s]{2,})\s*(?P<currency>usd|\$|грн|uah|eur|€)?", re.IGNORECASE
)
_URGENT_RE = re.compile(r"термін|швидко|цього тижня|негайно|якнайшвидше", re.IGNORECASE)

_CURRENCY_MAP = {"$": "USD", "usd": "USD", "грн": "UAH", "uah": "UAH", "eur": "EUR", "€": "EUR"}

_QUESTIONS_ORDER = [
    ("deal_type", "Уточніть, будь ласка: купівля, оренда чи продаж?"),
    ("city", "У якому місті шукаємо (Київ чи Львів)?"),
    ("property_type", "Який тип об'єкта цікавить: квартира, будинок, комерція чи земля?"),
    ("rooms", "Скільки кімнат потрібно?"),
    ("budget_max", "Який орієнтовний бюджет?"),
    ("phone", "Залиште, будь ласка, номер телефону для зв'язку."),
]


def extract_fields(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}

    for value, pattern in _DEAL_TYPE_PATTERNS.items():
        if pattern.search(text):
            fields["deal_type"] = value
            break

    for value, pattern in _PROPERTY_TYPE_PATTERNS.items():
        if pattern.search(text):
            fields["property_type"] = value
            break

    for city, pattern in _CITY_PATTERNS.items():
        if pattern.search(text):
            fields["city"] = city
            break

    rooms_match = _ROOMS_RE.search(text)
    if rooms_match:
        fields["rooms"] = int(rooms_match.group(1))

    phone_match = _PHONE_RE.search(text)
    if phone_match:
        fields["phone"] = phone_match.group(1)

    budget_match = _BUDGET_RE.search(text)
    # A phone number is itself a long run of digits, so the budget regex
    # can match the same digits as a (nonsensical) amount when the message
    # is just a phone number — skip it when the two matches overlap.
    budget_overlaps_phone = phone_match and budget_match and (
        budget_match.start() < phone_match.end() and phone_match.start() < budget_match.end()
    )
    if budget_match and not budget_overlaps_phone and len(budget_match.group("amount").replace(" ", "")) >= 3:
        amount = int(budget_match.group("amount").replace(" ", ""))
        fields["budget_max"] = amount
        currency = budget_match.group("currency")
        if currency:
            fields["budget_currency"] = _CURRENCY_MAP.get(currency.lower(), "USD")

    return fields


def classify(fields: dict[str, Any], text: str) -> dict[str, Any] | None:
    if not fields:
        return None
    has_core = fields.get("budget_max") and fields.get("phone")
    is_urgent = bool(_URGENT_RE.search(text))
    if has_core and is_urgent:
        temperature = "hot"
    elif has_core:
        temperature = "warm"
    else:
        temperature = "cold"
    return {
        "temperature": temperature,
        "urgency": "терміново" if is_urgent else "не вказано",
    }


_BARE_NUMBER_RE = re.compile(r"^\s*(\d+)\s*\+?\s*$")


def _field_asked_by(question_text: str) -> str | None:
    for key, question in _QUESTIONS_ORDER:
        if question in question_text:
            return key
    return None


def _extract_with_pending(text: str, pending_field: str | None) -> dict[str, Any]:
    """Like extract_fields(), but also resolves a bare numeric reply (e.g.
    '2') using whichever field the previous question was actually asking
    about — a bare number carries no field name of its own, so without this
    context it's silently dropped and the same question gets re-asked."""

    fields = extract_fields(text)
    if not fields:
        bare_number = _BARE_NUMBER_RE.match(text)
        if bare_number and pending_field in ("rooms", "budget_max"):
            fields[pending_field] = int(bare_number.group(1))
    return fields


def heuristic_reply(
    conversation_history: list[dict[str, Any]],
    user_message: str,
    known_fields: dict[str, Any] | None = None,
) -> DialogueResult:
    # Replay the whole conversation chronologically, tracking which field
    # each bot question was asking about, so a bare-number answer anywhere
    # in the history (not just the current turn) resolves to the right
    # field instead of being lost on every subsequent turn. Seeded with
    # known_fields first (e.g. already picked via the button menu, which
    # never writes to conversation_history) so those are never re-asked.
    known: dict[str, Any] = dict(known_fields or {})
    pending_field: str | None = None
    for msg in conversation_history:
        content = msg.get("content")
        if not isinstance(content, str):
            continue
        if msg.get("role") == "assistant":
            pending_field = _field_asked_by(content)
        elif msg.get("role") == "user":
            for key, value in _extract_with_pending(content, pending_field).items():
                known.setdefault(key, value)

    fields = _extract_with_pending(user_message, pending_field)
    known.update(fields)
    # Classify against everything known so far (including fields picked via
    # the button menu or earlier turns), not just this message's own
    # extracted fields -- otherwise a turn that only supplies the phone
    # (budget already set by a button earlier) sees no budget_max in
    # `fields` alone and gets explicitly classified "cold", overriding the
    # correct "warm" even though both fields are actually present.
    classification = classify(known, user_message)

    next_question = None
    for key, question in _QUESTIONS_ORDER:
        if key not in known:
            next_question = question
            break

    if fields:
        reply = "Дякую, записав! "
        if "phone" in fields:
            # Echo the number back so a typo is immediately visible to the
            # client, instead of silently saving a wrong number.
            reply += f"Номер телефону збережено: {fields['phone']}. "
        reply += next_question or "Зараз підберу варіанти під ваш запит."
    else:
        reply = next_question or "Розкажіть, будь ласка, детальніше про ваш запит."

    history = list(conversation_history) + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    return DialogueResult(
        reply_text=reply,
        profile_updates=fields,
        classification=classification,
        conversation_history=history,
    )
