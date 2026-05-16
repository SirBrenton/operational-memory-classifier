#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path

QUERY_SCRIPT = Path("scripts/query_operational_memory.py").resolve()


def read_input(path: str) -> str:
    return Path(path).read_text().strip()


def classify(text: str) -> dict:
    lower = text.lower()

    if "retry-after" in lower or "429" in lower or "rate limit" in lower:
        return {
            "decision": "WAIT",
            "reason": "provider cooldown / rate-limit signal present",
            "query": "which systems kept retrying when they should have waited?",
            "fix_shape": "Honor Retry-After as the minimum retry delay before local backoff.",
        }

    if "quota" in lower or "context" in lower or "too large" in lower:
        return {
            "decision": "CAP",
            "reason": "capacity or quota boundary likely exceeded",
            "query": "which systems exceeded capacity and needed to shrink the request?",
            "fix_shape": "Shrink the request, reduce concurrency, or route to a higher-capacity path.",
        }

    return {
        "decision": "STOP",
        "reason": "no safe retry/cap signal detected",
        "query": "which operational mistakes keep repeating across unrelated AI systems?",
        "fix_shape": "Stop retrying blindly; surface the condition for explicit handling.",
    }


def run_memory_query(query: str) -> str:
    proc = subprocess.run(
        [str(QUERY_SCRIPT), query, "--mode", "stage", "--limit", "3"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Classify an execution failure and retrieve matching GBrain operational precedent."
    )
    parser.add_argument("input", help="Path to finding/error text.")
    args = parser.parse_args()

    finding = read_input(args.input)
    result = classify(finding)
    precedent = run_memory_query(result["query"])

    print()
    print("EVIDENCE-BACKED EXECUTION CLASSIFIER")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("Finding:")
    print(finding)
    print()
    print(f"Classification: {result['decision']}")
    print(f"Reason: {result['reason']}")
    print(f"Fix shape: {result['fix_shape']}")
    print()
    print("Matched operational precedent:")
    print(precedent)
    print()
    print("Why this matters:")
    print(
        "When your agent fails at a boundary, this tells you what it means — "
        "grounded in confirmed fixes from systems that already hit the same wall."
    )


if __name__ == "__main__":
    main()
