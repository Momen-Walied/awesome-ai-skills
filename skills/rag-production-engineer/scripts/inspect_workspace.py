#!/usr/bin/env python3
"""Report portable agent, workflow, skill, and project signals in a repository."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


INSTRUCTION_NAMES = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "KIMI.md",
    "CONTRIBUTING.md",
)
WORKFLOW_MARKERS = {
    "spec-kit": (".specify", "specs"),
    "openspec": ("openspec", ".openspec"),
    "repository-plans": ("docs/plans", ".plans"),
}
SKILL_ROOTS = (
    ".agents/skills",
    ".claude/skills",
    ".opencode/skills",
    ".codex/skills",
)
MANIFESTS = (
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Makefile",
    "justfile",
)
EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "vendor",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    return parser.parse_args()


def instruction_files(root: Path) -> list[str]:
    names = set(INSTRUCTION_NAMES)
    matches: list[str] = []
    for directory, child_directories, files in os.walk(root):
        child_directories[:] = sorted(
            name for name in child_directories if name not in EXCLUDED_DIRECTORIES
        )
        current = Path(directory)
        matches.extend(
            str((current / name).relative_to(root)) for name in files if name in names
        )
    return sorted(matches)


def inspect(root: Path) -> dict[str, object]:
    root = root.resolve()
    instructions = instruction_files(root)
    workflows = {
        workflow: [marker for marker in markers if (root / marker).exists()]
        for workflow, markers in WORKFLOW_MARKERS.items()
    }
    workflows = {name: markers for name, markers in workflows.items() if markers}
    skill_roots = [path for path in SKILL_ROOTS if (root / path).is_dir()]
    manifests = [path for path in MANIFESTS if (root / path).is_file()]
    tests = sorted(
        str(path.relative_to(root))
        for pattern in ("tests", "test", "evals", "evaluation")
        for path in root.glob(pattern)
        if path.exists()
    )
    return {
        "root": str(root),
        "instructions": instructions,
        "workflows": workflows,
        "skill_roots": skill_roots,
        "manifests": manifests,
        "test_and_eval_roots": tests,
    }


def main() -> int:
    args = parse_args()
    if not args.root.is_dir():
        print(json.dumps({"error": f"not a directory: {args.root}"}))
        return 2
    print(json.dumps(inspect(args.root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
