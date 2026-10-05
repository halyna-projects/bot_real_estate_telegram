from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.models import DealType, Property, PropertyType, ReactionType

REACTION_LABELS = {
    ReactionType.INTERESTED: "👍 Interested",
    ReactionType.WANT_VIEWING: "📅 Want a viewing",
    ReactionType.NOT_SUITABLE: "👎 Not a fit",
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
    DealType.BUY: "🏠 Buy",
    DealType.RENT: "🔑 Rent",
    DealType.SELL: "💰 Sell",
}

CITY_OPTIONS = ["Toronto", "Calgary"]

DISTRICTS_BY_CITY = {
    "Toronto": ["Downtown", "North York", "Scarborough", "Etobicoke", "Yorkville"],
    "Calgary": ["Downtown", "Beltline", "Kensington", "Inglewood"],
}

PROPERTY_TYPE_MENU_LABELS = {
    PropertyType.APARTMENT: "Apartment",
    PropertyType.HOUSE: "House",
    PropertyType.COMMERCIAL: "Commercial",
    PropertyType.LAND: "Land",
}

ROOMS_OPTIONS = [1, 2, 3, 4]

# (upper bound of the range, button label, currency) per deal type; Canada
# uses CAD everywhere, rent is monthly, buy/sell is a one-off price.
BUDGET_RANGES = {
    DealType.RENT: [
        (1_800, "up to $1,800/mo", "CAD"),
        (2_800, "$1,800–2,800/mo", "CAD"),
        (4_000, "$2,800–4,000/mo", "CAD"),
        (6_000, "over $4,000/mo", "CAD"),
    ],
    "default": [
        (500_000, "up to $500,000", "CAD"),
        (800_000, "$500,000–800,000", "CAD"),
        (1_200_000, "$800,000–1,200,000", "CAD"),
        (1_800_000, "over $1,200,000", "CAD"),
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
    buttons.append([_menu_button("Any neighborhood", "district", "any")])
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
        keyboard=[[KeyboardButton(text="📱 Share phone number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
