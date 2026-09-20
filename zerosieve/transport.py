"""Transport helpers for HTTP and TLS behavior."""

from __future__ import annotations

import os
import ssl

INSECURE_SSL_ENV_VARS = (
    "ZERO_SEARCH_INSECURE_SSL",
    "CROSS_VALIDATED_SEARCH_INSECURE_SSL",
    "FREE_WEB_SEARCH_INSECURE_SSL",
)

TRUTHY_VALUES = {"1", "true", "yes", "on"}


def insecure_ssl_enabled() -> bool:
    """Return True when TLS verification is explicitly disabled by env var."""
    for env_var in INSECURE_SSL_ENV_VARS:
        value = os.getenv(env_var, "").strip().lower()
        if value in TRUTHY_VALUES:
            return True
    return False


def build_ssl_context() -> ssl.SSLContext:
    """Create a secure-by-default SSL context.

    Users in constrained environments can opt into insecure transport by
    setting `ZERO_SEARCH_INSECURE_SSL=1`.
    """
    context = ssl.create_default_context()
    if insecure_ssl_enabled():
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context
