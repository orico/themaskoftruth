#!/usr/bin/env python3
"""
The Floor Is a Lie - Top-Down Memory Puzzle Game
Main entry point for web and desktop
"""
import asyncio
import os
import sys

print("=" * 80)
print("ROOT MAIN.PY: Script is being executed!")
print("=" * 80)

# Detect if we're running in a web environment
try:
    import platform

    is_web = "emscripten" in platform.system().lower() or hasattr(
        sys, "_emscripten_info"
    )
    print(f"ROOT MAIN.PY: Running in web environment: {is_web}")
except:
    is_web = False
    print("ROOT MAIN.PY: Running in desktop environment")

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"ROOT MAIN.PY: Added {project_root} to sys.path")

try:
    print("ROOT MAIN.PY: Importing main from src.the_floor_is_a_lie.main...")
    from src.the_floor_is_a_lie.main import main

    print("ROOT MAIN.PY: Import successful!")
except Exception as e:
    print(f"ROOT MAIN.PY: Import FAILED - {e}")
    print(f"sys.path: {sys.path}")
    import traceback

    traceback.print_exc()
    raise


# For web environments, we need to yield control to the browser event loop
async def async_main():
    print("ROOT MAIN.PY: async_main() started")
    if is_web:
        print("ROOT MAIN.PY: Web mode - yielding to event loop")
        await asyncio.sleep(0)  # Yield to browser
    print("ROOT MAIN.PY: Calling main()...")
    main()
    print("ROOT MAIN.PY: main() returned!")


# Run the appropriate version
if is_web:
    print("ROOT MAIN.PY: Starting async execution for web...")
    asyncio.run(async_main())
else:
    print("ROOT MAIN.PY: Starting sync execution for desktop...")
    main()
