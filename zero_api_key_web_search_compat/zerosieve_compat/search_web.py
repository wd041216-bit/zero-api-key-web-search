"""Compatibility shim for the historical `zero_api_key_web_search_compat.search_web` path."""

from zero_api_key_web_search.search_web import *  # noqa: F401,F403
from zero_api_key_web_search.search_web import main

if __name__ == "__main__":
    main()
