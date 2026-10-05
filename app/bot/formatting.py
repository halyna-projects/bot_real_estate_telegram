from __future__ import annotations

from app.models import Lead, Property, PropertySource, ReactionType

_SOURCE_LABELS = {
    PropertySource.INTERNAL: "Sopstvena baza",
    PropertySource.RIELTOR_UA: "RIELTOR.UA",
}

_REACTION_LABELS = {
    ReactionType.INTERESTED: "Zanima me",
    ReactionType.WANT_VIEWING: "Želim razgledanje",
    ReactionType.NOT_SUITABLE: "Ne odgovara",
}


def format_property_card(property_: Property) -> str:
    lines = [f"🏠 <b>{property_.title}</b>"]
    location = property_.city
    if property_.district:
        location += f", {property_.district}"
    lines.append(f"📍 {location}")

    details = []
    if property_.rooms:
        details.append(f"{property_.rooms} sob.")
    if property_.area_sqm:
        details.append(f"{property_.area_sqm:g} m²")
    if details:
        lines.append(" · ".join(details))

    lines.append(f"💰 {property_.price:,} {property_.currency}".replace(",", " "))
    lines.append(f"Izvor: {_SOURCE_LABELS.get(property_.source, property_.source)}")

    if property_.url:
        lines.append(f'<a href="{property_.url}">Više detalja</a>')

    return "\n".join(lines)


def format_reaction_confirmation(property_: Property, reaction: ReactionType) -> str:
    label = _REACTION_LABELS[reaction]
    return f"{format_property_card(property_)}\n\n✅ Vaša reakcija: <b>{label}</b>"


def format_lead_summary_for_realtor(lead: Lead) -> str:
    temp_emoji = {"hot": "🔥", "warm": "🌤", "cold": "❄️"}.get(
        lead.temperature.value if lead.temperature else "", ""
    )
    name = lead.full_name or lead.telegram_username or f"ID {lead.telegram_user_id}"
    parts = [f"{temp_emoji} Novi lead: <b>{name}</b>"]
    if lead.deal_type:
        parts.append(f"Posao: {lead.deal_type.value}")
    if lead.city:
        parts.append(f"Grad: {lead.city}")
    if lead.budget_max:
        parts.append(f"Budžet: do {lead.budget_max:,} {lead.budget_currency}".replace(",", " "))
    if lead.phone:
        parts.append(f"Telefon: {lead.phone}")
    return " · ".join(parts)
