#!/usr/bin/env python3

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


def normalize(value: str) -> str:
    value = value.lower()
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"www\.", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def similarity(a: str, b: str) -> float:
    a_norm = normalize(a)
    b_norm = normalize(b)

    if not a_norm or not b_norm:
        return 0.0

    if a_norm == b_norm:
        return 1.0

    if a_norm in b_norm or b_norm in a_norm:
        return 0.92

    return SequenceMatcher(None, a_norm, b_norm).ratio()


def extract_github_urls(company: dict) -> list[str]:
    fields = [
        company.get("website", ""),
        company.get("long_description", ""),
        company.get("one_liner", ""),
    ]

    combined = "\n".join(str(f) for f in fields if f)

    matches = re.findall(
        r"https?://github\.com/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?",
        combined,
    )

    deduped = []

    for match in matches:
        if match not in deduped:
            deduped.append(match)

    return deduped


def load_json(path: Path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(
        description="Search YC public JSON for likely matching repos/companies."
    )

    parser.add_argument(
        "--json",
        required=True,
        help="Path to YC JSON file.",
    )

    parser.add_argument(
        "--query",
        required=True,
        help="Search query/company/person.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--out",
        default="output/yc_matches.txt",
    )

    args = parser.parse_args()

    json_path = Path(args.json).expanduser()
    out_path = Path(args.out).expanduser()

    companies = load_json(json_path)

    results = []

    for company in companies:
        candidates = [
            company.get("name", ""),
            company.get("slug", ""),
            company.get("website", ""),
            company.get("one_liner", ""),
        ]

        best_score = max(
            similarity(args.query, candidate)
            for candidate in candidates
            if candidate
        )

        github_urls = extract_github_urls(company)

        results.append(
            {
                "score": best_score,
                "company": company.get("name", ""),
                "website": company.get("website", ""),
                "github_urls": github_urls,
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)

    top = results[: args.limit]

    lines = []

    print()
    print("YC PUBLIC JSON SEARCH")
    print("=" * 60)
    print(f'query: "{args.query}"')
    print()

    for result in top:
        company = result["company"]
        score = result["score"]
        website = result["website"]

        print(f"{company}  (match={score:.2f})")

        if website:
            print(f"website: {website}")

        if result["github_urls"]:
            print("github:")
            for url in result["github_urls"]:
                print(f"  - {url}")

        print()

        lines.append(
            f"{company}\tmatch={score:.2f}\t{website}"
        )

        for url in result["github_urls"]:
            lines.append(f"  github: {url}")

        lines.append("")

    out_path.write_text("\n".join(lines))

    print(f"Wrote results to {out_path}")


if __name__ == "__main__":
    main()