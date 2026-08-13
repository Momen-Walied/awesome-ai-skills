#!/usr/bin/env python3
"""Validate and score portable Agent Skill behavior evaluations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


VALID_MODES = {
    "DESIGN",
    "IMPLEMENT",
    "DEBUG",
    "OPTIMIZE",
    "MIGRATE",
    "AUDIT",
    "OPERATE",
}
VALID_LEVELS = {"P0", "P1", "P2", "P3"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path, help="JSONL behavior case corpus.")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--results", type=Path, help="JSONL recorded agent outputs.")
    action.add_argument(
        "--emit-prompts",
        action="store_true",
        help="Write case IDs and prompts as JSONL for an external agent runner.",
    )
    action.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the case corpus without scoring results.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=1.0,
        help="Minimum passing check ratio from 0 to 1. Defaults to 1.",
    )
    return parser.parse_args()


def load_jsonl(path: Path, kind: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{kind} line {line_number}: invalid JSON: {error}"
                ) from error
            if not isinstance(record, dict):
                raise ValueError(f"{kind} line {line_number}: root must be an object")
            records.append(record)
    if not records:
        raise ValueError(f"{kind} file contains no records")
    return records


def validate_signal_map(value: Any, location: str) -> list[str]:
    errors: list[str] = []
    if value is None:
        return errors
    if not isinstance(value, dict):
        return [f"{location} must be an object"]
    for label, patterns in value.items():
        if not isinstance(label, str) or not label.strip():
            errors.append(f"{location} contains an empty label")
            continue
        if not isinstance(patterns, list) or not patterns:
            errors.append(f"{location}.{label} must be a non-empty list")
            continue
        for pattern in patterns:
            if not isinstance(pattern, str) or not pattern:
                errors.append(f"{location}.{label} contains an invalid pattern")
                continue
            try:
                re.compile(pattern)
            except re.error as error:
                errors.append(f"{location}.{label} has invalid regex {pattern!r}: {error}")
    return errors


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, case in enumerate(cases, start=1):
        location = f"case {index}"
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{location}: id must be a non-empty string")
            continue
        location = case_id
        if case_id in seen:
            errors.append(f"{location}: duplicate id")
        seen.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"{location}: prompt must be a non-empty string")
        if not isinstance(case.get("should_trigger"), bool):
            errors.append(f"{location}: should_trigger must be boolean")
            continue

        mode = case.get("expected_mode")
        level = case.get("expected_plan_level")
        if case["should_trigger"]:
            if mode not in VALID_MODES:
                errors.append(f"{location}: expected_mode must be a supported mode")
            if level not in VALID_LEVELS:
                errors.append(
                    f"{location}: expected_plan_level must be P0, P1, P2, or P3"
                )
        elif mode is not None or level is not None:
            errors.append(
                f"{location}: non-trigger cases cannot define mode or planning level"
            )
        errors.extend(
            validate_signal_map(case.get("required_signals"), f"{location}.required")
        )
        errors.extend(
            validate_signal_map(case.get("forbidden_signals"), f"{location}.forbidden")
        )
    return errors


def validate_results(
    results: list[dict[str, Any]], case_ids: set[str]
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    indexed: dict[str, dict[str, Any]] = {}
    for index, result in enumerate(results, start=1):
        location = f"result {index}"
        case_id = result.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{location}: case_id must be a non-empty string")
            continue
        if case_id not in case_ids:
            errors.append(f"{location}: unknown case_id {case_id}")
        if case_id in indexed:
            errors.append(f"{location}: duplicate case_id {case_id}")
        if not isinstance(result.get("triggered"), bool):
            errors.append(f"{location}: triggered must be boolean")
        if "response" in result and not isinstance(result["response"], str):
            errors.append(f"{location}: response must be a string")
        indexed[case_id] = result
    for missing in sorted(case_ids - indexed.keys()):
        errors.append(f"missing result for case_id {missing}")
    return indexed, errors


def matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def score_case(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    checks = 1
    passed = 0
    expected_trigger = case["should_trigger"]
    actual_trigger = result["triggered"]
    if expected_trigger == actual_trigger:
        passed += 1
    else:
        failures.append(
            f"trigger expected {expected_trigger} but recorded {actual_trigger}"
        )

    if expected_trigger and actual_trigger:
        response = result.get("response", "")
        mode = case["expected_mode"]
        level = case["expected_plan_level"]
        checks += 2
        if re.search(rf"\bMode:\s*{re.escape(mode)}\b", response, re.IGNORECASE):
            passed += 1
        else:
            failures.append(f"missing expected mode {mode}")
        if re.search(rf"\b{re.escape(level)}\b", response):
            passed += 1
        else:
            failures.append(f"missing expected planning level {level}")

        for label, patterns in case.get("required_signals", {}).items():
            checks += 1
            if matches_any(patterns, response):
                passed += 1
            else:
                failures.append(f"missing required signal: {label}")

        for label, patterns in case.get("forbidden_signals", {}).items():
            checks += 1
            if not matches_any(patterns, response):
                passed += 1
            else:
                failures.append(f"found prohibited signal: {label}")

    return {
        "case_id": case["id"],
        "passed_checks": passed,
        "total_checks": checks,
        "score": round(passed / checks, 6),
        "failures": failures,
    }


def score(cases: list[dict[str, Any]], results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    case_reports = [score_case(case, results[case["id"]]) for case in cases]
    passed = sum(report["passed_checks"] for report in case_reports)
    checks = sum(report["total_checks"] for report in case_reports)
    tp = fp = tn = fn = 0
    for case in cases:
        actual = results[case["id"]]["triggered"]
        expected = case["should_trigger"]
        if expected and actual:
            tp += 1
        elif expected and not actual:
            fn += 1
        elif not expected and actual:
            fp += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    return {
        "summary": {
            "cases": len(cases),
            "passed_checks": passed,
            "total_checks": checks,
            "score": round(passed / checks, 6),
            "trigger_precision": round(precision, 6),
            "trigger_recall": round(recall, 6),
            "trigger_confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        },
        "cases": case_reports,
    }


def main() -> int:
    args = parse_args()
    if not 0 <= args.min_score <= 1:
        print("error: --min-score must be between 0 and 1", file=sys.stderr)
        return 2
    try:
        cases = load_jsonl(args.cases, "cases")
        case_errors = validate_cases(cases)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if case_errors:
        print("case corpus validation failed:", file=sys.stderr)
        for error in case_errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    if args.emit_prompts:
        for case in cases:
            print(json.dumps({"case_id": case["id"], "prompt": case["prompt"]}))
        return 0

    if not args.results:
        summary = {
            "cases": len(cases),
            "positive": sum(case["should_trigger"] for case in cases),
            "negative": sum(not case["should_trigger"] for case in cases),
            "status": "valid",
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    try:
        raw_results = load_jsonl(args.results, "results")
        results, result_errors = validate_results(
            raw_results, {case["id"] for case in cases}
        )
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if result_errors:
        print("result validation failed:", file=sys.stderr)
        for error in result_errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    report = score(cases, results)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["summary"]["score"] >= args.min_score else 1


if __name__ == "__main__":
    raise SystemExit(main())
