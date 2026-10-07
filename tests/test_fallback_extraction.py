from app.ai.fallback import classify, extract_fields, heuristic_reply
from app.ai.prompts import GREETING_MESSAGE


def test_extract_deal_type_and_city():
    fields = extract_fields("I want to buy an apartment in Toronto")
    assert fields["deal_type"] == "buy"
    assert fields["property_type"] == "apartment"
    assert fields["city"] == "Toronto"


def test_extract_rooms_budget_phone():
    fields = extract_fields("Need 2 bedrooms, budget 95000 usd, phone +380501234567")
    assert fields["rooms"] == 2
    assert fields["budget_max"] == 95000
    assert fields["budget_currency"] == "USD"
    assert fields["phone"] == "+380501234567"


def test_extract_bare_phone_does_not_also_set_a_bogus_budget():
    # Regression: a message that's just a phone number (e.g. answering the
    # phone question as free text) used to also match the budget regex
    # against the same digits, setting a nonsensical budget like
    # 4165551234 CAD.
    fields = extract_fields("+14165551234")
    assert fields["phone"] == "+14165551234"
    assert "budget_max" not in fields


def test_classify_hot_when_urgent_and_has_core_data():
    fields = {"budget_max": 95000, "phone": "+14165551234"}
    result = classify(fields, "Need it urgently, this week")
    assert result["temperature"] == "hot"


def test_classify_cold_without_core_data():
    result = classify({}, "just browsing listings")
    assert result is None


def test_heuristic_reply_asks_for_missing_field():
    result = heuristic_reply([], "I want to buy an apartment")
    assert result.profile_updates["deal_type"] == "buy"
    assert "city" in result.reply_text.lower() or "toronto" in result.reply_text.lower()


def test_heuristic_reply_understands_bare_number_answering_rooms_question():
    # Regression: a bare "2" in reply to "How many bedrooms do you need?"
    # used to be silently dropped, so the bot re-asked the same question
    # forever.
    history = [{"role": "assistant", "content": "How many bedrooms do you need?"}]
    result = heuristic_reply(history, "2")
    assert result.profile_updates["rooms"] == 2
    assert "bedrooms do you need" not in result.reply_text.lower()


def test_heuristic_reply_understands_bare_number_answering_budget_question():
    history = [{"role": "assistant", "content": "What's your approximate budget?"}]
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
    # time), so the bot re-asked "How many bedrooms do you need?" after
    # every subsequent answer instead of moving on.
    history = [
        {"role": "assistant", "content": "How many bedrooms do you need?"},
        {"role": "user", "content": "2"},
        {"role": "assistant", "content": "Please leave a phone number so we can reach you."},
    ]
    result = heuristic_reply(history, "4165551234")
    assert "bedrooms do you need" not in result.reply_text.lower()


def test_heuristic_reply_honors_fields_already_set_via_the_button_menu():
    # Regression: the button menu writes straight onto the Lead row and
    # never touches conversation_history, so a lead that picked deal_type/
    # city/etc. via buttons and then typed their phone as free text (an
    # explicitly supported alternative to the "share contact" button) used
    # to have heuristic_reply re-ask "buy, rent, or sell?" as if nothing
    # had been answered yet, because it only knew about fields mentioned
    # in conversation_history.
    known_fields = {
        "deal_type": "buy",
        "city": "Calgary",
        "property_type": "apartment",
        "rooms": 2,
        "budget_max": 600000,
    }
    history = [{"role": "assistant", "content": "Please leave a phone number so we can reach you."}]
    result = heuristic_reply(history, "+14035551234", known_fields)
    assert result.profile_updates["phone"] == "+14035551234"
    assert "buy, rent" not in result.reply_text.lower()
    assert "right away" in result.reply_text.lower()
    # Regression: classify() used to only see this turn's own extracted
    # fields ({"phone": ...}), missing the budget_max set earlier via the
    # button menu, so it explicitly classified the lead "cold" even though
    # phone + budget were both actually present -- overriding what should
    # have been "warm".
    assert result.classification["temperature"] == "warm"


def test_heuristic_reply_does_not_misread_its_own_greeting_as_an_answer():
    # Regression: the greeting itself asks "buying, renting, or selling?",
    # which used to be re-scanned as if the client had said it, making the
    # bot think deal_type (and everything else) was already known after a
    # single real answer, and jump straight to "I'll find matching listings".
    history = [{"role": "assistant", "content": GREETING_MESSAGE}]
    result = heuristic_reply(history, "buying")
    assert result.profile_updates["deal_type"] == "buy"
    assert "city" in result.reply_text.lower()
    assert "right away" not in result.reply_text.lower()
