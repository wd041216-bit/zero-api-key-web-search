"""Compatibility shim for the historical `zero_api_key_web_search_compat.context` path."""

from zero_api_key_web_search.context import *  # noqa: F401,F403
from zero_api_key_web_search.context import main

if __name__ == "__main__":
    main()
