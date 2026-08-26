"""Single Gemini provider boundary shell; A0 performs no live requests."""

from __future__ import annotations

from typing import Any

from .config import RuntimeConfig


class ProviderNotConfiguredError(RuntimeError):
    """Raised safely when live mode is requested without a credential."""


class GeminiClientFactory:
    """Lazily create the current google-genai client at the integration phase."""

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config

    def create(self) -> Any:
        if not self._config.provider_configured:
            raise ProviderNotConfiguredError(
                "Gemini is not configured; no provider request was made."
            )

        # The import and client construction are deliberately lazy. Calling this
        # method is reserved for the explicit live integration checkpoint.
        from google import genai

        key = self._config.gemini_api_key
        assert key is not None  # narrowed by provider_configured
        return genai.Client(api_key=key.get_secret_value())
