#!/usr/bin/env python3
"""Create an isolated repository for a fixture-backed skill evaluation."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases.jsonl"
FIXTURES = ROOT / "evals" / "fixtures"
CASE_COMMANDS = {
    "greenfield-production-design": {
        "verify": "find docs/plans -maxdepth 1 -type f -name '*.md' -print",
        "inspect_diff": "git diff --stat",
    },
    "bounded-chunk-config": {
        "verify": "python3 -m unittest discover -s tests -v",
        "inspect_diff": "git diff -- app/config.py tests/test_config.py",
    },
    "missing-bounded-change-target": {
        "verify": "git status --short",
        "inspect_diff": "git diff --exit-code",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_id", help="Evaluation case with a matching fixture.")
    parser.add_argument("--output", required=True, type=Path, help="New workspace path.")
    return parser.parse_args()


def load_case(case_id: str) -> dict[str, Any]:
    with CASES.open(encoding="utf-8") as handle:
        for line in handle:
            case = json.loads(line)
            if case.get("id") == case_id:
                return case
    raise ValueError(f"unknown evaluation case: {case_id}")


def prepare_workspace(case_id: str, output: Path) -> dict[str, str]:
    case = load_case(case_id)
    fixture = FIXTURES / case_id
    if not fixture.is_dir():
        raise ValueError(f"evaluation case has no workspace fixture: {case_id}")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"output directory is not empty: {output}")

    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture, output, dirs_exist_ok=True)
    subprocess.run(
        ["git", "init", "--initial-branch=main", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(output), "add", "--all"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(output),
            "-c",
            "user.name=Agent Skill Eval",
            "-c",
            "user.email=eval@example.invalid",
            "commit",
            "-m",
            "Create evaluation baseline",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "case_id": case_id,
        "workspace": str(output.resolve()),
        "prompt": case["prompt"],
        **CASE_COMMANDS.get(
            case_id,
            {
                "verify": "git status --short",
                "inspect_diff": "git diff --exit-code",
            },
        ),
    }


def main() -> int:
    args = parse_args()
    try:
        result = prepare_workspace(args.case_id, args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
