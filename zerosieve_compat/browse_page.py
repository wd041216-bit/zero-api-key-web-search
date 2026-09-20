"""Compatibility shim for the historical `zerosieve_compat.browse_page` path."""

from zerosieve.browse_page import *  # noqa: F401,F403
from zerosieve.browse_page import main

if __name__ == "__main__":
    main()
