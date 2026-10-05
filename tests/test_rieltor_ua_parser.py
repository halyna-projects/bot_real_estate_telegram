from app.search.rieltor_ua import parse_listing_page

SAMPLE_HTML = """
<html><body>
<div class="offer-card">
  <a href="/offers/12345/">
    <h3 class="offer-title">вул. Антоновича, 3к, 88м²</h3>
    <div class="offer-price">$115 000</div>
    <div class="offer-rooms">3 кімнати</div>
    <div class="offer-area">88 м²</div>
    <div class="offer-district">Печерський район</div>
  </a>
</div>
<div class="offer-card">
  <a href="https://rieltor.ua/offers/67890/">
    <h3 class="offer-title">пр-т Перемоги, 1к, 42м²</h3>
    <div class="offer-price">68 000 грн</div>
  </a>
</div>
<div class="offer-card">
  <!-- malformed card without a link, must be skipped gracefully -->
  <span>no link here</span>
</div>
</body></html>
"""


def test_parse_listing_page_extracts_expected_fields():
    listings = parse_listing_page(SAMPLE_HTML, city="Киев")
    assert len(listings) == 2

    first = listings[0]
    assert first.external_id == "12345"
    assert first.price == 115000
    assert first.currency == "USD"
    assert first.rooms == 3
    assert first.area_sqm == 88.0
    assert first.district == "Печерський район"

    second = listings[1]
    assert second.external_id == "67890"
    assert second.price == 68000
    assert second.currency == "UAH"
    assert second.url.startswith("https://rieltor.ua")


def test_parse_listing_page_ignores_malformed_cards():
    listings = parse_listing_page("<div class='offer-card'></div>", city="Киев")
    assert listings == []
