from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    api_key: str | None
    model: str
    app_password: str | None

def load_config(st_module=None) -> AppConfig:
    """Load settings from Streamlit secrets first, then environment variables."""
    def secret(name: str):
        if st_module is None:
            return None
        try:
            return st_module.secrets.get(name)
        except Exception:
            return None

    api_key = secret("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    model = secret("OPENAI_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5.5"
    app_password = secret("APP_PASSWORD") or os.getenv("APP_PASSWORD")
    return AppConfig(api_key=api_key, model=model, app_password=app_password)
