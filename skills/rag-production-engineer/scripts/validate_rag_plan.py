#!/usr/bin/env python3
"""Validate that a RAG architecture plan covers production concerns."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_SECTIONS = (
    "use_case",
    "workload",
    "architecture",
    "ingestion",
    "retrieval",
    "generation",
    "evaluation",
    "observability",
    "reliability",
    "security",
    "vendors",
    "rollout",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    return parser.parse_args()


def validate(plan: Any) -> list[str]:
    if not isinstance(plan, dict):
        return ["root must be a JSON object"]

    errors: list[str] = []
    for section in REQUIRED_SECTIONS:
        value = plan.get(section)
        if value is None:
            errors.append(f"missing section: {section}")
            continue
        if not isinstance(value, dict):
            errors.append(f"section {section} must be an object")
            continue
        if not value:
            errors.append(
                f"section {section} is empty; add decisions or status=unknown"
            )
        elif value.get("status") == "unknown" and len(value) == 1:
            continue
    return errors


def main() -> int:
    args = parse_args()
    try:
        with args.plan.open(encoding="utf-8") as handle:
            plan = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    errors = validate(plan)
    if errors:
        print("RAG plan validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("RAG plan is complete enough for review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
