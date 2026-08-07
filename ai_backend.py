from __future__ import annotations

import json
import re
from openai import OpenAI


class TechCheckError(RuntimeError):
    pass


def _json_text(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


class TechCheckAI:
    """Single OpenAI gateway used by every page."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise TechCheckError("OPENAI_API_KEY is not configured.")
        if not model:
            raise TechCheckError("OPENAI_MODEL is not configured.")
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def structured(self, instructions: str, payload: dict) -> dict:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=json.dumps(payload, ensure_ascii=False),
            )
            output = getattr(response, "output_text", "") or ""
            if not output:
                raise TechCheckError("The AI returned an empty response.")
            try:
                return json.loads(_json_text(output))
            except json.JSONDecodeError as exc:
                raise TechCheckError(
                    "The AI response was not valid structured JSON. Please run the review again."
                ) from exc
        except TechCheckError:
            raise
        except Exception as exc:
            raise TechCheckError(f"AI request failed: {exc}") from exc

    def chat(self, instructions: str, messages: list[dict[str, str]]) -> str:
        conversation = "\n\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages
        )
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=conversation,
            )
            output = getattr(response, "output_text", "") or ""
            if not output:
                raise TechCheckError("The AI returned an empty response.")
            return output
        except TechCheckError:
            raise
        except Exception as exc:
            raise TechCheckError(f"Sounding Board request failed: {exc}") from exc
