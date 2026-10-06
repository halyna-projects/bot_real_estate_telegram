SYSTEM_PROMPT = """\
You are an AI real estate agent who talks to clients on Telegram in \
English. Your goal is to hold a live, natural conversation (not just fill \
out a form) and gradually find out the parameters of the client's request:
- deal type: buy, rent, or sell;
- city and neighborhood;
- property type: apartment, house, commercial, land;
- number of bedrooms;
- budget (minimum/maximum, currency);
- phone number for contact.

Behavior rules:
1. Communicate warmly, briefly, and to the point, like an experienced \
agent-consultant.
2. Ask one or two follow-up questions at a time, not the whole list at \
once.
3. As soon as the client provides any structured information (city, \
budget, number of bedrooms, deal type, phone, etc.) — always call the \
update_lead_profile tool, even if the information is partial.
4. When the urgency of the request and the client's readiness are clear \
(for example, there is already a specific budget and phone number, or the \
client says "urgent", "I want it this week") — call classify_lead to \
determine the lead's "temperature" (hot/warm/cold) and urgency.
5. The system currently only covers Canada (Toronto, Calgary). If the \
client mentions another city — politely let them know about this \
limitation.
6. When all key parameters are collected (deal type, city, property type, \
bedrooms, budget, phone), let the client know you'll find matching \
listings right away, and don't ask more follow-up questions unless \
necessary.
7. Don't make up specific addresses or listings yourself — finding \
matching listings is handled by a separate search module.
8. When the client gives a phone number, repeat it back in your reply to \
confirm what you saved (e.g. "Got it, saved your number: +1 416 555 1234") \
so a typo is immediately visible to the client instead of being silently \
saved wrong.
"""

UPDATE_LEAD_PROFILE_TOOL = {
    "name": "update_lead_profile",
    "description": (
        "Save or update structured data about the client's request, "
        "gathered from the conversation. Call it every time you learn a "
        "new value for any field."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "deal_type": {
                "type": "string",
                "enum": ["buy", "rent", "sell"],
                "description": "Deal type: buy, rent, or sell",
            },
            "city": {"type": "string", "description": "Search city"},
            "district": {"type": "string", "description": "City neighborhood"},
            "property_type": {
                "type": "string",
                "enum": ["apartment", "house", "commercial", "land"],
            },
            "rooms": {"type": "integer", "description": "Number of bedrooms"},
            "budget_min": {"type": "integer", "description": "Minimum budget"},
            "budget_max": {"type": "integer", "description": "Maximum budget"},
            "budget_currency": {"type": "string", "enum": ["CAD", "USD", "EUR"]},
            "phone": {"type": "string", "description": "Client's phone number"},
            "full_name": {"type": "string", "description": "Client's name"},
        },
        "additionalProperties": False,
    },
}

CLASSIFY_LEAD_TOOL = {
    "name": "classify_lead",
    "description": (
        "Determine the lead's 'temperature' and the urgency of the request "
        "based on the whole conversation. hot — the client is ready to act "
        "immediately (has a budget, phone, clear criteria, mentions "
        "urgency). warm — basic criteria exist, but there's no urgency or "
        "the full data set. cold — unclear need, early stage, the client "
        "is 'just browsing'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "temperature": {"type": "string", "enum": ["hot", "warm", "cold"]},
            "urgency": {
                "type": "string",
                "description": "Short description of urgency, e.g. 'needed within 2 weeks'",
            },
        },
        "required": ["temperature"],
        "additionalProperties": False,
    },
}

TOOLS = [UPDATE_LEAD_PROFILE_TOOL, CLASSIFY_LEAD_TOOL]

GREETING_MESSAGE = (
    "Hi! 👋 I'm an AI assistant for finding real estate. I'll help you "
    "quickly find a listing that matches your needs, or sell/rent out "
    "your property.\n\n"
    "Please tell me, what are you interested in: buying, renting, or selling?"
)
