from app.models import DealType, Lead, LeadStatus, PropertyType, Temperature
from app.services.leads import reset_lead_for_new_conversation
from app.services.qualification import (
    apply_classification,
    apply_profile_updates,
    heuristic_classification,
)


def test_apply_profile_updates_sets_valid_enum_fields():
    lead = Lead(telegram_user_id=1)
    apply_profile_updates(
        lead,
        {
            "deal_type": "buy",
            "property_type": "apartment",
            "city": "Toronto",
            "rooms": 2,
            "budget_max": 650000,
            "phone": "+14165551234",
        },
    )
    assert lead.deal_type == DealType.BUY
    assert lead.property_type == PropertyType.APARTMENT
    assert lead.city == "Toronto"
    assert lead.rooms == 2
    assert lead.budget_max == 650000
    assert lead.phone == "+14165551234"


def test_apply_profile_updates_ignores_invalid_enum_value():
    lead = Lead(telegram_user_id=1)
    apply_profile_updates(lead, {"deal_type": "not-a-real-type"})
    assert lead.deal_type is None


def test_reset_lead_for_new_conversation_clears_a_fully_qualified_profile():
    lead = Lead(telegram_user_id=1, status=LeadStatus.OFFERS_SENT)
    apply_profile_updates(
        lead,
        {
            "deal_type": "buy",
            "property_type": "apartment",
            "city": "Toronto",
            "rooms": 2,
            "budget_max": 650000,
            "phone": "+14165551234",
        },
    )
    lead.temperature = Temperature.HOT
    lead.conversation_history = [{"role": "user", "content": "2 bedrooms"}]
    assert lead.is_qualified()

    reset_lead_for_new_conversation(lead)

    assert lead.missing_required_fields() == [
        "deal_type",
        "city",
        "property_type",
        "rooms",
        "budget_max",
        "phone",
    ]
    assert lead.status == LeadStatus.NEW
    assert lead.temperature is None
    assert lead.conversation_history == []


def test_lead_missing_required_fields():
    lead = Lead(telegram_user_id=1)
    assert "city" in lead.missing_required_fields()
    assert not lead.is_qualified()

    apply_profile_updates(
        lead,
        {
            "deal_type": "buy",
            "city": "Toronto",
            "property_type": "apartment",
            "rooms": 2,
            "budget_max": 650000,
            "phone": "+14165551234",
        },
    )
    assert lead.is_qualified()


def test_apply_classification_sets_temperature_and_urgency():
    lead = Lead(telegram_user_id=1)
    apply_classification(lead, {"temperature": "hot", "urgency": "this week"})
    assert lead.temperature == Temperature.HOT
    assert lead.urgency == "this week"


def test_heuristic_classification_warm_when_phone_and_budget_present():
    lead = Lead(telegram_user_id=1, phone="+14165551234", budget_max=650000)
    assert heuristic_classification(lead) == Temperature.WARM


def test_heuristic_classification_cold_without_contact_info():
    lead = Lead(telegram_user_id=1)
    assert heuristic_classification(lead) == Temperature.COLD
