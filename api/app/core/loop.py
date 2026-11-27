"""Event loop choice.

The database driver (psycopg) cannot run on Windows' default "Proactor" event loop, so on
Windows we use the "Selector" loop. Everywhere else the normal default is used.
"""

import asyncio
import sys


def new_event_loop() -> asyncio.AbstractEventLoop:
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop()
    return asyncio.new_event_loop()
