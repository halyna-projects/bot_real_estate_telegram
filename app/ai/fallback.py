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
    "rent": re.compile(r"аренд|сн(ять|яла|иму)|найм", re.IGNORECASE),
    "sell": re.compile(r"продат|продаж", re.IGNORECASE),
    "buy": re.compile(r"купит|покупк|приобрест", re.IGNORECASE),
}

_PROPERTY_TYPE_PATTERNS = {
    "house": re.compile(r"дом[а-я]*|коттедж", re.IGNORECASE),
    "commercial": re.compile(r"коммерц|офис|магазин", re.IGNORECASE),
    "land": re.compile(r"земл[а-я]*|участ", re.IGNORECASE),
    "apartment": re.compile(r"квартир", re.IGNORECASE),
}

_CITY_PATTERNS = {
    "Подгорица": re.compile(r"подгориц|podgorica", re.IGNORECASE),
    "Будва": re.compile(r"будв|budva", re.IGNORECASE),
    "Котор": re.compile(r"котор|kotor", re.IGNORECASE),
    "Тиват": re.compile(r"тиват|tivat", re.IGNORECASE),
}

_ROOMS_RE = re.compile(r"(\d+)\s*[-]?\s*к(омн|омнат|)")
_PHONE_RE = re.compile(r"(\+382\d{7,8}|\+\d{8,15}|0\d{8,9})")
_BUDGET_RE = re.compile(
    r"(?P<amount>\d[\d\s]{2,})\s*(?P<currency>usd|\$|грн|uah|eur|евро|€)?", re.IGNORECASE
)
_URGENT_RE = re.compile(r"срочно|быстро|на этой неделе|немедленно|как можно скорее", re.IGNORECASE)

_CURRENCY_MAP = {
    "$": "USD",
    "usd": "USD",
    "грн": "UAH",
    "uah": "UAH",
    "eur": "EUR",
    "евро": "EUR",
    "€": "EUR",
}

_QUESTIONS_ORDER = [
    ("deal_type", "Уточните, пожалуйста: покупка, аренда или продажа?"),
    ("city", "В каком городе ищем (Подгорица, Будва, Котор или Тиват)?"),
    ("property_type", "Какой тип объекта интересует: квартира, дом, коммерция или земля?"),
    ("rooms", "Сколько комнат нужно?"),
    ("budget_max", "Какой ориентировочный бюджет?"),
    ("phone", "Оставьте, пожалуйста, номер телефона для связи."),
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
    if budget_match and len(budget_match.group("amount").replace(" ", "")) >= 3:
        amount = int(budget_match.group("amount").replace(" ", ""))
        fields["budget_max"] = amount
        currency = budget_match.group("currency")
        if currency:
            fields["budget_currency"] = _CURRENCY_MAP.get(currency.lower(), "EUR")

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
        "urgency": "срочно" if is_urgent else "не указано",
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
    conversation_history: list[dict[str, Any]], user_message: str
) -> DialogueResult:
    # Replay the whole conversation chronologically, tracking which field
    # each bot question was asking about, so a bare-number answer anywhere
    # in the history (not just the current turn) resolves to the right
    # field instead of being lost on every subsequent turn.
    known: dict[str, Any] = {}
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
    classification = classify(fields, user_message)
    known.update(fields)

    next_question = None
    for key, question in _QUESTIONS_ORDER:
        if key not in known:
            next_question = question
            break

    if fields:
        reply = "Спасибо, записал! "
        reply += next_question or "Сейчас подберу варианты под ваш запрос."
    else:
        reply = next_question or "Расскажите, пожалуйста, подробнее о вашем запросе."

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
