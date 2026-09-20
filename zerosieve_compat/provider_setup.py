"""Compatibility shim for the historical `zerosieve_compat.provider_setup` path."""

from zerosieve.provider_setup import *  # noqa: F401,F403
from zerosieve.provider_setup import main

if __name__ == "__main__":
    main()
