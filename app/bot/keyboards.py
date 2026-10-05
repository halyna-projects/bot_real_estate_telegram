from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.models import DealType, Property, PropertyType, ReactionType

REACTION_LABELS = {
    ReactionType.INTERESTED: "👍 Заинтересовало",
    ReactionType.WANT_VIEWING: "📅 Хочу просмотр",
    ReactionType.NOT_SUITABLE: "👎 Не подошло",
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
    DealType.BUY: "🏠 Покупка",
    DealType.RENT: "🔑 Аренда",
    DealType.SELL: "💰 Продажа",
}

CITY_OPTIONS = ["Киев", "Львов"]

DISTRICTS_BY_CITY = {
    "Киев": ["Шевченковский", "Печерский", "Соломенский", "Оболонский", "Дарницкий"],
    "Львов": ["Лычаковский", "Железнодорожный", "Галицкий", "Сыховский"],
}

PROPERTY_TYPE_MENU_LABELS = {
    PropertyType.APARTMENT: "Квартира",
    PropertyType.HOUSE: "Дом",
    PropertyType.COMMERCIAL: "Коммерция",
    PropertyType.LAND: "Земля",
}

ROOMS_OPTIONS = [1, 2, 3, 4]

# (upper bound of the range, button label, currency) per deal type; buy/sell
# share the USD "default" ranges, rent uses UAH ranges.
BUDGET_RANGES = {
    DealType.RENT: [
        (15_000, "до 15 000 грн", "UAH"),
        (30_000, "15 000–30 000 грн", "UAH"),
        (50_000, "30 000–50 000 грн", "UAH"),
        (80_000, "свыше 50 000 грн", "UAH"),
    ],
    "default": [
        (50_000, "до $50 000", "USD"),
        (100_000, "$50 000–100 000", "USD"),
        (200_000, "$100 000–200 000", "USD"),
        (300_000, "свыше $200 000", "USD"),
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
    buttons.append([_menu_button("Любой район", "district", "any")])
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
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
