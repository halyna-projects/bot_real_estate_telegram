from app.ai.fallback import classify, extract_fields, heuristic_reply
from app.ai.prompts import GREETING_MESSAGE


def test_extract_deal_type_and_city():
    fields = extract_fields("Хочу купити квартиру у Києві")
    assert fields["deal_type"] == "buy"
    assert fields["property_type"] == "apartment"
    assert fields["city"] == "Київ"


def test_extract_rooms_budget_phone():
    fields = extract_fields("Потрібно 2 кімнати, бюджет 95000 usd, телефон +380501234567")
    assert fields["rooms"] == 2
    assert fields["budget_max"] == 95000
    assert fields["budget_currency"] == "USD"
    assert fields["phone"] == "+380501234567"


def test_extract_bare_phone_does_not_also_set_a_bogus_budget():
    # Regression: a message that's just a phone number (e.g. answering the
    # phone question as free text) used to also match the budget regex
    # against the same digits, setting a nonsensical budget like
    # 380501234567 USD.
    fields = extract_fields("+380501234567")
    assert fields["phone"] == "+380501234567"
    assert "budget_max" not in fields


def test_classify_hot_when_urgent_and_has_core_data():
    fields = {"budget_max": 95000, "phone": "+380501234567"}
    result = classify(fields, "Потрібно терміново, цього тижня")
    assert result["temperature"] == "hot"


def test_classify_cold_without_core_data():
    result = classify({}, "просто дивлюсь варіанти")
    assert result is None


def test_heuristic_reply_asks_for_missing_field():
    result = heuristic_reply([], "Хочу купити квартиру")
    assert result.profile_updates["deal_type"] == "buy"
    assert "місто" in result.reply_text.lower() or "київ" in result.reply_text.lower()


def test_heuristic_reply_understands_bare_number_answering_rooms_question():
    # Regression: a bare "2" in reply to "Скільки кімнат потрібно?" used to be
    # silently dropped, so the bot re-asked the same question forever.
    history = [{"role": "assistant", "content": "Скільки кімнат потрібно?"}]
    result = heuristic_reply(history, "2")
    assert result.profile_updates["rooms"] == 2
    assert "кімнат" not in result.reply_text.lower()


def test_heuristic_reply_understands_bare_number_answering_budget_question():
    history = [{"role": "assistant", "content": "Який орієнтовний бюджет?"}]
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
    # time), so the bot re-asked "Скільки кімнат потрібно?" after every
    # subsequent answer instead of moving on.
    history = [
        {"role": "assistant", "content": "Скільки кімнат потрібно?"},
        {"role": "user", "content": "2"},
        {"role": "assistant", "content": "Залиште, будь ласка, номер телефону для зв'язку."},
    ]
    result = heuristic_reply(history, "0501234567")
    assert "кімнат" not in result.reply_text.lower()


def test_heuristic_reply_honors_fields_already_set_via_the_button_menu():
    # Regression: the button menu writes straight onto the Lead row and
    # never touches conversation_history, so a lead that picked deal_type/
    # city/etc. via buttons and then typed their phone as free text (an
    # explicitly supported alternative to the "share contact" button) used
    # to have heuristic_reply re-ask "купівля, оренда чи продаж?" as if
    # nothing had been answered yet, because it only knew about fields
    # mentioned in conversation_history.
    known_fields = {
        "deal_type": "buy",
        "city": "Львів",
        "property_type": "apartment",
        "rooms": 2,
        "budget_max": 100000,
    }
    history = [{"role": "assistant", "content": "Залиште, будь ласка, номер телефону для зв'язку."}]
    result = heuristic_reply(history, "+380671234567", known_fields)
    assert result.profile_updates["phone"] == "+380671234567"
    assert "купівля" not in result.reply_text.lower()
    assert "зараз підберу" in result.reply_text.lower()
    # Regression: classify() used to only see this turn's own extracted
    # fields ({"phone": ...}), missing the budget_max set earlier via the
    # button menu, so it explicitly classified the lead "cold" even though
    # phone + budget were both actually present -- overriding what should
    # have been "warm".
    assert result.classification["temperature"] == "warm"


def test_heuristic_reply_does_not_misread_its_own_greeting_as_an_answer():
    # Regression: the greeting itself asks "купівля, оренда чи продаж?",
    # which used to be re-scanned as if the client had said it, making the
    # bot think deal_type (and everything else) was already known after a
    # single real answer, and jump straight to "Зараз підберу варіанти".
    history = [{"role": "assistant", "content": GREETING_MESSAGE}]
    result = heuristic_reply(history, "купівля")
    assert result.profile_updates["deal_type"] == "buy"
    assert "міст" in result.reply_text.lower()
    assert "зараз підберу" not in result.reply_text.lower()
