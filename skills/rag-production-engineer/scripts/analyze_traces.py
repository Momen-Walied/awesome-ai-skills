#!/usr/bin/env python3
"""Summarize latency, errors, cost, and fallbacks from JSONL spans."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", type=Path)
    return parser.parse_args()


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[rank]


def load_spans(path: Path) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                span = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"line {line_number}: invalid JSON: {error}") from error
            if not isinstance(span, dict):
                raise ValueError(f"line {line_number}: root must be an object")
            if not isinstance(span.get("name"), str):
                raise ValueError(f"line {line_number}: name must be a string")
            duration = span.get("duration_ms")
            if (
                isinstance(duration, bool)
                or not isinstance(duration, (int, float))
                or not math.isfinite(duration)
                or duration < 0
            ):
                raise ValueError(
                    f"line {line_number}: duration_ms must be finite and non-negative"
                )
            cost = span.get("cost_usd", 0.0)
            if (
                isinstance(cost, bool)
                or not isinstance(cost, (int, float))
                or not math.isfinite(cost)
                or cost < 0
            ):
                raise ValueError(
                    f"line {line_number}: cost_usd must be finite and non-negative"
                )
            if span.get("fallback") is not None and not isinstance(
                span["fallback"], str
            ):
                raise ValueError(f"line {line_number}: fallback must be a string")
            spans.append(span)
    if not spans:
        raise ValueError("trace export contains no spans")
    return spans


def summarize(spans: Iterable[dict[str, Any]]) -> dict[str, Any]:
    span_list = list(spans)
    durations = [float(span["duration_ms"]) for span in span_list]
    errors = sum(
        str(span.get("status", "ok")).lower() not in {"ok", "success", "unset"}
        for span in span_list
    )
    costs = [float(span.get("cost_usd", 0.0)) for span in span_list]
    fallbacks = Counter(
        str(span["fallback"]) for span in span_list if span.get("fallback")
    )
    return {
        "count": len(span_list),
        "error_rate": round(errors / len(span_list), 6),
        "latency_ms": {
            "p50": round(percentile(durations, 0.50), 3),
            "p95": round(percentile(durations, 0.95), 3),
            "p99": round(percentile(durations, 0.99), 3),
            "max": round(max(durations), 3),
        },
        "cost_usd": round(sum(costs), 6),
        "fallbacks": dict(sorted(fallbacks.items())),
    }


def main() -> int:
    args = parse_args()
    try:
        spans = load_spans(args.traces)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for span in spans:
        grouped[span["name"]].append(span)
    report = {
        "overall": summarize(spans),
        "spans": {name: summarize(items) for name, items in sorted(grouped.items())},
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
