from __future__ import annotations

import json
import re
from openai import OpenAI

# Keep the model server-side. End users do not need to choose or see it.
MODEL = "gpt-5"


class TechCheckError(RuntimeError):
    pass


def _strip_json_fence(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


class TechCheckAI:
    def __init__(self, api_key: str):
        if not api_key:
            raise TechCheckError(
                "OpenAI API key is not configured. Add OPENAI_API_KEY in Streamlit Secrets."
            )
        self.client = OpenAI(api_key=api_key)

    def structured(self, instructions: str, payload: dict) -> dict:
        try:
            response = self.client.responses.create(
                model=MODEL,
                instructions=instructions,
                input=json.dumps(payload, ensure_ascii=False),
            )
            text = getattr(response, "output_text", "") or ""
            if not text:
                raise TechCheckError("The AI returned an empty response.")

            try:
                return json.loads(_strip_json_fence(text))
            except json.JSONDecodeError as exc:
                raise TechCheckError(
                    "The AI response was not valid structured JSON. Run the review again."
                ) from exc

        except TechCheckError:
            raise
        except Exception as exc:
            raise TechCheckError(f"AI request failed: {exc}") from exc

    def chat(self, instructions: str, messages: list[dict[str, str]]) -> str:
        conversation = "\n\n".join(
            f"{message['role'].upper()}: {message['content']}"
            for message in messages
        )

        try:
            response = self.client.responses.create(
                model=MODEL,
                instructions=instructions,
                input=conversation,
            )
            text = getattr(response, "output_text", "") or ""
            if not text:
                raise TechCheckError("The AI returned an empty response.")
            return text

        except TechCheckError:
            raise
        except Exception as exc:
            raise TechCheckError(f"Sounding Board request failed: {exc}") from exc
