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


def duration_ms(value: str, default_unit: str | None = None) -> float | None:
    match = DURATION_PATTERN.search(value.replace("**", ""))
    if match:
        number = float(match.group(1).replace(",", ""))
        unit = match.group(2).lower()
    else:
        number_match = re.fullmatch(
            r"\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*",
            value.replace("**", "").replace("`", ""),
        )
        if not number_match or default_unit is None:
            return None
        number = float(number_match.group(1).replace(",", ""))
        unit = default_unit
    return number if unit == "ms" or unit.startswith("millisecond") else number * 1000


def validate_latency_budget(body: str) -> list[str]:
    errors: list[str] = []
    lines = body.splitlines()
    tables: list[tuple[str, list[tuple[str, str, float | None, str]]]] = []

    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        headers = [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        if len(headers) < 2 or "stage" not in headers[0] or "budget" not in headers[1]:
            continue
        if sum("budget" in header for header in headers[1:]) > 1:
            errors.append(
                "P3 latency tables must use one critical percentile per table; "
                "use separate tables instead of p50, p95, and p99 budget columns"
            )
        default_unit = None
        if re.search(r"\bms\b|milliseconds?", headers[1]):
            default_unit = "ms"
        elif re.search(r"\bseconds?\b|\(s\)", headers[1]):
            default_unit = "s"
        label = f"table {len(tables) + 1}"
        for prior in reversed(lines[:index]):
            heading = re.match(r"^#{3,6}\s+(.+)$", prior)
            if heading:
                label = heading.group(1).strip()
                break
        rows: list[tuple[str, str, float | None, str]] = []
        for row in lines[index + 2 :]:
            if not row.lstrip().startswith("|"):
                break
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            value = duration_ms(cells[1], default_unit)
            rows.append(
                (
                    cells[0].replace("**", ""),
                    cells[1].replace("**", ""),
                    value,
                    " ".join(cells[2:]),
                )
            )
        tables.append((label, rows))

    if not tables:
        return ["P3 budgets must include a stage latency budget table"]

    for label, rows in tables:
        prefix = "P3 latency budget"
        if len(tables) > 1:
            prefix += f" '{label}'"
        total_rows = [row for row in rows if "total" in row[0].lower()]
        stage_rows = [row for row in rows if "total" not in row[0].lower()]
        if not total_rows:
            errors.append(f"{prefix} must include a declared total")
        elif len(total_rows) > 1:
            errors.append(
                f"{prefix} must describe one critical path with one total; "
                "use a separate table for each primary or fallback path"
            )
        elif stage_rows:
            total = total_rows[0]
            unknown_stages = [row for row in stage_rows if row[2] is None]
            if total[2] is not None and unknown_stages:
                errors.append(
                    f"{prefix} cannot declare a numeric total while stage "
                    "budgets remain symbolic or UNKNOWN"
                )
            elif total[2] is not None:
                declared = total[2]
                calculated = sum(row[2] or 0 for row in stage_rows)
                if abs(declared - calculated) > 0.5:
                    errors.append(
                        f"{prefix} total does not match its stage budgets: "
                        f"declared {declared:g} ms, calculated {calculated:g} ms"
                    )
            elif not re.search(
                r"(?:=|sum|subtotal).*headroom|headroom.*(?:=|sum|subtotal)",
                total[1] + " " + total[3],
                re.IGNORECASE,
            ):
                errors.append(
                    f"{prefix} symbolic total must provide a recomputable "
                    "stage-subtotal-plus-headroom formula"
                )

        headroom_rows = [row for row in stage_rows if "headroom" in row[0].lower()]
        has_positive_headroom = any(
            (row[2] is not None and row[2] > 0)
            or bool(
                re.search(
                    r"(?:[1-9][0-9]*(?:\.[0-9]+)?\s*%|"
                    r"0?\.[0-9]*[1-9][0-9]*\s*\*\s*(?:stage[_ ]?)?subtotal)",
                    row[1] + " " + row[3],
                    re.IGNORECASE,
                )
            )
            for row in headroom_rows
        )
        if not has_positive_headroom:
            errors.append(f"{prefix} must reserve positive headroom")

        if any(
            row[2] is not None
            and re.search(r"placeholder", row[1] + " " + row[3], re.IGNORECASE)
            for row in headroom_rows
        ):
            errors.append(
                f"{prefix} must not invent a numeric headroom placeholder; "
                "use measured evidence or a symbolic positive formula"
            )

        if any(
            re.search(
                r"\b(?:concurrent(?:ly)?|parallel)\s+with\b", row[3], re.IGNORECASE
            )
            for row in stage_rows
        ):
            errors.append(
                f"{prefix} must combine concurrent branches into one "
                "critical-path row"
            )

    return errors


def validate_decision_table(body: str) -> list[str]:
    for line in body.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        headers = [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        has_decision = any("decision" in cell or "question" in cell for cell in headers)
        has_recommendation = any("recommend" in cell for cell in headers)
        has_alternatives = any("alternative" in cell or "option" in cell for cell in headers)
        has_impact = any("impact" in cell or "consequence" in cell for cell in headers)
        if has_decision and has_recommendation and has_alternatives and has_impact:
            return []
    return [
        "AWAITING_DECISIONS plans require a decision table with Decision, "
        "Recommendation, Alternatives, and Impact columns"
    ]


def has_owner_decision_blocker(text: str) -> bool:
    return bool(
        re.search(
            r"(?:owner|user|stakeholder|business|security|platform)"
            r"[^.\n]{0,60}(?:decision|input|confirmation|approval)|"
            r"(?:decision|input|confirmation|approval)"
            r"[^.\n]{0,60}(?:owner|user|stakeholder|business|security|platform)|"
            r"decisions?\s+(?:that\s+)?(?:require|need|await)"
            r"[^.\n]{0,40}(?:input|answer|confirmation|approval)|"
            r"decisions?\s+[^.\n]{0,40}(?:must be answered|are answered)",
            text,
            re.IGNORECASE,
        )
    )


def validate_ready_state(
    text: str, status: str | None, result: str | None
) -> list[str]:
    if result != "READY" and status not in {
        "READY",
        "APPROVED",
        "IN_PROGRESS",
        "IMPLEMENTED",
    }:
        return []

    errors: list[str] = []
    owners = metadata_value(text, "Owners") or ""
    if re.search(r"\bUNKNOWN\b|\bTBD\b", owners, re.IGNORECASE):
        errors.append("READY plans require a named accountable owner")

    evidence = heading_body(text, "Evidence and assumptions") or ""
    material_input = re.compile(
        r"vendor|provider|transaction|database|write path|authorization|ACL|"
        r"tenant|SLO|service level|cost budget|cost ceiling|risk acceptance|"
        r"QPS|query rate|workload|corpus|chunk count|rollout",
        re.IGNORECASE,
    )
    for line in evidence.splitlines():
        if "UNKNOWN" in line.upper() and material_input.search(line):
            errors.append(
                "READY plans cannot retain material UNKNOWN inputs for "
                "architecture, security, service levels, cost, or rollout"
            )
            break

    assumptions = heading_body(text, "Planning assumptions package") or ""
    if assumptions and re.search(
        r"owner input|before implementation|must be (?:validated|confirmed|replaced)|"
        r"placeholder|assumed true|owner approval|required before",
        assumptions,
        re.IGNORECASE,
    ):
        errors.append(
            "READY plans cannot replace unresolved owner decisions with a "
            "planning assumptions package"
        )

    if re.search(
        r"(?:can|will)\s+(?:then\s+)?be marked\s+`?READY`?|"
        r"before implementation[^.\n]{0,120}(?:replace|validate|confirm|approve)|"
        r"(?:replace|validate|validated|confirm|approve)"
        r"[^.\n]{0,120}before implementation|"
        r"owner-dependent\s+unknowns?",
        text,
        re.IGNORECASE,
    ):
        errors.append(
            "READY status contradicts unresolved pre-implementation decisions "
            "or evidence gates"
        )
    return errors


def validate_security_language(text: str) -> list[str]:
    errors: list[str] = []
    for line in text.splitlines():
        if re.search(r"fail[- ]?open", line, re.IGNORECASE) and re.search(
            r"auth|ACL|tenant|permission|policy|unauthorized|deny", line, re.IGNORECASE
        ):
            errors.append("authorization and tenant-isolation failures must fail closed")
            break

    for line in text.splitlines():
        if re.search(
            r"(?:read[- ]only|retention[- ]only).*(?:fallback|failover|failback)|"
            r"(?:fallback|failover|failback).*(?:read[- ]only|retention[- ]only)",
            line,
            re.IGNORECASE,
        ) and not re.search(r"\b(?:not|never|cannot|no longer)\b", line, re.IGNORECASE):
            errors.append("read-only or retention-only indexes cannot serve as failover")
            break
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


def validate_zero_downtime_without_cdc(text: str) -> list[str]:
    if not re.search(r"zero[- ]downtime|zero\s+customer[- ]facing\s+downtime", text, re.IGNORECASE):
        return []
    if not re.search(
        r"(?:no|without|lacks?|absent|none)[^\n.]{0,80}"
        r"(?:CDC|change data capture|mutation log|change stream|watermark)|"
        r"(?:CDC|change data capture|mutation log|change stream|watermark)"
        r"[^\n.]{0,50}(?:does not exist|unavailable|absent|none)",
        text,
        re.IGNORECASE,
    ):
        return []

    errors: list[str] = []
    if not re.search(
        r"transactional\s+outbox|"
        r"(?:same|single)\s+(?:database\s+)?transaction[^.\n]{0,100}"
        r"(?:outbox|journal|event)|"
        r"(?:outbox|journal|event)[^.\n]{0,100}"
        r"(?:same|single)\s+(?:database\s+)?transaction|"
        r"atomically[^.\n]{0,100}(?:source|business)\s+mutation",
        text,
        re.IGNORECASE,
    ):
        errors.append(
            "zero-downtime migration without source CDC requires atomic "
            "source-mutation capture, such as a transactional outbox"
        )

    if not re.search(
        r"(?:start|enable|activate|establish)[^.\n]{0,80}"
        r"(?:capture|outbox|journal)[^.\n]{0,80}before[^.\n]{0,80}"
        r"(?:snapshot|backfill)|"
        r"(?:capture|outbox|journal)[^.\n]{0,80}(?:active|enabled)"
        r"[^.\n]{0,80}before[^.\n]{0,80}(?:snapshot|backfill)",
        text,
        re.IGNORECASE,
    ):
        errors.append(
            "zero-downtime migration without source CDC must activate ordered "
            "capture before the bootstrap snapshot or backfill"
        )

    if not re.search(
        r"(?:bypass|uncontrolled|direct|legacy|admin|background)[^.\n]{0,140}"
        r"(?:block|cannot|impossible|unprovable|write freeze|guarantee breaks)|"
        r"(?:block|cannot|impossible|unprovable|write freeze|guarantee breaks)"
        r"[^.\n]{0,140}(?:bypass|uncontrolled|direct|legacy|admin|background)",
        text,
        re.IGNORECASE,
    ):
        errors.append(
            "zero-downtime migration without source CDC must block cutover or "
            "require an approved write freeze when any writer bypasses capture"
        )
    return errors


def validate_migration_fallback(text: str) -> list[str]:
    correctness = heading_body(text, "Migration correctness") or ""
    rollout = heading_body(text, "Rollout and rollback") or ""
    fallback_text = correctness + "\n" + rollout
    old_vendor = r"Vendor\s+A|Old[- ]Vendor|old\s+(?:vendor|index|provider)"
    fallback = r"fallback|failback|rollback"

    if not re.search(
        rf"(?:{fallback})[^.\n]{{0,100}}(?:{old_vendor})|"
        rf"(?:{old_vendor})[^.\n]{{0,100}}(?:{fallback})",
        fallback_text,
        re.IGNORECASE,
    ):
        return []

    errors: list[str] = []
    snapshot_only_fallback = re.search(
        rf"(?:{old_vendor})[^.\n]{{0,160}}(?:only|solely)"
        r"[^.\n]{0,80}(?:nightly|periodic)?\s*snapshots?|"
        rf"(?:only|solely)[^.\n]{{0,80}}(?:nightly|periodic)?\s*snapshots?"
        rf"[^.\n]{{0,160}}(?:{old_vendor})",
        text,
        re.IGNORECASE,
    )
    ordered_to_fallback = re.search(
        rf"(?:{old_vendor})[^.\n]{{0,140}}"
        r"(?:ordered|dual[- ]write|outbox|mutation|delete|revocation)|"
        r"(?:ordered|dual[- ]write|outbox|mutation|delete|revocation)"
        rf"[^.\n]{{0,140}}(?:{old_vendor})|"
        r"(?:tombstone|delete|revocation|mutation)[^.]{0,140}"
        r"both\s+(?:indexes|vendors|providers)[^.]{0,80}"
        r"(?:acknowledge|receive|apply)|"
        r"both\s+(?:indexes|vendors|providers)[^.]{0,80}"
        r"(?:acknowledge|receive|apply)[^.]{0,140}"
        r"(?:tombstone|delete|revocation|mutation)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if snapshot_only_fallback or not ordered_to_fallback:
        errors.append(
            "MIGRATE fallback must receive ordered content, delete, and "
            "permission-revocation mutations"
        )

    has_data_gate = re.search(
        rf"(?:{fallback})[^.]{{0,180}}(?:data|content)"
        r"[^.]{0,80}(?:watermark|freshness|version|reconciliation)|"
        r"(?:data|content)[^.]{0,80}(?:watermark|freshness|version|reconciliation)"
        rf"[^.]{{0,180}}(?:{fallback})",
        fallback_text,
        re.IGNORECASE | re.DOTALL,
    )
    has_policy_gate = re.search(
        rf"(?:{fallback})[^.]{{0,180}}(?:policy|authorization|ACL|permission)"
        r"[^.]{0,80}(?:watermark|freshness|version|reconciliation)|"
        r"(?:policy|authorization|ACL|permission)"
        r"[^.]{0,80}(?:watermark|freshness|version|reconciliation)"
        rf"[^.]{{0,180}}(?:{fallback})",
        fallback_text,
        re.IGNORECASE | re.DOTALL,
    )
    if not has_data_gate or not has_policy_gate:
        errors.append(
            "MIGRATE fallback eligibility requires separate data and policy "
            "freshness gates"
        )

    if re.search(
        r"fallback[^.\n]{0,100}(?:acceptable|allowed)[^.\n]{0,100}tolerat|"
        r"fallback\.allow_stale|allow[_ -]?stale[_ -]?(?:index|fallback)",
        text,
        re.IGNORECASE,
    ):
        errors.append(
            "stale authorization state cannot be made fallback-eligible by "
            "query sensitivity or tolerance"
        )
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

    backfill_formula_match = re.search(
        r"backfill\s+cost.*?(?=\n(?:#{1,6}\s+|"
        r"(?:incremental\s+)?dual[- ]run\s+cost|"
        r"steady[- ]state\s+cost)|\Z)",
        budgets,
        re.IGNORECASE | re.DOTALL,
    )
    if backfill_formula_match:
        formula = backfill_formula_match.group(0)
        cost_expression = re.search(
            r"(?:backfill_write_cost|(?:one[- ]time\s+)?backfill\s+cost)"
            r"\**\s*=\s*(.*?)(?=\n\s*(?:[A-Za-z][A-Za-z _-]*cost|"
            r"backfill_duration|reembedding_cost)\s*=|\n\s*\n|\Z)",
            formula,
            re.IGNORECASE | re.DOTALL,
        )
        if cost_expression and re.search(
            r"/.*(?:throughput|chunks/s|chunks per second).*(?:\*|×)",
            cost_expression.group(1),
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
    risks_body = heading_body(text, "Risks and decisions") or ""
    evidence_body = heading_body(text, "Evidence and assumptions") or ""
    assumptions_body = heading_body(text, "Planning assumptions package") or ""
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

    has_open_decisions = has_owner_decision_blocker(
        evidence_body + "\n" + risks_body + "\n" + assumptions_body + "\n" + audit_body
    ) or bool(
        re.search(
            r"\b(?:AWAITING_DECISIONS|open decisions?|blocking decisions?|"
            r"decisions? required from)\b",
            risks_body + "\n" + audit_body,
            re.IGNORECASE,
        )
    )
    if has_open_decisions:
        if status != "AWAITING_DECISIONS" or result != "AWAITING_DECISIONS":
            errors.append(
                "plans blocked only by owner input must use AWAITING_DECISIONS "
                "for both Status and Result"
            )
        errors.extend(validate_decision_table(risks_body))

    errors.extend(validate_ready_state(text, status, result))

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
            errors.extend(validate_zero_downtime_without_cdc(text))
            errors.extend(validate_migration_fallback(text))
            rollout_body = heading_body(text, "Rollout and rollback") or ""
            errors.extend(validate_rollout_windows(rollout_body))

    errors.extend(validate_security_language(text))

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
