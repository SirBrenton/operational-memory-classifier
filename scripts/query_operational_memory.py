#!/usr/bin/env python3

import argparse
import re
import subprocess
from pathlib import Path

DEFAULT_IMPORT_DIR = Path(
    "~/Development-Projects/practicallyai/cases/gbrain-hackathon/demo-import-expanded"
).expanduser()

DEFAULT_QUERY = (
    "where do systems receive the right operational signal "
    "but make the wrong execution decision?"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Render GBrain receipt query results as clean operational memory."
    )
    parser.add_argument("query", nargs="?", default=DEFAULT_QUERY)
    parser.add_argument("--import-dir", default=str(DEFAULT_IMPORT_DIR))
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--mode",
        choices=["full", "stage"],
        default="full",
        help="full = detailed cards; stage = compact live-demo cards",
    )
    return parser.parse_args()


def run_gbrain_query(query: str) -> str:
    cmd = [
        "gtimeout",
        "8s",
        "bun",
        "run",
        "src/cli.ts",
        "query",
        query,
    ]

    proc = subprocess.run(
        cmd,
        cwd=Path("~/Development-Projects/gbrain").expanduser(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    return proc.stdout


def extract_slugs(output: str) -> list[str]:
    slugs = re.findall(r"\]\s+(pt-[a-z0-9\-]+)\s+--", output)
    seen = set()
    ordered = []

    for slug in slugs:
        if slug not in seen:
            seen.add(slug)
            ordered.append(slug)

    return ordered


def section(md: str, heading: str) -> str:
    pattern = rf"## {re.escape(heading)}\n\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, md, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def title(md: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", md, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def compact(text: str, max_chars: int = 520) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())

    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]

    sentence_break = max(
        truncated.rfind(". "),
        truncated.rfind("! "),
        truncated.rfind("? "),
    )

    if sentence_break > max_chars * 0.6:
        return truncated[: sentence_break + 1].strip()

    word_break = truncated.rfind(" ")

    if word_break > 0:
        return truncated[:word_break].rstrip() + "…"

    return truncated.rstrip() + "…"


def first_sentence(text: str, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return fallback

    match = re.search(r"(.+?[.!?])(\s|$)", text)
    if match:
        return match.group(1).strip()

    return compact(text, 180)


def clean_empty_none_block(text: str) -> str:
    text = re.sub(r"^- none\s*$", "", text, flags=re.MULTILINE).strip()

    if text.strip() == "This failure can create:":
        return ""

    return text


def render_receipt_stage(path: Path, slug: str) -> str:
    md = path.read_text()

    t = title(md, slug)
    failure_shape = section(md, "Failure Shape")
    why = clean_empty_none_block(section(md, "Why It Matters"))

    summary_match = re.search(
        r"Summary:\n\n(.*?)(?=\n\nConstraints|\Z)",
        failure_shape,
        flags=re.DOTALL,
    )
    summary = summary_match.group(1).strip() if summary_match else failure_shape

    effect = first_sentence(why, fallback="")
    summary_line = first_sentence(summary, fallback="Operational failure pattern surfaced.")

    cleaned_effect = effect.replace("This failure can create:", "").strip()
    effect_line = (
        f"\nEffect: {compact(cleaned_effect, 220)}"
        if cleaned_effect
        else ""
    )

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{t}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pattern: {compact(summary_line, 220)}{effect_line}
""".strip()


def main():
    args = parse_args()
    import_dir = Path(args.import_dir).expanduser()

    raw = run_gbrain_query(args.query)
    slugs = extract_slugs(raw)[: args.limit]

    print()
    print("OPERATIONAL MEMORY QUERY")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(args.query)
    print()

    if not slugs:
        print("No receipt slugs returned by GBrain.")
        return

    rendered = 0

    for slug in slugs:
        path = import_dir / f"{slug}.md"

        if not path.exists():
            continue

        if args.mode == "stage":
            print(render_receipt_stage(path, slug))
        else:
            print(render_receipt_stage(path, slug))

        print()
        rendered += 1

    if rendered == 0:
        print("GBrain returned slugs, but no matching markdown files were found.")
        print()
        print("Returned slugs:")
        for slug in slugs:
            print(f"- {slug}")


if __name__ == "__main__":
    main()