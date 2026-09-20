"""Compatibility shim for the historical `zerosieve_compat.search_web` path."""

from zerosieve.search_web import *  # noqa: F401,F403
from zerosieve.search_web import main

if __name__ == "__main__":
    main()
