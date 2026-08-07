from techcheck.reviews import review_quote, review_service

class FakeAI:
    def __init__(self):
        self.calls = []
    def json_review(self, prompt, payload):
        self.calls.append((prompt, payload))
        return {"ok": True}

def test_quote_review_passes_all_fields():
    ai = FakeAI()
    result = review_quote(ai, "Q10", 20.0, 10000.0, "Supply and install drain")
    assert result == {"ok": True}
    assert len(ai.calls) == 1
    payload = ai.calls[0][1]
    assert '"claimed_labour_hours": 20.0' in payload
    assert '"materials_and_equipment_allowance_aud": 10000.0' in payload
    assert "Supply and install drain" in payload

def test_service_review_passes_hours():
    ai = FakeAI()
    review_service(ai, "Technician notes", 14.89)
    assert '"claimed_labour_hours": 14.89' in ai.calls[0][1]
