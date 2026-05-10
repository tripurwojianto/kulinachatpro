"""Provider selector: Gemini primary, OpenAI fallback."""
import logging
import os

logger = logging.getLogger(__name__)

PROVIDERS = {
    "gemini": {
        "model": "gemini-2.0-flash",
        "label": "Gemini 2.0 Flash",
        "env_key": "GOOGLE_API_KEY",
    },
    "openai": {
        "model": "gpt-4o",
        "label": "GPT-4o (OpenAI)",
        "env_key": "OPENAI_API_KEY",
    },
}

_active_provider: str = "gemini"


def get_active_provider() -> str:
    return _active_provider


def get_active_model() -> str:
    return PROVIDERS[_active_provider]["model"]


def set_provider(provider: str) -> str:
    global _active_provider
    if provider not in PROVIDERS:
        return f"Provider '{provider}' tidak dikenal. Pilihan: gemini, openai"
    key = os.getenv(PROVIDERS[provider]["env_key"], "")
    if not key:
        return f"API key untuk {provider} belum ada di .env"
    _active_provider = provider
    logger.info(f"[ModelProvider] Aktif: {PROVIDERS[provider]['label']}")
    return f"ok:{provider}"
