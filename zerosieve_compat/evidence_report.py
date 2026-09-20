"""Compatibility shim for the historical `zerosieve_compat.evidence_report` path."""

from zerosieve.evidence_report import *  # noqa: F401,F403
from zerosieve.evidence_report import main

if __name__ == "__main__":
    main()
