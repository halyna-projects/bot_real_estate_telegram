from app.ai.fallback import classify, extract_fields, heuristic_reply
from app.ai.prompts import GREETING_MESSAGE


def test_extract_deal_type_and_city():
    fields = extract_fields("Želim da kupim stan u Podgorici")
    assert fields["deal_type"] == "buy"
    assert fields["property_type"] == "apartment"
    assert fields["city"] == "Podgorica"


def test_extract_rooms_budget_phone():
    fields = extract_fields("Potrebne su 2 sobe, budžet 95000 usd, telefon +380501234567")
    assert fields["rooms"] == 2
    assert fields["budget_max"] == 95000
    assert fields["budget_currency"] == "USD"
    assert fields["phone"] == "+380501234567"


def test_extract_bare_phone_does_not_also_set_a_bogus_budget():
    # Regression: a message that's just a phone number (e.g. answering the
    # phone question as free text) used to also match the budget regex
    # against the same digits, setting a nonsensical budget like
    # 38212345678 EUR.
    fields = extract_fields("+38212345678")
    assert fields["phone"] == "+38212345678"
    assert "budget_max" not in fields


def test_classify_hot_when_urgent_and_has_core_data():
    fields = {"budget_max": 95000, "phone": "+380501234567"}
    result = classify(fields, "Potrebno hitno, ove nedelje")
    assert result["temperature"] == "hot"


def test_classify_cold_without_core_data():
    result = classify({}, "samo gledam ponude")
    assert result is None


def test_heuristic_reply_asks_for_missing_field():
    result = heuristic_reply([], "Želim da kupim stan")
    assert result.profile_updates["deal_type"] == "buy"
    assert "grad" in result.reply_text.lower() or "podgoric" in result.reply_text.lower()


def test_heuristic_reply_understands_bare_number_answering_rooms_question():
    # Regression: a bare "2" in reply to "Koliko soba je potrebno?" used to
    # be silently dropped, so the bot re-asked the same question forever.
    history = [{"role": "assistant", "content": "Koliko soba je potrebno?"}]
    result = heuristic_reply(history, "2")
    assert result.profile_updates["rooms"] == 2
    assert "soba je potrebno" not in result.reply_text.lower()


def test_heuristic_reply_understands_bare_number_answering_budget_question():
    history = [{"role": "assistant", "content": "Koji je okvirni budžet?"}]
    result = heuristic_reply(history, "90000")
    assert result.profile_updates["budget_max"] == 90000


def test_heuristic_reply_ignores_bare_number_with_no_pending_question():
    result = heuristic_reply([], "2")
    assert "rooms" not in result.profile_updates
    assert "budget_max" not in result.profile_updates


def test_heuristic_reply_remembers_a_historical_bare_number_answer():
    # Regression: a bare "2" answering the rooms question several turns ago
    # used to be forgotten on later turns (the re-scan of history couldn't
    # tell it was answering "rooms" without knowing what was asked at the
    # time), so the bot re-asked "Koliko soba je potrebno?" after every
    # subsequent answer instead of moving on.
    history = [
        {"role": "assistant", "content": "Koliko soba je potrebno?"},
        {"role": "user", "content": "2"},
        {"role": "assistant", "content": "Ostavite, molim vas, broj telefona za kontakt."},
    ]
    result = heuristic_reply(history, "0501234567")
    assert "soba je potrebno" not in result.reply_text.lower()


def test_heuristic_reply_honors_fields_already_set_via_the_button_menu():
    # Regression: the button menu writes straight onto the Lead row and
    # never touches conversation_history, so a lead that picked deal_type/
    # city/etc. via buttons and then typed their phone as free text (an
    # explicitly supported alternative to the "share contact" button) used
    # to have heuristic_reply re-ask "kupovina, zakup ili prodaja?" as if
    # nothing had been answered yet, because it only knew about fields
    # mentioned in conversation_history.
    known_fields = {
        "deal_type": "buy",
        "city": "Budva",
        "property_type": "apartment",
        "rooms": 2,
        "budget_max": 100000,
    }
    history = [{"role": "assistant", "content": "Ostavite, molim vas, broj telefona za kontakt."}]
    result = heuristic_reply(history, "+38267123456", known_fields)
    assert result.profile_updates["phone"] == "+38267123456"
    assert "kupovina" not in result.reply_text.lower()
    assert "odmah ću pronaći" in result.reply_text.lower()


def test_heuristic_reply_does_not_misread_its_own_greeting_as_an_answer():
    # Regression: the greeting itself asks "kupovina, zakup ili prodaja?",
    # which used to be re-scanned as if the client had said it, making the
    # bot think deal_type (and everything else) was already known after a
    # single real answer, and jump straight to "Odmah ću pronaći ponude".
    history = [{"role": "assistant", "content": GREETING_MESSAGE}]
    result = heuristic_reply(history, "kupovina")
    assert result.profile_updates["deal_type"] == "buy"
    assert "grad" in result.reply_text.lower()
    assert "odmah ću pronaći" not in result.reply_text.lower()
