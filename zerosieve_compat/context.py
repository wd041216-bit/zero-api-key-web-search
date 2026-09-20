"""Compatibility shim for the historical `zerosieve_compat.context` path."""

from zerosieve.context import *  # noqa: F401,F403
from zerosieve.context import main

if __name__ == "__main__":
    main()
