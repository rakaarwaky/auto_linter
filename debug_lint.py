import asyncio
import sys
import os
import json

# Ensure src is in path
sys.path.append(os.getcwd())

from src.bootstrap.container import get_container

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 debug_lint.py <path>")
        return

    path = os.path.abspath(sys.argv[1])
    container = get_container()
    
    print(f"--- Debugging Lint Check for: {path} ---")
    print(f"Venv Bin: {container.venv_bin}")
    
    try:
        report = await container.analysis_use_case.execute(path)
        results = container.analysis_use_case.to_dict(report)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
