"""Compatibility shim for the historical `zero_api_key_web_search_compat.verify_claim` path."""

from zero_api_key_web_search.verify_claim import *  # noqa: F401,F403
from zero_api_key_web_search.verify_claim import main

if __name__ == "__main__":
    main()
