import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())