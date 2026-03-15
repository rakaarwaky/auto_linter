import asyncio
import os
import sys
from src.bootstrap.container import get_container

async def main():
    path = os.getcwd()
    container = get_container()
    print(f"Running analysis for: {path}")
    report = await container.analysis_use_case.execute(path)
    results = container.analysis_use_case.to_dict(report)
    print("Analysis results summary:")
    for key, val in results.items():
        if isinstance(val, list):
            print(f" - {key}: {len(val)} findings")
        elif isinstance(val, dict):
             print(f" - {key}: {len(val)} entries")
        else:
             print(f" - {key}: {val}")

    if "governance" in results and isinstance(results["governance"], list):
        print("\nGovernance Check:")
        for rule in results["governance"]:
            print(f" - {rule.get('message', 'No message')}")

if __name__ == "__main__":
    # Ensure current dir is in path
    sys.path.append(os.getcwd())
    asyncio.run(main())
