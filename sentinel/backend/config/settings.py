import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Application metadata
    app_name: str = "CaseMind Sentinel"
    version:  str = "1.0.0"
    subtitle: str = "Police AI Investigation Platform"

    # LLM gateway — Portkey AI Gateway via Anthropic-compatible API
    llm_provider:     str = "portkey"
    portkey_api_key:  str = ""
    portkey_base_url: str = ""
    portkey_model:    str = ""
    portkey_provider: str = ""
    # Optional: path to a CA bundle file. If empty, client falls back to
    # the default certificate store.
    portkey_ca_bundle: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name = os.getenv("APP_NAME",    "CaseMind Sentinel"),
            version  = os.getenv("APP_VERSION", "1.0.0"),
            subtitle = os.getenv("APP_SUBTITLE", "Police AI Investigation Platform"),

            llm_provider      = os.getenv("LLM_PROVIDER",      "portkey"),
            portkey_api_key   = os.getenv("PORTKEY_API_KEY",   ""),
            portkey_base_url  = os.getenv("PORTKEY_BASE_URL",  ""),
            portkey_model     = os.getenv("PORTKEY_MODEL",     ""),
            portkey_provider  = os.getenv("PORTKEY_PROVIDER",  ""),
            portkey_ca_bundle = os.getenv("PORTKEY_CA_BUNDLE", ""),
        )


settings = Settings.from_env()
