from __future__ import annotations
import json
import re
from openai import OpenAI

class TechCheckAIError(RuntimeError):
    pass

def clean_json(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

class TechCheckAI:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise TechCheckAIError("OpenAI API key is not configured.")
        if not model:
            raise TechCheckAIError("OpenAI model is not configured.")
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def structured_review(self, instructions: str, payload: dict) -> dict:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=json.dumps(payload, ensure_ascii=False),
            )
            text = getattr(response, "output_text", "") or ""
            if not text:
                raise TechCheckAIError("The AI returned an empty response.")
            try:
                return json.loads(clean_json(text))
            except json.JSONDecodeError as exc:
                raise TechCheckAIError(
                    "The AI response was not valid structured JSON. Run the review again."
                ) from exc
        except TechCheckAIError:
            raise
        except Exception as exc:
            raise TechCheckAIError(f"AI request failed: {exc}") from exc

    def chat(self, instructions: str, messages: list[dict[str, str]]) -> str:
        transcript = "\n\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages
        )
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=transcript,
            )
            text = getattr(response, "output_text", "") or ""
            if not text:
                raise TechCheckAIError("The AI returned an empty response.")
            return text
        except TechCheckAIError:
            raise
        except Exception as exc:
            raise TechCheckAIError(f"Sounding Board request failed: {exc}") from exc
