#!/usr/bin/env python3

import argparse
import re
import subprocess
from pathlib import Path

QUERY_SCRIPT = Path("scripts/query_operational_memory.py").resolve()


def read_input(path: str) -> str:
    return Path(path).read_text().strip()


def compact(text: str, max_chars: int = 140) -> str:
    text = " ".join(text.strip().split())

    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    word_break = truncated.rfind(" ")

    if word_break > 0:
        return truncated[:word_break].rstrip() + "…"

    return truncated.rstrip() + "…"


def classify(text: str) -> dict:
    lower = text.lower()

    if "retry-after" in lower or "429" in lower or "rate limit" in lower:
        return {
            "decision": "WAIT",
            "reason": "provider cooldown / rate-limit signal present",
            "query": "which failures ignore Retry-After and retry inside provider cooldown windows?",
            "fix_shape": "Honor Retry-After as the minimum retry delay before local backoff.",
            "risk": "retry amplification / quota burn / workflow stall",
        }

    if "quota" in lower or "context" in lower or "too large" in lower:
        return {
            "decision": "CAP",
            "reason": "capacity or quota boundary likely exceeded",
            "query": "which systems exceeded capacity and needed to shrink the request?",
            "fix_shape": "Shrink the request, reduce concurrency, or route to a higher-capacity path.",
            "risk": "capacity exhaustion / failed execution / wasted attempts",
        }

    return {
        "decision": "STOP",
        "reason": "no safe retry/cap signal detected",
        "query": "which operational mistakes keep repeating across unrelated AI systems?",
        "fix_shape": "Stop retrying blindly; surface the condition for explicit handling.",
        "risk": "unbounded retries / unclear recovery / hidden failure amplification",
    }


def run_memory_query(query: str) -> str:
    proc = subprocess.run(
        [str(QUERY_SCRIPT), query, "--mode", "stage", "--limit", "5"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip()


def clean_title(title: str) -> str:
    title = title.strip()
    title = title.replace(" Retry-After execution failure", "")
    title = title.replace(" operational failure receipt", "")
    return title


def render_precedent_summary(output: str, limit: int = 3) -> str:
    blocks = []
    current_title = None

    for raw_line in output.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("OPERATIONAL MEMORY QUERY"):
            continue

        if line.startswith("━") or line.startswith("which "):
            continue

        if (
            line.endswith("execution failure")
            or line.endswith("operational failure receipt")
        ):
            current_title = clean_title(line)
            continue

        if line.startswith("Pattern:") and current_title:
            pattern = line.replace("Pattern:", "", 1).strip()
            blocks.append(f"  → {current_title}\n    {compact(pattern, 115)}")
            current_title = None

        if len(blocks) >= limit:
            break

    if not blocks:
        return "  → no matching precedent found"

    return "\n\n".join(blocks)


def print_hero_result(
    finding: str,
    classification: str,
    reason: str,
    risk: str,
    fix_shape: str,
    precedent_output: str,
):
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("OPERATIONAL MEMORY CLASSIFIER")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("Finding:")
    print(f"  {compact(finding, 160)}")
    print()
    print("Classification:")
    print(f"  {classification}")
    print()
    print("Reason:")
    print(f"  {reason}")
    print()
    print("Risk:")
    print(f"  {risk}")
    print()
    print("Fix shape:")
    print(f"  {fix_shape}")
    print()
    print("Matched precedent:")
    print(render_precedent_summary(precedent_output))
    print()
    print("Grounding:")
    print("  Retrieved from operational-memory receipts tied to real production fixes.")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Classify an execution failure and retrieve matching GBrain operational precedent."
    )
    parser.add_argument("input", help="Path to finding/error text.")
    args = parser.parse_args()

    finding = read_input(args.input)
    result = classify(finding)
    precedent = run_memory_query(result["query"])

    print_hero_result(
        finding=finding,
        classification=result["decision"],
        reason=result["reason"],
        risk=result["risk"],
        fix_shape=result["fix_shape"],
        precedent_output=precedent,
    )


if __name__ == "__main__":
    main()