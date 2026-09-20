"""Compatibility shim for the historical `zero_api_key_web_search_compat.evidence_report` path."""

from zero_api_key_web_search.evidence_report import *  # noqa: F401,F403
from zero_api_key_web_search.evidence_report import main

if __name__ == "__main__":
    main()
