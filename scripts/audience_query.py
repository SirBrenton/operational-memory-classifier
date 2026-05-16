#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(
    "~/Development-Projects/practicallyai/cases/gbrain-hackathon/scripts/demo/query_operational_memory.py"
).expanduser()

QUERIES = {
    "1": (
        "Hidden retry storms",
        "which systems kept retrying when they should have waited?",
    ),
    "2": (
        "Fake resilience",
        "where did systems look resilient while actually making failures worse?",
    ),
    "3": (
        "Repeating ecosystem mistakes",
        "which operational mistakes keep repeating across unrelated AI systems?",
    ),
}


def main():
    print()
    print("CHOOSE THE NEXT OPERATIONAL MEMORY QUERY")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    for key, (label, query) in QUERIES.items():
        print(f"{key}. {label}")
        print(f"   {query}")
        print()

    choice = input("Audience choice [1/2/3]: ").strip()

    if choice not in QUERIES:
        print("Invalid choice.")
        sys.exit(1)

    label, query = QUERIES[choice]

    print()
    print(f"RUNNING: {label}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    subprocess.run(
        [str(SCRIPT), query, "--mode", "stage"],
        check=False,
    )


if __name__ == "__main__":
    main()