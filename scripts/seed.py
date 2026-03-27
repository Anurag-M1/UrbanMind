"""
Standalone seed script for running via docker-compose exec.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from scripts_seed import seed_intersections, main

if __name__ == "__main__":
    asyncio.run(main())
