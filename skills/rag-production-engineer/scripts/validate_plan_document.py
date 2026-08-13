#!/usr/bin/env python3
"""Validate the structure of a persistent P2 or P3 RAG plan."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_METADATA = ("Status", "Mode", "Owners", "Last updated")
REQUIRED_SECTIONS = (
    "Outcome",
    "Scope",
    "Evidence and assumptions",
    "Current system",
    "Target system",
    "Gap analysis",
    "Delivery plan",
    "Evaluation and acceptance",
    "Operability",
    "Rollout and rollback",
    "Risks and decisions",
    "Plan audit",
)
P3_REQUIRED_SECTIONS = ("Capacity, latency, and cost budgets",)
VALID_STATUSES = {
    "PROPOSED",
    "AWAITING_DECISIONS",
    "READY",
    "APPROVED",
    "IN_PROGRESS",
    "IMPLEMENTED",
    "SUPERSEDED",
}
PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|TBD|FIXME|FILL[ -]?ME|IMPLEMENT LATER)\b|<[^>\n]+>",
    re.IGNORECASE,
)
DURATION_PATTERN = re.compile(
    r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(ms|milliseconds?|s|seconds?)\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--level", choices=("P2", "P3"), required=True)
    return parser.parse_args()


def heading_body(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def metadata_value(text: str, key: str) -> str | None:
    match = re.search(rf"^\*\*{re.escape(key)}:\*\*\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def duration_ms(value: str) -> float | None:
    match = DURATION_PATTERN.search(value.replace("**", ""))
    if not match:
        return None
    number = float(match.group(1).replace(",", ""))
    unit = match.group(2).lower()
    return number if unit == "ms" or unit.startswith("millisecond") else number * 1000


def validate_latency_budget(body: str) -> list[str]:
    errors: list[str] = []
    lines = body.splitlines()
    rows: list[tuple[str, float, str]] = []
    found_table = False

    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        headers = [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        if len(headers) < 2 or "stage" not in headers[0] or "budget" not in headers[1]:
            continue
        found_table = True
        for row in lines[index + 2 :]:
            if not row.lstrip().startswith("|"):
                break
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            value = duration_ms(cells[1])
            if value is not None:
                rows.append((cells[0].replace("**", ""), value, " ".join(cells[2:])))
        break

    if not found_table:
        return ["P3 budgets must include a stage latency budget table"]

    total_rows = [row for row in rows if "total" in row[0].lower()]
    stage_rows = [row for row in rows if "total" not in row[0].lower()]
    if not total_rows:
        errors.append("P3 latency budget table must include a declared total")
    elif stage_rows:
        declared = total_rows[-1][1]
        calculated = sum(row[1] for row in stage_rows)
        if abs(declared - calculated) > 0.5:
            errors.append(
                "P3 latency total does not match its stage budgets: "
                f"declared {declared:g} ms, calculated {calculated:g} ms"
            )

    if not any("headroom" in row[0].lower() and row[1] > 0 for row in stage_rows):
        errors.append("P3 latency budget must reserve positive headroom")

    if any("concurrent" in row[2].lower() for row in stage_rows):
        errors.append(
            "P3 latency table must combine concurrent branches into one "
            "critical-path row"
        )

    return errors


def validate(text: str, level: str) -> list[str]:
    errors: list[str] = []

    if not re.search(r"^# \S.+", text, re.MULTILINE):
        errors.append("missing level-one plan title")

    for key in REQUIRED_METADATA:
        if not metadata_value(text, key):
            errors.append(f"missing metadata: {key}")

    status = metadata_value(text, "Status")
    if status and status not in VALID_STATUSES:
        errors.append(f"invalid status: {status}")

    for section in REQUIRED_SECTIONS:
        body = heading_body(text, section)
        if body is None:
            errors.append(f"missing section: {section}")
        elif not body:
            errors.append(f"empty section: {section}")

    if level == "P3":
        for section in P3_REQUIRED_SECTIONS:
            body = heading_body(text, section)
            if body is None:
                errors.append(f"missing P3 section: {section}")
            elif not body:
                errors.append(f"empty P3 section: {section}")

    mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)```", text, re.DOTALL)
    flowcharts = [block for block in mermaid_blocks if re.search(r"\bflowchart\b", block)]
    sequences = [
        block for block in mermaid_blocks if re.search(r"\bsequenceDiagram\b", block)
    ]
    if len(flowcharts) < 2:
        errors.append("include separate current-state and target-state flowcharts")
    if level == "P3" and not sequences:
        errors.append("P3 plans require a migration, cutover, or failure sequence diagram")

    current_body = heading_body(text, "Current system") or ""
    target_body = heading_body(text, "Target system") or ""
    if "```mermaid" not in current_body:
        errors.append("Current system must contain its Mermaid diagram")
    if "```mermaid" not in target_body:
        errors.append("Target system must contain its Mermaid diagram")

    audit_body = heading_body(text, "Plan audit") or ""
    if not re.search(r"\b(?:PASS|FAIL|READY|AWAITING_DECISIONS)\b", audit_body):
        errors.append("Plan audit must record an explicit result")

    if "AWAITING_DECISIONS" in audit_body and status != "AWAITING_DECISIONS":
        errors.append(
            "Status must be AWAITING_DECISIONS when the audit result is "
            "AWAITING_DECISIONS"
        )
    if re.search(r"\bREADY\b", audit_body) and status not in {
        "READY",
        "APPROVED",
        "IN_PROGRESS",
        "IMPLEMENTED",
    }:
        errors.append("Status must reflect a READY audit result")

    if level == "P3":
        budget_body = heading_body(text, "Capacity, latency, and cost budgets")
        if budget_body:
            if not re.search(
                r"\b(?:QPS|queries per second|chunks per second)\b",
                budget_body,
                re.IGNORECASE,
            ):
                errors.append("P3 budgets must include a capacity rate with units")
            if not re.search(
                r"\b(?:ms|milliseconds?|seconds?)\b",
                budget_body,
                re.IGNORECASE,
            ):
                errors.append("P3 budgets must include latency units")
            if not re.search(
                r"(?:cost|USD|\$).*?(?:=|formula|UNKNOWN)",
                budget_body,
                re.IGNORECASE | re.DOTALL,
            ):
                errors.append(
                    "P3 budgets must include a cost formula or explicit unknown"
                )
            if not re.search(
                r"\b(?:MEASURED|ESTIMATED|PROPOSED|UNKNOWN)\b", budget_body
            ):
                errors.append("P3 budgets must label numerical evidence")
            errors.extend(validate_latency_budget(budget_body))

    placeholders = sorted(set(PLACEHOLDER_PATTERN.findall(text)))
    if placeholders:
        errors.append("unresolved placeholders: " + ", ".join(placeholders))

    return errors


def main() -> int:
    args = parse_args()
    try:
        text = args.plan.read_text(encoding="utf-8")
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    errors = validate(text, args.level)
    if errors:
        print(f"{args.level} plan validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"{args.level} plan structure is ready for semantic audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
