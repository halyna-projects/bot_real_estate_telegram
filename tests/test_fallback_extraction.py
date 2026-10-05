from app.ai.fallback import classify, extract_fields, heuristic_reply
from app.ai.prompts import GREETING_MESSAGE


def test_extract_deal_type_and_city():
    fields = extract_fields("Хочу купить квартиру в Киеве")
    assert fields["deal_type"] == "buy"
    assert fields["property_type"] == "apartment"
    assert fields["city"] == "Киев"


def test_extract_rooms_budget_phone():
    fields = extract_fields("Нужно 2 комнаты, бюджет 95000 usd, телефон +380501234567")
    assert fields["rooms"] == 2
    assert fields["budget_max"] == 95000
    assert fields["budget_currency"] == "USD"
    assert fields["phone"] == "+380501234567"


def test_classify_hot_when_urgent_and_has_core_data():
    fields = {"budget_max": 95000, "phone": "+380501234567"}
    result = classify(fields, "Нужно срочно, на этой неделе")
    assert result["temperature"] == "hot"


def test_classify_cold_without_core_data():
    result = classify({}, "просто смотрю варианты")
    assert result is None


def test_heuristic_reply_asks_for_missing_field():
    result = heuristic_reply([], "Хочу купить квартиру")
    assert result.profile_updates["deal_type"] == "buy"
    assert "город" in result.reply_text.lower() or "киев" in result.reply_text.lower()


def test_heuristic_reply_understands_bare_number_answering_rooms_question():
    # Regression: a bare "2" in reply to "Сколько комнат нужно?" used to be
    # silently dropped, so the bot re-asked the same question forever.
    history = [{"role": "assistant", "content": "Сколько комнат нужно?"}]
    result = heuristic_reply(history, "2")
    assert result.profile_updates["rooms"] == 2
    assert "комнат" not in result.reply_text.lower()


def test_heuristic_reply_understands_bare_number_answering_budget_question():
    history = [{"role": "assistant", "content": "Какой ориентировочный бюджет?"}]
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
    # time), so the bot re-asked "Сколько комнат нужно?" after every
    # subsequent answer instead of moving on.
    history = [
        {"role": "assistant", "content": "Сколько комнат нужно?"},
        {"role": "user", "content": "2"},
        {"role": "assistant", "content": "Оставьте, пожалуйста, номер телефона для связи."},
    ]
    result = heuristic_reply(history, "0501234567")
    assert "комнат" not in result.reply_text.lower()


def test_heuristic_reply_does_not_misread_its_own_greeting_as_an_answer():
    # Regression: the greeting itself asks "покупка, аренда или продажа?",
    # which used to be re-scanned as if the client had said it, making the
    # bot think deal_type (and everything else) was already known after a
    # single real answer, and jump straight to "Сейчас подберу варианты".
    history = [{"role": "assistant", "content": GREETING_MESSAGE}]
    result = heuristic_reply(history, "покупка")
    assert result.profile_updates["deal_type"] == "buy"
    assert "город" in result.reply_text.lower()
    assert "сейчас подберу" not in result.reply_text.lower()
