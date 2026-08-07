from techcheck.config import load_config

def test_default_model(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = load_config(None)
    assert cfg.model == "gpt-5.5"

def test_env_model(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    cfg = load_config(None)
    assert cfg.model == "test-model"
