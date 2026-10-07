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
    "rent": re.compile(r"rent|renting|lease", re.IGNORECASE),
    "sell": re.compile(r"sell|selling|sale", re.IGNORECASE),
    "buy": re.compile(r"buy|buying|purchase", re.IGNORECASE),
}

_PROPERTY_TYPE_PATTERNS = {
    "house": re.compile(r"house|cottage|townhouse", re.IGNORECASE),
    "commercial": re.compile(r"commercial|office|retail|shop", re.IGNORECASE),
    "land": re.compile(r"\bland\b|\blot\b|acreage", re.IGNORECASE),
    "apartment": re.compile(r"apartment|condo|flat", re.IGNORECASE),
}

_CITY_PATTERNS = {
    "Toronto": re.compile(r"toronto", re.IGNORECASE),
    "Calgary": re.compile(r"calgary", re.IGNORECASE),
}

_ROOMS_RE = re.compile(r"(\d+)\s*[-]?\s*(bed|bedroom|br)s?\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(\+1\d{10}|\+\d{8,15}|\d{10})")
_BUDGET_RE = re.compile(
    r"(?P<amount>\d[\d\s,]{2,})\s*(?P<currency>cad|c\$|usd|us\$|\$|eur|€)?", re.IGNORECASE
)
_URGENT_RE = re.compile(r"urgent|asap|this week|right away|immediately|as soon as possible", re.IGNORECASE)

_CURRENCY_MAP = {
    "$": "CAD",
    "cad": "CAD",
    "c$": "CAD",
    "usd": "USD",
    "us$": "USD",
    "eur": "EUR",
    "€": "EUR",
}

_QUESTIONS_ORDER = [
    ("deal_type", "Just to confirm: are you looking to buy, rent, or sell?"),
    ("city", "Which city are we searching in (Toronto or Calgary)?"),
    ("property_type", "What type of property are you interested in: apartment, house, commercial, or land?"),
    ("rooms", "How many bedrooms do you need?"),
    ("budget_max", "What's your approximate budget?"),
    ("phone", "Please leave a phone number so we can reach you."),
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
    amount_digits = budget_match.group("amount").replace(" ", "").replace(",", "") if budget_match else ""
    if budget_match and not budget_overlaps_phone and len(amount_digits) >= 3:
        fields["budget_max"] = int(amount_digits)
        currency = budget_match.group("currency")
        if currency:
            fields["budget_currency"] = _CURRENCY_MAP.get(currency.lower(), "CAD")

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
        "urgency": "urgent" if is_urgent else "not specified",
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
        reply = "Thanks, got it! "
        if "phone" in fields:
            # Echo the number back so a typo is immediately visible to the
            # client, instead of silently saving a wrong number.
            reply += f"Phone number saved: {fields['phone']}. "
        reply += next_question or "I'll find matching listings for your request right away."
    else:
        reply = next_question or "Please tell me more about what you're looking for."

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
