import asyncio

try:
    from esbonio.sphinx_agent.server import main
except ImportError:
    from .server import main

asyncio.run(main())
