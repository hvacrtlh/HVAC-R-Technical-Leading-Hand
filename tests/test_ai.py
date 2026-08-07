import pytest
from techcheck.ai import AIClient, AIError, _clean_json

def test_clean_json_fence():
    raw = """```json
{"a":1}
```"""
    assert _clean_json(raw) == '{"a":1}'

def test_ai_requires_key():
    with pytest.raises(AIError):
        AIClient("", "gpt-5.5")

def test_ai_requires_model():
    with pytest.raises(AIError):
        AIClient("fake-key", "")
