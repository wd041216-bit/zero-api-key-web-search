"""Compatibility shim for the historical `zerosieve_compat.verify_claim` path."""

from zerosieve.verify_claim import *  # noqa: F401,F403
from zerosieve.verify_claim import main

if __name__ == "__main__":
    main()
