#!/usr/bin/env python3
"""Evaluate ranked retrieval results from a JSONL dataset."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute recall, precision, reciprocal rank, and nDCG for JSONL "
            "retrieval results."
        )
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument(
        "--k", type=int, nargs="+", default=[1, 3, 5, 10], help="Rank cutoffs."
    )
    parser.add_argument(
        "--slice-field",
        default="query_class",
        help="Optional field used for sliced metrics.",
    )
    return parser.parse_args()


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"line {line_number}: invalid JSON: {error}") from error
            if not isinstance(case, dict):
                raise ValueError(f"line {line_number}: root must be an object")
            for field in ("relevant_ids", "retrieved_ids"):
                if not isinstance(case.get(field), list):
                    raise ValueError(f"line {line_number}: {field} must be a list")
            cases.append(case)
    if not cases:
        raise ValueError("dataset contains no cases")
    return cases


def metrics_at_k(case: dict[str, Any], k: int) -> dict[str, float]:
    relevant = set(map(str, case["relevant_ids"]))
    retrieved = list(map(str, case["retrieved_ids"]))[:k]
    unique_hits: set[str] = set()
    for item in retrieved:
        if item in relevant:
            unique_hits.add(item)
    recall = len(unique_hits) / len(relevant) if relevant else 1.0
    precision = len(unique_hits) / k

    reciprocal_rank = 0.0
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            reciprocal_rank = 1.0 / rank
            break

    ranked_hits: set[str] = set()
    dcg = 0.0
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant and item not in ranked_hits:
            dcg += 1.0 / math.log2(rank + 1)
            ranked_hits.add(item)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    ndcg = dcg / idcg if idcg else 1.0
    return {
        "recall": recall,
        "precision": precision,
        "mrr": reciprocal_rank,
        "ndcg": ndcg,
    }


def summarize(cases: Iterable[dict[str, Any]], cutoffs: list[int]) -> dict[str, Any]:
    case_list = list(cases)
    result: dict[str, Any] = {"cases": len(case_list), "metrics": {}}
    for k in cutoffs:
        values: dict[str, list[float]] = defaultdict(list)
        for case in case_list:
            for name, value in metrics_at_k(case, k).items():
                values[name].append(value)
        result["metrics"][str(k)] = {
            name: round(statistics.fmean(scores), 6)
            for name, scores in sorted(values.items())
        }
    return result


def main() -> int:
    args = parse_args()
    if any(k <= 0 for k in args.k):
        print("error: every k must be positive", file=sys.stderr)
        return 2
    try:
        cases = load_cases(args.dataset)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    cutoffs = sorted(set(args.k))
    report: dict[str, Any] = {"overall": summarize(cases, cutoffs)}
    slices: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        slices[str(case.get(args.slice_field, "unspecified"))].append(case)
    report["slices"] = {
        name: summarize(slice_cases, cutoffs)
        for name, slice_cases in sorted(slices.items())
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
