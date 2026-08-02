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

HOW PORTKEY AUTHENTICATES TO GROQ (pick one)
    - Virtual key: set PORTKEY_VIRTUAL_KEY. Portkey stores the Groq key, so
      GROQ_API_KEY is not needed by this service at all.
    - Pass-through: leave PORTKEY_VIRTUAL_KEY unset. GROQ_API_KEY is forwarded
      to Groq as the bearer token and PORTKEY_PROVIDER (default "groq") tells
      Portkey which provider to route to.
    - Optionally set PORTKEY_CONFIG to a saved Portkey config id (routing,
      fallbacks, cache rules defined in the Portkey dashboard).
"""

import os

from openai import OpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
PORTKEY_GATEWAY_URL = "https://api.portkey.ai/v1"


def _portkey_headers(portkey_key):
    """The x-portkey-* headers that select the upstream provider and options.
    OpenAI's SDK sends `api_key` as the Authorization bearer separately."""
    headers = {"x-portkey-api-key": portkey_key}

    virtual_key = os.environ.get("PORTKEY_VIRTUAL_KEY")
    if virtual_key:
        headers["x-portkey-virtual-key"] = virtual_key
    else:
        headers["x-portkey-provider"] = os.environ.get("PORTKEY_PROVIDER", "groq")

    config = os.environ.get("PORTKEY_CONFIG")
    if config:
        headers["x-portkey-config"] = config
    return headers


def build_groq_client():
    """Construct the OpenAI-compatible client for Groq.

    Routes through Portkey when PORTKEY_API_KEY is set; otherwise talks to Groq
    directly. Raises RuntimeError only when neither a Groq key nor a Portkey
    virtual key is available, so importing this module never requires any key.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    portkey_key = os.environ.get("PORTKEY_API_KEY")

    if portkey_key:
        # With a virtual key the upstream key lives in Portkey, so a placeholder
        # is fine (the OpenAI SDK just needs a non-empty api_key).
        bearer = groq_key or "portkey-virtual-key"
        return OpenAI(
            base_url=PORTKEY_GATEWAY_URL,
            api_key=bearer,
            default_headers=_portkey_headers(portkey_key),
        )

    if not groq_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return OpenAI(base_url=GROQ_BASE_URL, api_key=groq_key)
