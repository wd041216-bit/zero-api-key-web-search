"""Compatibility shim for the historical `zero_api_key_web_search_compat.browse_page` path."""

from zero_api_key_web_search.browse_page import *  # noqa: F401,F403
from zero_api_key_web_search.browse_page import main

if __name__ == "__main__":
    main()
