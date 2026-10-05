from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.models import DealType, Property, PropertyType, ReactionType

REACTION_LABELS = {
    ReactionType.INTERESTED: "👍 Zanima me",
    ReactionType.WANT_VIEWING: "📅 Želim razgledanje",
    ReactionType.NOT_SUITABLE: "👎 Ne odgovara",
}


def reaction_callback_data(property_id: int, reaction: ReactionType) -> str:
    return f"react:{property_id}:{reaction.value}"


def parse_reaction_callback(data: str) -> tuple[int, ReactionType]:
    _, property_id, reaction_value = data.split(":")
    return int(property_id), ReactionType(reaction_value)


def property_reaction_keyboard(property_: Property) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=label, callback_data=reaction_callback_data(property_.id, reaction)
        )
        for reaction, label in REACTION_LABELS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


# --- Guided menu (button-driven qualification, alternative to free text) ---

DEAL_TYPE_MENU_LABELS = {
    DealType.BUY: "🏠 Kupovina",
    DealType.RENT: "🔑 Zakup",
    DealType.SELL: "💰 Prodaja",
}

CITY_OPTIONS = ["Podgorica", "Budva", "Kotor", "Tivat"]

DISTRICTS_BY_CITY = {
    "Podgorica": ["Centar", "Gorica", "Zapad", "Stari aerodrom", "Blok 5/6"],
    "Budva": ["Stari grad", "Bečići", "Rafailovići", "Petrovac"],
    "Kotor": ["Stari grad", "Dobrota", "Muo", "Perast"],
    "Tivat": ["Centar", "Donja Lastva", "Krašići"],
}

PROPERTY_TYPE_MENU_LABELS = {
    PropertyType.APARTMENT: "Stan",
    PropertyType.HOUSE: "Kuća",
    PropertyType.COMMERCIAL: "Poslovni prostor",
    PropertyType.LAND: "Zemljište",
}

ROOMS_OPTIONS = [1, 2, 3, 4]

# (upper bound of the range, button label, currency) per deal type; Montenegro
# uses EUR everywhere, rent is monthly, buy/sell is a one-off price.
BUDGET_RANGES = {
    DealType.RENT: [
        (300, "do 300 €/mes", "EUR"),
        (600, "300–600 €/mes", "EUR"),
        (1_000, "600–1 000 €/mes", "EUR"),
        (2_000, "preko 1 000 €/mes", "EUR"),
    ],
    "default": [
        (50_000, "do €50 000", "EUR"),
        (100_000, "€50 000–100 000", "EUR"),
        (200_000, "€100 000–200 000", "EUR"),
        (300_000, "preko €200 000", "EUR"),
    ],
}


def _menu_button(text: str, field: str, value: object) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=f"menu:{field}:{value}")


def parse_menu_callback(data: str) -> tuple[str, str]:
    _, field, value = data.split(":", 2)
    return field, value


def deal_type_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [_menu_button(label, "deal_type", deal_type.value)]
        for deal_type, label in DEAL_TYPE_MENU_LABELS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def city_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [[_menu_button(city, "city", city)] for city in CITY_OPTIONS]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def district_menu_keyboard(city: str) -> InlineKeyboardMarkup:
    buttons = [[_menu_button(d, "district", d)] for d in DISTRICTS_BY_CITY.get(city, [])]
    buttons.append([_menu_button("Bilo koja opština", "district", "any")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def property_type_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        _menu_button(label, "property_type", property_type.value)
        for property_type, label in PROPERTY_TYPE_MENU_LABELS.items()
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rooms_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        _menu_button(f"{n}+" if n == ROOMS_OPTIONS[-1] else str(n), "rooms", n)
        for n in ROOMS_OPTIONS
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def budget_menu_keyboard(deal_type: DealType) -> InlineKeyboardMarkup:
    ranges = BUDGET_RANGES.get(deal_type, BUDGET_RANGES["default"])
    buttons = [
        [_menu_button(label, "budget", f"{amount}_{currency}")]
        for amount, label, currency in ranges
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def phone_share_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Pošalji broj", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
