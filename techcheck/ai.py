from __future__ import annotations
import json
import re
from typing import Any

class AIError(RuntimeError):
    pass

def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

class AIClient:
    """Single gateway for all OpenAI calls. Model is always defined here."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise AIError("OPENAI_API_KEY is not configured.")
        if not model:
            raise AIError("OPENAI_MODEL is not configured.")
        self.model = model
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AIError("The openai package is not installed. Check requirements.txt.") from exc
        self.client = OpenAI(api_key=api_key)

    def json_review(self, system_prompt: str, user_payload: str) -> dict[str, Any]:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=user_payload,
            )
            text = getattr(response, "output_text", "") or ""
            if not text:
                raise AIError("The AI returned an empty response.")
            return json.loads(_clean_json(text))
        except json.JSONDecodeError as exc:
            raise AIError("The AI response was not valid JSON. Please run the review again.") from exc
        except AIError:
            raise
        except Exception as exc:
            raise AIError(f"Live AI request failed: {exc}") from exc

    def chat(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        transcript = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=transcript,
            )
            text = getattr(response, "output_text", "") or ""
            if not text:
                raise AIError("The AI returned an empty response.")
            return text
        except AIError:
            raise
        except Exception as exc:
            raise AIError(f"Sounding Board request failed: {exc}") from exc
