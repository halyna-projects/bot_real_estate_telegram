from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.ai.prompts import CLASSIFY_LEAD_TOOL, SYSTEM_PROMPT, TOOLS, UPDATE_LEAD_PROFILE_TOOL
from app.config import get_settings

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 4


@dataclass
class DialogueResult:
    """Result of one AI dialogue turn."""

    reply_text: str
    profile_updates: dict[str, Any] = field(default_factory=dict)
    classification: dict[str, Any] | None = None
    conversation_history: list[dict[str, Any]] = field(default_factory=list)


class DialogueEngine:
    """Wraps the Anthropic Claude API to hold a natural-language qualification
    dialogue with a lead while extracting structured data via tool calls.

    Falls back to a lightweight heuristic engine when no API key is
    configured, so the rest of the system keeps working without a live key
    (useful for local development, tests and demos).
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        if self.settings.anthropic_api_key:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self.settings.anthropic_api_key)

    @property
    def is_live(self) -> bool:
        return self._client is not None

    def next_reply(
        self,
        conversation_history: list[dict[str, Any]],
        user_message: str,
        known_fields: dict[str, Any] | None = None,
    ) -> DialogueResult:
        if not self.is_live:
            from app.ai.fallback import heuristic_reply

            return heuristic_reply(conversation_history, user_message, known_fields)

        messages = list(conversation_history) + [
            {"role": "user", "content": user_message}
        ]

        profile_updates: dict[str, Any] = {}
        classification: dict[str, Any] | None = None

        system = SYSTEM_PROMPT
        if known_fields:
            system += (
                "\n\nVeć je poznato o klijentu (npr. izabrano preko dugmića "
                f"ranije u ovom razgovoru): {known_fields}. Ne pitaj ponovo — "
                "uzmi to u obzir pri sledećem pitanju i pozivu "
                "update_lead_profile."
            )

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self._client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=1024,
                system=system,
                tools=TOOLS,
                messages=messages,
            )

            assistant_content = [block.model_dump() for block in response.content]
            messages.append({"role": "assistant", "content": assistant_content})

            if response.stop_reason != "tool_use":
                reply_text = "".join(
                    block.text for block in response.content if block.type == "text"
                ).strip()
                return DialogueResult(
                    reply_text=reply_text or "Recite mi, molim vas, malo detaljnije.",
                    profile_updates=profile_updates,
                    classification=classification,
                    conversation_history=messages,
                )

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if block.name == UPDATE_LEAD_PROFILE_TOOL["name"]:
                    profile_updates.update(
                        {k: v for k, v in block.input.items() if v not in (None, "")}
                    )
                    result_payload = {"status": "saved"}
                elif block.name == CLASSIFY_LEAD_TOOL["name"]:
                    classification = dict(block.input)
                    result_payload = {"status": "classified"}
                else:
                    result_payload = {"status": "ignored"}

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": [{"type": "text", "text": str(result_payload)}],
                    }
                )

            messages.append({"role": "user", "content": tool_results})

        logger.warning("DialogueEngine: max tool iterations reached without final text reply")
        return DialogueResult(
            reply_text="Hvala na informacijama! Odmah ću pronaći ponude.",
            profile_updates=profile_updates,
            classification=classification,
            conversation_history=messages,
        )
