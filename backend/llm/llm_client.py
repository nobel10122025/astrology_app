"""Shared Groq client factory, optionally routed through the Portkey AI gateway.

WHY THIS EXISTS
    planet_judge, groq_narrator and tool_planner each built their own
    ``OpenAI(base_url=GROQ_BASE_URL, api_key=...)`` client. That is three copies
    of the same wiring and no single place to add gateway routing. This module
    is the one place a Groq client is constructed.

DIRECT vs GATEWAY (env-gated - default behaviour is unchanged)
    - PORTKEY_API_KEY unset  -> talk to Groq directly, exactly as before.
    - PORTKEY_API_KEY set     -> the identical OpenAI-SDK calls are routed
      through Portkey's OpenAI-compatible gateway instead, which gives
      observability, caching, retries and fallbacks without touching any call
      site. No extra dependency: Portkey is driven purely by request headers.

HOW PORTKEY REACHES GROQ (three modes, checked in this order)
    1. Model catalog (recommended, matches Portkey's current quickstart):
       set PORTKEY_SLUG to your integration slug (e.g. "astrology-app-key").
       Portkey stores the Groq key against that slug, so GROQ_API_KEY is not
       needed here. The model sent to the API is rewritten to
       "@<slug>/<model>" by resolve_model(), which is how the catalog routes.
    2. Virtual key: set PORTKEY_VIRTUAL_KEY (the older header-based form).
    3. Pass-through: neither of the above - GROQ_API_KEY is forwarded to Groq
       and PORTKEY_PROVIDER (default "groq") names the provider.

    Optionally set PORTKEY_CONFIG to a saved Portkey config id (routing,
    fallbacks, cache rules defined in the Portkey dashboard).
"""

import os

from openai import OpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
PORTKEY_GATEWAY_URL = "https://api.portkey.ai/v1"


def _portkey_headers(portkey_key):
    """The x-portkey-* headers. `x-portkey-api-key` authenticates to Portkey;
    the remaining headers pick how Portkey reaches the upstream provider.

    In model-catalog mode (PORTKEY_SLUG set) the routing lives in the model
    string, so no provider/virtual-key header is sent."""
    headers = {"x-portkey-api-key": portkey_key}

    if not os.environ.get("PORTKEY_SLUG"):
        virtual_key = os.environ.get("PORTKEY_VIRTUAL_KEY")
        if virtual_key:
            headers["x-portkey-virtual-key"] = virtual_key
        else:
            headers["x-portkey-provider"] = os.environ.get("PORTKEY_PROVIDER", "groq")

    config = os.environ.get("PORTKEY_CONFIG")
    if config:
        headers["x-portkey-config"] = config
    return headers


def resolve_model(model):
    """Rewrite a bare model name for Portkey's model catalog.

    In catalog mode a model is addressed as "@<slug>/<model>". Outside catalog
    mode (direct Groq, virtual key, or pass-through) the name is returned
    unchanged, and an already-prefixed "@..." name is never touched.
    """
    slug = os.environ.get("PORTKEY_SLUG")
    if os.environ.get("PORTKEY_API_KEY") and slug and not str(model).startswith("@"):
        return f"@{slug}/{model}"
    return model


def build_groq_client():
    """Construct the OpenAI-compatible client for Groq.

    Routes through Portkey when PORTKEY_API_KEY is set; otherwise talks to Groq
    directly. Raises RuntimeError only when no usable credential is available,
    so importing this module never requires any key.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    portkey_key = os.environ.get("PORTKEY_API_KEY")

    if portkey_key:
        # In catalog / virtual-key mode the upstream key lives in Portkey, so
        # the bearer only needs to be non-empty; the Portkey key is fine.
        bearer = groq_key or portkey_key
        return OpenAI(
            base_url=PORTKEY_GATEWAY_URL,
            api_key=bearer,
            default_headers=_portkey_headers(portkey_key),
        )

    if not groq_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return OpenAI(base_url=GROQ_BASE_URL, api_key=groq_key)
