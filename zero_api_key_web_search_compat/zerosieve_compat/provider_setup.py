"""Compatibility shim for the historical `zero_api_key_web_search_compat.provider_setup` path."""

from zero_api_key_web_search.provider_setup import *  # noqa: F401,F403
from zero_api_key_web_search.provider_setup import main

if __name__ == "__main__":
    main()
