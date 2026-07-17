"""LLM client boundary.

CaseMind Sentinel calls the Portkey AI Gateway using the Anthropic SDK's
Anthropic-compatible API surface. The gateway handles routing to the underlying
model provider; the application holds only the Portkey API key.

Configuration:
  PORTKEY_API_KEY    — gateway credential
  PORTKEY_BASE_URL   — Portkey gateway endpoint
  PORTKEY_MODEL      — model identifier passed through the gateway
  PORTKEY_PROVIDER   — x-portkey-provider header value
  PORTKEY_CA_BUNDLE  — (optional) path to CA bundle file; auto-detected on macOS
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import os

import anthropic
import httpx

from config.settings import settings


def _build_ssl_context() -> str | bool:
    """Return a CA bundle path suitable for the current environment.

    On macOS the system keychain may contain CAs not included in Python's
    certifi bundle. We extract them automatically so no manual cert-file
    setup is needed.
    """
    if settings.portkey_ca_bundle:
        return settings.portkey_ca_bundle

    if sys.platform != "darwin":
        return True  # use default certifi bundle on non-macOS

    try:
        # Export from both System and login keychains
        pem_parts = []
        for keychain in ("/Library/Keychains/System.keychain",):
            result = subprocess.run(
                ["security", "find-certificate", "-a", "-p", keychain],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                pem_parts.append(result.stdout)

        # Also include login keychain (no path = current user's login)
        result = subprocess.run(
            ["security", "find-certificate", "-a", "-p"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            pem_parts.append(result.stdout)

        if pem_parts:
            tmp = tempfile.NamedTemporaryFile(
                suffix=".pem", delete=False, mode="w",
                prefix="casemind_ca_",
            )
            tmp.write("\n".join(pem_parts))
            tmp.close()
            return tmp.name
    except Exception:
        pass

    return True  # fall back to certifi


_ca_bundle = _build_ssl_context()


def generate_grounded_answer(prompt: str) -> str:
    """Call the LLM through the Portkey gateway and return the answer text.

    Raises RuntimeError with a human-readable message if PORTKEY_API_KEY is
    missing, so the caller can return a structured error response instead of
    crashing.
    """
    if not settings.portkey_api_key:
        raise RuntimeError(
            "Portkey API key is not configured. "
            "Set PORTKEY_API_KEY in sentinel/backend/.env."
        )

    http_client = httpx.Client(verify=_ca_bundle)

    # Portkey expects the key as Authorization: Bearer <token>.
    # The Anthropic SDK's auth_token parameter sends exactly that header.
    client = anthropic.Anthropic(
        auth_token      = settings.portkey_api_key,
        base_url        = settings.portkey_base_url,
        default_headers = {"x-portkey-provider": settings.portkey_provider},
        http_client     = http_client,
    )

    message = client.messages.create(
        model      = settings.portkey_model,
        max_tokens = 512,
        messages   = [{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()
