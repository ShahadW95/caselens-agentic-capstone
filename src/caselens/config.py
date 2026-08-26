"""Safe configuration loading for environment and Streamlit secrets."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

FROZEN_CHAT_MODEL = "gemini-3.7-flash"
FROZEN_EMBEDDING_MODEL = "gemini-embedding-2"
FROZEN_EMBEDDING_DIMENSIONS = 768


class RuntimeConfig(BaseModel):
    """Validated non-secret defaults plus an optionally configured key."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    gemini_api_key: SecretStr | None = Field(default=None, repr=False)
    gemini_chat_model: Literal["gemini-3.7-flash"] = FROZEN_CHAT_MODEL
    gemini_embedding_model: Literal["gemini-embedding-2"] = FROZEN_EMBEDDING_MODEL
    gemini_embedding_dimensions: Literal[768] = FROZEN_EMBEDDING_DIMENSIONS
    adapter_mode: Literal["live", "development_fake"] = "live"

    @property
    def provider_configured(self) -> bool:
        return bool(
            self.gemini_api_key
            and self.gemini_api_key.get_secret_value().strip()
        )

    @classmethod
    def from_sources(
        cls,
        *,
        environ: Mapping[str, str] | None = None,
        streamlit_secrets: Mapping[str, object] | None = None,
    ) -> "RuntimeConfig":
        """Load secrets first, then environment, without logging either source."""

        env = os.environ if environ is None else environ
        secrets = {} if streamlit_secrets is None else streamlit_secrets

        def get_value(name: str, default: object) -> object:
            secret_value = secrets.get(name)
            if secret_value is not None and str(secret_value).strip():
                return secret_value
            return env.get(name, default)

        raw_key = get_value("GEMINI_API_KEY", "")
        return cls(
            gemini_api_key=SecretStr(str(raw_key)) if str(raw_key).strip() else None,
            gemini_chat_model=get_value("GEMINI_CHAT_MODEL", FROZEN_CHAT_MODEL),
            gemini_embedding_model=get_value(
                "GEMINI_EMBEDDING_MODEL", FROZEN_EMBEDDING_MODEL
            ),
            gemini_embedding_dimensions=get_value(
                "GEMINI_EMBEDDING_DIMENSIONS", FROZEN_EMBEDDING_DIMENSIONS
            ),
            adapter_mode=get_value("CASELENS_ADAPTER_MODE", "live"),
        )


def safe_setup_message(config: RuntimeConfig) -> str | None:
    """Return a user-safe setup warning without disclosing configuration data."""

    if config.provider_configured:
        return None
    return (
        "Provider configuration is missing. Foundation mode remains available; "
        "no model call will be attempted."
    )
