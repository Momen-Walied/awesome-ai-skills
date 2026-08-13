#!/usr/bin/env python3
"""Validate required contracts in a persistent P2 or P3 RAG plan."""

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
MIGRATION_REQUIRED_SECTIONS = ("Compatibility matrix", "Migration correctness")
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
ROLLOUT_WINDOW_PATTERN = re.compile(
    r"\b(?:canary|burn[- ]?in|hold|dual[- ]run window|retirement window)\b.*?"
    r"\b\d+(?:\s*[-–]\s*\d+)?\s*(?:minutes?|hours?|days?|h|d)\b",
    re.IGNORECASE,
)
EVIDENCE_LABEL_PATTERN = re.compile(
    r"\b(?:MEASURED|ESTIMATED|PROPOSED|DECIDED|UNKNOWN)\b"
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


def audit_result(body: str) -> str | None:
    match = re.search(r"^(?:\*\*)?Result:(?:\*\*)?\s*(.+)$", body, re.MULTILINE)
    if not match:
        return None
    value = match.group(1)
    for result in ("AWAITING_DECISIONS", "READY", "FAIL", "PASS"):
        if re.search(rf"\b{result}\b", value):
            return result
    return None


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
    elif len(total_rows) > 1:
        errors.append(
            "P3 latency table must describe one critical path with one total; "
            "use a separate table for each primary or fallback path"
        )
    elif stage_rows:
        declared = total_rows[0][1]
        calculated = sum(row[1] for row in stage_rows)
        if abs(declared - calculated) > 0.5:
            errors.append(
                "P3 latency total does not match its stage budgets: "
                f"declared {declared:g} ms, calculated {calculated:g} ms"
            )

    if not any("headroom" in row[0].lower() and row[1] > 0 for row in stage_rows):
        errors.append("P3 latency budget must reserve positive headroom")

    if any(
        re.search(r"\b(?:concurrent(?:ly)?|parallel)\s+with\b", row[2], re.IGNORECASE)
        for row in stage_rows
    ):
        errors.append(
            "P3 latency table must combine concurrent branches into one "
            "critical-path row"
        )

    return errors


def validate_budget_assumptions(body: str) -> list[str]:
    errors: list[str] = []
    for line in body.splitlines():
        if re.search(r"\bpeak\s*/\s*\d", line, re.IGNORECASE):
            errors.append(
                "P3 budgets must not derive average traffic or duty cycle from "
                "an invented peak ratio"
            )
            break
    return errors


def validate_rollout_windows(body: str) -> list[str]:
    errors: list[str] = []
    for line in body.splitlines():
        if ROLLOUT_WINDOW_PATTERN.search(line) and not EVIDENCE_LABEL_PATTERN.search(line):
            errors.append(
                "P3 canary, hold, burn-in, and retirement windows must carry "
                "an evidence label"
            )
            break
    return errors


def validate_migration_contracts(text: str) -> list[str]:
    errors: list[str] = []
    compatibility = heading_body(text, "Compatibility matrix") or ""
    correctness = heading_body(text, "Migration correctness") or ""
    budgets = heading_body(text, "Capacity, latency, and cost budgets") or ""
    rollout = heading_body(text, "Rollout and rollback") or ""
    mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)```", text, re.DOTALL)
    sequence_text = "\n".join(
        block for block in mermaid_blocks if re.search(r"\bsequenceDiagram\b", block)
    )

    compatibility_checks = (
        (r"embedding", "embedding model"),
        (r"dimension", "embedding dimensions"),
        (r"(?:distance metric|similarity metric)", "distance or similarity metric"),
        (r"(?:identifier|stable id|document id|chunk id)", "stable identifiers"),
        (r"(?:ACL|authoriz|filter)", "ACL and filter semantics"),
        (r"score", "score semantics"),
        (
            r"(?:score threshold|threshold consumer|confidence cutoff|consumer[^\n|]*raw score)",
            "score threshold consumers",
        ),
        (
            r"(?:generation|generator).*(?:schema|output)|"
            r"(?:schema|output).*(?:generation|generator)",
            "generation output contract",
        ),
    )
    if compatibility:
        for pattern, label in compatibility_checks:
            if not re.search(pattern, compatibility, re.IGNORECASE | re.DOTALL):
                errors.append(f"MIGRATE compatibility matrix must cover {label}")

    correctness_checks = (
        (r"source of truth", "an authoritative source of truth"),
        (r"(?:snapshot|checkpoint)", "a snapshot or checkpoint"),
        (
            r"(?:change[- ]stream|change capture|mutation stream)[^\n.]*watermark|"
            r"watermark[^\n.]*(?:change[- ]stream|change capture|mutation stream)",
            "a change-stream watermark",
        ),
        (r"version.*(?:order|conditional)|(?:order|conditional).*version", "version ordering"),
        (r"idempoten", "idempotent mutation handling"),
        (r"tombstone", "versioned tombstones"),
        (
            r"(?:permission|ACL|authoriz).*revocation|"
            r"revocation.*(?:permission|ACL|authoriz)",
            "permission revocation propagation",
        ),
        (r"replay", "mutation replay"),
        (r"reconcil", "cross-index reconciliation"),
        (
            r"fallback.*(?:fresh|watermark|current|consistent)|"
            r"(?:fresh|watermark|current|consistent).*fallback",
            "a fallback freshness gate",
        ),
    )
    if correctness:
        for pattern, label in correctness_checks:
            if not re.search(pattern, correctness, re.IGNORECASE | re.DOTALL):
                errors.append(f"MIGRATE correctness must define {label}")

        for vendor in ("Vendor A", "Vendor B"):
            vendor_pattern = re.escape(vendor).replace(r"\ ", r"\s+")
            if not re.search(
                rf"(?:{vendor_pattern}\s+(?:ACL|authorization)\s+adapter|"
                rf"(?:ACL|authorization)\s+adapter\s+(?:for\s+)?{vendor_pattern})",
                correctness,
                re.IGNORECASE,
            ):
                errors.append(
                    "MIGRATE correctness must define a separate "
                    f"{vendor} authorization adapter"
                )

    if not re.search(
        r"(?:retrieval.*generation|generation.*retrieval).*"
        r"(?:independent|separate).*(?:flag|canar)|"
        r"(?:independent|separate).*(?:flag|canar).*"
        r"(?:retrieval.*generation|generation.*retrieval)",
        text,
        re.IGNORECASE | re.DOTALL,
    ):
        errors.append(
            "MIGRATE plans must use independent retrieval and generation rollout flags or canaries"
        )
    if not re.search(r"crossed|factorial|four combinations", text, re.IGNORECASE):
        errors.append("MIGRATE plans must evaluate crossed retrieval and generation combinations")

    sequence_checks = (
        (r"(?:snapshot|checkpoint|watermark)", "snapshot or watermark"),
        (r"backfill", "backfill"),
        (r"dual[- ]write|ordered.*mutation", "ordered live mutations"),
        (r"reconcil", "reconciliation"),
        (r"shadow", "shadowing"),
        (r"canary", "canary"),
        (r"cutover", "cutover"),
        (r"fallback|failback", "fallback"),
        (r"retir", "retirement"),
    )
    for pattern, label in sequence_checks:
        if not re.search(pattern, sequence_text, re.IGNORECASE):
            errors.append(f"MIGRATE sequence diagram must show {label}")

    if not re.search(
        r"(?:one[- ]time\s+)?backfill\s+cost|"
        r"cost\s+(?:of|for)\s+(?:the\s+)?backfill",
        budgets,
        re.IGNORECASE,
    ):
        errors.append("MIGRATE budgets must include one-time backfill cost")
    if not re.search(
        r"(?:incremental\s+)?dual[- ]run\s+cost|"
        r"cost\s+(?:of|for|during)\s+(?:the\s+)?dual[- ]run",
        budgets,
        re.IGNORECASE,
    ):
        errors.append("MIGRATE budgets must include incremental dual-run cost")
    if not re.search(
        r"(?:migration|backfill)[_ ]duration.*(?:chunks per second|chunks/s|throughput)|"
        r"(?:chunks per second|chunks/s|throughput).*(?:migration|backfill)[_ ]duration",
        budgets,
        re.IGNORECASE | re.DOTALL,
    ):
        errors.append("MIGRATE budgets must separate backfill duration from cost")

    backfill_formula = next(
        (
            paragraph
            for paragraph in re.split(r"\n\s*\n", budgets)
            if re.search(r"backfill\s+cost", paragraph, re.IGNORECASE)
        ),
        None,
    )
    if backfill_formula:
        formula_match = re.search(
            r"backfill\s+cost", backfill_formula, re.IGNORECASE
        )
        if formula_match is None:
            raise AssertionError("backfill formula selection lost its marker")
        formula = backfill_formula[formula_match.start() :]
        if re.search(
            r"/.*(?:throughput|chunks/s|chunks per second).*(?:\*|×)",
            formula,
            re.IGNORECASE | re.DOTALL,
        ):
            errors.append(
                "MIGRATE backfill cost is dimensionally invalid: do not "
                "multiply duration by a per-chunk price"
            )
        if not re.search(
            r"billing unit|per\s+(?:1,?000|million|chunk|token|operation)",
            formula,
            re.IGNORECASE,
        ):
            errors.append("MIGRATE backfill cost must show the provider billing unit")

    for line in budgets.splitlines():
        if re.search(r"dual[- ]run\s+cost", line, re.IGNORECASE) and re.search(
            r"(?:\*|×|x)\s*2\b", line, re.IGNORECASE
        ):
            errors.append(
                "MIGRATE dual-run cost must price Vendor A and Vendor B "
                "separately instead of multiplying writes by two"
            )
            break
    if not re.search(
        r"(?:failure detection|timeout|deadline).*fallback retrieval|"
        r"fallback retrieval.*(?:failure detection|timeout|deadline)",
        budgets + "\n" + rollout,
        re.IGNORECASE | re.DOTALL,
    ):
        errors.append(
            "MIGRATE fallback budget must include primary failure detection and fallback retrieval"
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
    mode = metadata_value(text, "Mode")
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

    if level == "P3" and mode == "MIGRATE":
        for section in MIGRATION_REQUIRED_SECTIONS:
            body = heading_body(text, section)
            if body is None:
                errors.append(f"missing MIGRATE section: {section}")
            elif not body:
                errors.append(f"empty MIGRATE section: {section}")

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
    result = audit_result(audit_body)
    if result is None:
        errors.append("Plan audit must record an explicit result")

    if result == "AWAITING_DECISIONS" and status != "AWAITING_DECISIONS":
        errors.append(
            "Status must be AWAITING_DECISIONS when the audit result is "
            "AWAITING_DECISIONS"
        )
    if result == "READY" and status not in {
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
            errors.extend(validate_budget_assumptions(budget_body))

        if mode == "MIGRATE":
            errors.extend(validate_migration_contracts(text))
            rollout_body = heading_body(text, "Rollout and rollback") or ""
            errors.extend(validate_rollout_windows(rollout_body))

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

    print(f"{args.level} plan contract validation passed; ready for semantic audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
