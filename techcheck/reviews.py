from __future__ import annotations
import json
from .ai import AIClient
from .prompts import SERVICE_REVIEW_PROMPT, QUOTE_REVIEW_PROMPT

def review_service(ai: AIClient, report_text: str, labour_hours: float | None = None) -> dict:
    payload = {
        "claimed_labour_hours": labour_hours,
        "technician_report": report_text,
    }
    return ai.json_review(SERVICE_REVIEW_PROMPT, json.dumps(payload, ensure_ascii=False))

def review_quote(
    ai: AIClient,
    quote_reference: str,
    labour_hours: float,
    materials_allowance: float,
    scope: str,
) -> dict:
    payload = {
        "quote_reference": quote_reference,
        "claimed_labour_hours": labour_hours,
        "materials_and_equipment_allowance_aud": materials_allowance,
        "scope_and_quotation_details": scope,
    }
    return ai.json_review(QUOTE_REVIEW_PROMPT, json.dumps(payload, ensure_ascii=False))

def demo_service(report_text: str, labour_hours: float | None = None) -> dict:
    lower = report_text.lower()
    concerns = []
    if "replace compressor" in lower and not any(k in lower for k in ["megger", "insulation resistance", "winding"]):
        concerns.append("Compressor replacement is mentioned without clear electrical test evidence.")
    return {
        "decision": "Approve with Comments" if concerns else "Request Further Information",
        "confidence": 45,
        "overall_score": 60,
        "summary": "Demonstration mode uses limited deterministic checks only.",
        "diagnosis_assessment": "Live AI is required for report-specific technical reasoning.",
        "evidence": [],
        "technical_concerns": concerns,
        "missing_tests": [],
        "parts_assessment": [],
        "labour": {
            "claimed_hours": labour_hours or 0,
            "reasonable_range": "Live AI required",
            "rating": "Unable to assess",
            "reason": "Demonstration mode does not benchmark labour."
        },
        "risks": [],
        "questions_for_technician": [],
        "coaching": [],
        "senior_technician_challenge": {
            "alternative_causes": [],
            "best_next_test": "",
            "cheaper_first_step": "",
            "root_cause_comment": ""
        }
    }

def demo_quote(quote_reference: str, labour_hours: float, materials_allowance: float, scope: str) -> dict:
    return {
        "commercial_risk": "Medium",
        "decision": "Request Further Information",
        "confidence": 35,
        "headline": "Demonstration mode does not perform genuine quotation reasoning.",
        "labour": {
            "claimed_hours": labour_hours,
            "reasonable_range": "Live AI required",
            "rating": "Unable to assess",
            "reason": "Use Live AI for scope-based labour assessment."
        },
        "materials": {
            "allowance": materials_allowance,
            "rating": "Unable to assess",
            "reason": "Use Live AI for scope-based commercial assessment."
        },
        "scope_clarity": "Fair" if len(scope.strip()) > 30 else "Poor",
        "items_to_check": ["Switch to Live AI for a genuine quote review."],
        "missing_scope_items": [],
        "questions_before_approval": [],
        "commercial_notes": []
    }
