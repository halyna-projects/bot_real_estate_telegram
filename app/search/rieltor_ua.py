"""Best-effort parser/adapter for RIELTOR.UA search results.

MVP constraints from the product spec: search is limited to Kyiv/Lviv and a
$100k price cap. The live site markup can change at any time, so parsing is
isolated in `parse_listing_page()` (pure function, easy to unit-test against
a saved HTML fixture) while `fetch_listings()` does the actual network call
and degrades gracefully (returns an empty list) on any network or parsing
error instead of breaking the client's search flow.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.models import DealType, Lead, PropertyType

logger = logging.getLogger(__name__)

_DEAL_TYPE_SLUG = {DealType.BUY: "prodazha", DealType.RENT: "arenda", DealType.SELL: "prodazha"}
_PROPERTY_TYPE_SLUG = {
    PropertyType.APARTMENT: "kvartiry",
    PropertyType.HOUSE: "doma",
    PropertyType.COMMERCIAL: "kommercheskaya-nedvizhimost",
    PropertyType.LAND: "zemelnye-uchastki",
}

_PRICE_RE = re.compile(r"[\d\s]+")


@dataclass
class ScrapedListing:
    external_id: str
    title: str
    city: str
    district: str | None
    rooms: int | None
    area_sqm: float | None
    price: int
    currency: str
    url: str
    description: str | None = None


def build_search_url(lead: Lead) -> str | None:
    settings = get_settings()
    if not lead.city or lead.city not in settings.rieltor_ua_allowed_cities_list:
        return None

    deal_slug = _DEAL_TYPE_SLUG.get(lead.deal_type, "prodazha")
    type_slug = _PROPERTY_TYPE_SLUG.get(lead.property_type, "kvartiry")

    params = {}
    if lead.rooms:
        params["rooms"] = lead.rooms
    if lead.budget_max:
        params["price_max"] = min(lead.budget_max, settings.rieltor_ua_max_price_usd)
    if lead.district:
        params["district"] = lead.district

    base = f"{settings.rieltor_ua_base_url}/{deal_slug}-{type_slug}-{lead.city.lower()}/"
    query = urlencode(params)
    return f"{base}?{query}" if query else base


def parse_listing_page(html: str, city: str) -> list[ScrapedListing]:
    """Parse a RIELTOR.UA search results page into structured listings.

    Selectors are best-effort against the public listing card markup and are
    intentionally defensive: any card missing required fields is skipped
    rather than raising, so a partial markup change degrades gracefully
    instead of taking down the whole search.
    """

    soup = BeautifulSoup(html, "lxml")
    listings: list[ScrapedListing] = []

    cards = soup.select("[data-qa='offer-card'], .offer-card, .listing-card")
    for card in cards:
        try:
            listing = _parse_card(card, city)
        except Exception:  # noqa: BLE001 - defensive scraping, log and skip
            logger.debug("Skipping unparsable RIELTOR.UA card", exc_info=True)
            continue
        if listing:
            listings.append(listing)

    return listings


def _parse_card(card, city: str) -> ScrapedListing | None:
    link = card.select_one("a")
    if not link or not link.get("href"):
        return None
    url = link["href"]
    external_id = url.rstrip("/").split("/")[-1]

    title_el = card.select_one("[data-qa='offer-title'], .offer-title, h3, h2")
    title = title_el.get_text(strip=True) if title_el else "Объявление без названия"

    price_el = card.select_one("[data-qa='offer-price'], .offer-price, .price")
    price = 0
    currency = "USD"
    if price_el:
        raw = price_el.get_text(strip=True)
        match = _PRICE_RE.search(raw)
        if match:
            price = int(match.group(0).replace(" ", "").replace("\xa0", ""))
        if "грн" in raw.lower():
            currency = "UAH"
        elif "€" in raw:
            currency = "EUR"

    rooms_el = card.select_one("[data-qa='offer-rooms'], .offer-rooms")
    rooms = None
    if rooms_el:
        rooms_match = re.search(r"\d+", rooms_el.get_text())
        if rooms_match:
            rooms = int(rooms_match.group(0))

    area_el = card.select_one("[data-qa='offer-area'], .offer-area")
    area_sqm = None
    if area_el:
        area_match = re.search(r"[\d.]+", area_el.get_text())
        if area_match:
            area_sqm = float(area_match.group(0))

    district_el = card.select_one("[data-qa='offer-district'], .offer-district")
    district = district_el.get_text(strip=True) if district_el else None

    if not price:
        return None

    return ScrapedListing(
        external_id=external_id,
        title=title,
        city=city,
        district=district,
        rooms=rooms,
        area_sqm=area_sqm,
        price=price,
        currency=currency,
        url=url if url.startswith("http") else f"{get_settings().rieltor_ua_base_url}{url}",
    )


async def fetch_listings(lead: Lead) -> list[ScrapedListing]:
    """Fetch and parse live RIELTOR.UA listings for a lead's criteria.

    Returns an empty list (never raises) when the city is unsupported, the
    network call fails, or the page markup can't be parsed — the caller
    (hybrid search) simply falls back to internal inventory in that case.
    """

    settings = get_settings()
    url = build_search_url(lead)
    if not url:
        return []

    try:
        async with httpx.AsyncClient(timeout=settings.rieltor_ua_request_timeout) as client:
            response = await client.get(
                url, headers={"User-Agent": "Mozilla/5.0 (compatible; AIRealtorBot/1.0)"}
            )
            response.raise_for_status()
    except httpx.HTTPError:
        logger.warning("RIELTOR.UA request failed for %s", url, exc_info=True)
        return []

    listings = parse_listing_page(response.text, lead.city)
    return [item for item in listings if item.price <= settings.rieltor_ua_max_price_usd]
