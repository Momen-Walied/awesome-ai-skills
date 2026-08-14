from __future__ import annotations

import importlib.util
import json
import math
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


retrieval = load_module(
    "evaluate_retrieval",
    ROOT / "skills" / "rag-production-engineer" / "scripts" / "evaluate_retrieval.py",
)
traces = load_module(
    "analyze_traces",
    ROOT / "skills" / "rag-production-engineer" / "scripts" / "analyze_traces.py",
)
rag_plan = load_module(
    "validate_rag_plan",
    ROOT / "skills" / "rag-production-engineer" / "scripts" / "validate_rag_plan.py",
)
plan_document = load_module(
    "validate_plan_document",
    ROOT
    / "skills"
    / "rag-production-engineer"
    / "scripts"
    / "validate_plan_document.py",
)
skill_evals = load_module("run_skill_evals", ROOT / "scripts" / "run_skill_evals.py")
eval_workspace = load_module(
    "prepare_eval_workspace", ROOT / "scripts" / "prepare_eval_workspace.py"
)
workspace_inspector = load_module(
    "inspect_workspace",
    ROOT / "skills" / "rag-production-engineer" / "scripts" / "inspect_workspace.py",
)


class RetrievalEvaluationTests(unittest.TestCase):
    def test_fixture_loads_and_slices(self) -> None:
        cases = retrieval.load_cases(FIXTURES / "retrieval-results.jsonl")
        report = retrieval.summarize(cases, [1, 3])
        self.assertEqual(report["cases"], 2)
        self.assertEqual(report["metrics"]["1"]["recall"], 0.25)

    def test_duplicate_results_do_not_inflate_metrics(self) -> None:
        case = {"relevant_ids": ["doc-a"], "retrieved_ids": ["doc-a", "doc-a"]}
        metrics = retrieval.metrics_at_k(case, 2)
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 1.0)
        self.assertEqual(metrics["ndcg"], 1.0)

    def test_non_object_case_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.jsonl"
            path.write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "root must be an object"):
                retrieval.load_cases(path)


class WorkspaceInspectionTests(unittest.TestCase):
    def test_detects_agent_workflow_and_test_signals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("Run tests.\n", encoding="utf-8")
            (root / "services" / "api").mkdir(parents=True)
            (root / "services" / "api" / "CLAUDE.md").write_text(
                "Use API conventions.\n", encoding="utf-8"
            )
            (root / "node_modules" / "dependency").mkdir(parents=True)
            (root / "node_modules" / "dependency" / "AGENTS.md").write_text(
                "Ignore dependency instructions.\n", encoding="utf-8"
            )
            (root / ".specify" / "memory").mkdir(parents=True)
            (root / ".agents" / "skills").mkdir(parents=True)
            (root / "tests").mkdir()
            (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

            report = workspace_inspector.inspect(root)

        self.assertEqual(
            report["instructions"], ["AGENTS.md", "services/api/CLAUDE.md"]
        )
        self.assertEqual(report["workflows"], {"spec-kit": [".specify"]})
        self.assertEqual(report["skill_roots"], [".agents/skills"])
        self.assertEqual(report["manifests"], ["pyproject.toml"])
        self.assertEqual(report["test_and_eval_roots"], ["tests"])


class TraceAnalysisTests(unittest.TestCase):
    def test_fixture_summary_includes_errors_cost_and_fallbacks(self) -> None:
        spans = traces.load_spans(FIXTURES / "traces.jsonl")
        report = traces.summarize(spans)
        self.assertEqual(report["count"], 3)
        self.assertAlmostEqual(report["error_rate"], 1 / 3, places=6)
        self.assertEqual(report["cost_usd"], 0.023)
        self.assertEqual(report["fallbacks"], {"cached-answer": 1})

    def test_invalid_numeric_values_are_rejected(self) -> None:
        invalid_values = (-1, True, math.inf)
        for value in invalid_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "traces.jsonl"
                path.write_text(
                    json.dumps({"name": "retrieve", "duration_ms": value}) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "finite and non-negative"):
                    traces.load_spans(path)

    def test_non_numeric_cost_is_rejected_during_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "traces.jsonl"
            path.write_text(
                '{"name":"generate","duration_ms":10,"cost_usd":"unknown"}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "cost_usd"):
                traces.load_spans(path)


class PlanValidationTests(unittest.TestCase):
    def test_machine_readable_plan_fixture_is_valid(self) -> None:
        plan = json.loads((FIXTURES / "rag-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(rag_plan.validate(plan), [])

    def test_machine_readable_plan_reports_missing_sections(self) -> None:
        errors = rag_plan.validate({"use_case": {"status": "unknown"}})
        self.assertIn("missing section: workload", errors)

    def test_approved_p2_document_is_valid(self) -> None:
        text = (FIXTURES / "p2-plan.md").read_text(encoding="utf-8")
        self.assertEqual(plan_document.validate(text, "P2"), [])

    def test_p3_document_requires_sequence_diagram(self) -> None:
        text = (FIXTURES / "p2-plan.md").read_text(encoding="utf-8")
        errors = plan_document.validate(text, "P3")
        self.assertTrue(any("sequence diagram" in error for error in errors))

    def test_p3_document_requires_numerical_budgets(self) -> None:
        text = (FIXTURES / "p2-plan.md").read_text(encoding="utf-8")
        text += """

```mermaid
sequenceDiagram
    participant API
    participant Index
    API->>Index: Authorized query
```
"""
        errors = plan_document.validate(text, "P3")
        self.assertTrue(any("Capacity, latency, and cost budgets" in error for error in errors))

    def test_p3_document_accepts_labeled_recomputable_budgets(self) -> None:
        text = (FIXTURES / "p2-plan.md").read_text(encoding="utf-8")
        text = text.replace("**Status:** APPROVED", "**Status:** AWAITING_DECISIONS")
        text = text.replace(
            "## Operability",
            """## Capacity, latency, and cost budgets

PROPOSED: 100 QPS. Cost formula: monthly USD = queries per second * duty cycle
* unit cost; unit cost is UNKNOWN.

| Stage | Budget p95 | Notes |
| --- | --- | --- |
| Authorized retrieval | 800 milliseconds | Critical path |
| Headroom | 200 milliseconds | Queueing and variance |
| Total | 1,000 milliseconds | Recomputed total |

## Operability""",
        )
        text = text.replace(
            "## Risks and decisions",
            """```mermaid
sequenceDiagram
    participant API
    participant Index
    API->>Index: Authorized query
```

## Risks and decisions

| Decision | Recommendation | Alternatives | Impact |
| --- | --- | --- | --- |
| Cost ceiling | Use the approved product ceiling | Reduce scope | Controls rollout |
""",
        )
        text = text.replace(
            "Result: PASS and READY for implementation.",
            "Result: AWAITING_DECISIONS pending the cost ceiling.",
        )
        self.assertEqual(plan_document.validate(text, "P3"), [])

    def test_plan_status_must_match_awaiting_decisions_audit(self) -> None:
        text = (FIXTURES / "p2-plan.md").read_text(encoding="utf-8")
        text = text.replace(
            "Result: PASS and READY for implementation.",
            "Result: AWAITING_DECISIONS pending a policy decision.",
        )
        errors = plan_document.validate(text, "P2")
        self.assertTrue(any("Status must be AWAITING_DECISIONS" in error for error in errors))

    def test_audit_result_ignores_future_status_mentions_in_prose(self) -> None:
        body = """
**Result:** AWAITING_DECISIONS

Resolve the owner decision before moving the plan to READY.
"""
        self.assertEqual(plan_document.audit_result(body), "AWAITING_DECISIONS")

    def test_p3_latency_budget_rejects_bad_total_and_parallel_rows(self) -> None:
        body = """
| Stage | Budget p95 | Notes |
| --- | --- | --- |
| Dense | 250 ms | Concurrent with lexical |
| Lexical | 100 ms | Concurrent with dense |
| Headroom | 130 ms | Variance |
| Total | 470 ms | Claimed total |
"""
        errors = plan_document.validate_latency_budget(body)
        self.assertTrue(any("declared 470 ms, calculated 480 ms" in error for error in errors))
        self.assertTrue(any("combine concurrent branches" in error for error in errors))

    def test_p3_latency_budget_requires_positive_headroom(self) -> None:
        body = """
| Stage | Budget p95 | Notes |
| --- | --- | --- |
| Retrieval | 300 ms | Critical path |
| Total | 300 ms | Recomputed total |
"""
        errors = plan_document.validate_latency_budget(body)
        self.assertIn("P3 latency budget must reserve positive headroom", errors)

    def test_p3_latency_budget_allows_one_combined_parallel_stage(self) -> None:
        body = """
| Stage | Budget p95 | Notes |
| --- | --- | --- |
| Hybrid retrieval | 300 ms | Dense and lexical run concurrently; slower branch wins |
| Headroom | 100 ms | Variance |
| Total | 400 ms | Recomputed total |
"""
        self.assertEqual(plan_document.validate_latency_budget(body), [])

    def test_p3_latency_budget_uses_units_declared_in_header(self) -> None:
        body = """
| Stage | Budget (ms) | Notes |
| --- | --- | --- |
| Retrieval | 300 | Measured path |
| Headroom | 100 | Variance |
| Total | 400 | Recomputed total |
"""
        self.assertEqual(plan_document.validate_latency_budget(body), [])

    def test_p3_latency_budget_accepts_symbolic_unknowns(self) -> None:
        body = """
| Stage | Budget p95 (ms) | Evidence / formula |
| --- | --- | --- |
| Retrieval | UNKNOWN | Measure at production load shape |
| Generation | UNKNOWN | Measure with the selected model |
| Headroom | PROPOSED: 20% of measured stage subtotal | headroom = 0.20 * stage_subtotal |
| Total | UNKNOWN | total = stage_subtotal + headroom |
"""
        self.assertEqual(plan_document.validate_latency_budget(body), [])

    def test_p3_latency_budget_rejects_multiple_percentiles_and_placeholders(self) -> None:
        body = """
| Stage | Budget p50 (ms) | Budget p95 (ms) | Notes |
| --- | --- | --- | --- |
| Retrieval | UNKNOWN | UNKNOWN | Measure later |
| Headroom | 50 ms | 50 ms | PROPOSED placeholder |
| Total | 50 ms | UNKNOWN | Claimed total |
"""
        errors = plan_document.validate_latency_budget(body)
        self.assertTrue(any("one critical percentile" in error for error in errors))
        self.assertTrue(any("numeric total" in error for error in errors))
        self.assertTrue(any("numeric headroom placeholder" in error for error in errors))

    def test_p3_latency_budget_validates_every_path_table(self) -> None:
        body = """
### Primary path

| Stage | Budget (ms) |
| --- | --- |
| Retrieval | 300 |
| Headroom | 100 |
| Total | 400 |

### Fallback path

| Stage | Budget (ms) |
| --- | --- |
| Failure detection | 100 |
| Fallback retrieval | 200 |
| Headroom | 100 |
| Total | 450 |
"""
        errors = plan_document.validate_latency_budget(body)
        self.assertTrue(any("Fallback path" in error for error in errors))
        self.assertTrue(any("declared 450 ms, calculated 400 ms" in error for error in errors))

    def test_p3_latency_budget_rejects_multiple_path_totals(self) -> None:
        body = """
| Stage | Budget p95 | Notes |
| --- | --- | --- |
| Retrieval | 300 ms | Primary path |
| Primary total | 300 ms | Primary path |
| Fallback retrieval | 200 ms | Fallback path |
| Fallback total | 500 ms | Claimed fallback path |
| Headroom | 100 ms | Variance |
"""
        errors = plan_document.validate_latency_budget(body)
        self.assertTrue(any("separate table" in error for error in errors))

    def test_p3_migration_contract_fixture_is_valid(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        self.assertEqual(plan_document.validate(text, "P3"), [])

    def test_p3_migration_requires_dedicated_contract_sections(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        text = text.replace("## Compatibility matrix", "## Provider notes")
        errors = plan_document.validate(text, "P3")
        self.assertIn("missing MIGRATE section: Compatibility matrix", errors)

    def test_p3_migration_rejects_missing_watermark_and_score_thresholds(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        text = text.replace("watermark", "position")
        text = text.replace("threshold consumers", "downstream consumers")
        errors = plan_document.validate(text, "P3")
        self.assertTrue(any("change-stream watermark" in error for error in errors))
        self.assertTrue(any("score threshold consumers" in error for error in errors))

    def test_p3_migration_requires_vendor_specific_authorization_adapters(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        correctness = plan_document.heading_body(text, "Migration correctness")
        self.assertIsNotNone(correctness)
        errors = plan_document.validate_migration_contracts(
            text.replace("Vendor\nA ACL adapter", "shared ACL adapter")
        )
        self.assertTrue(any("Vendor A authorization adapter" in error for error in errors))

    def test_p3_migration_requires_migration_specific_costs(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        text = text.replace("One-time backfill cost", "One-time copy expense")
        text = text.replace("Incremental dual-run cost", "Incremental overlap expense")
        errors = plan_document.validate(text, "P3")
        self.assertTrue(any("one-time backfill cost" in error for error in errors))
        self.assertTrue(any("incremental dual-run cost" in error for error in errors))

    def test_p3_migration_rejects_dimensionally_invalid_costs(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        text = text.replace(
            "billable chunks / billing unit chunks * price per billing unit",
            "chunks / throughput chunks/s * price per 1,000 chunks",
        )
        text = text.replace(
            "Vendor A\nstorage and writes + Vendor B storage and writes",
            "daily mutations * 2 (Vendor A + Vendor B writes)",
        )
        errors = plan_document.validate(text, "P3")
        self.assertTrue(any("dimensionally invalid" in error for error in errors))
        self.assertTrue(any("price Vendor A and Vendor B separately" in error for error in errors))

    def test_p3_budget_rejects_invented_peak_ratio(self) -> None:
        body = "Average QPS is UNKNOWN; use peak / 3 as an ESTIMATED duty cycle."
        errors = plan_document.validate_budget_assumptions(body)
        self.assertTrue(any("invented peak ratio" in error for error in errors))

    def test_p3_migration_sequence_requires_cutover_and_retirement(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        text = text.replace("Cutover", "Promote")
        text = text.replace("Retire", "Remove")
        errors = plan_document.validate(text, "P3")
        self.assertTrue(any("sequence diagram must show cutover" in error for error in errors))
        self.assertTrue(any("sequence diagram must show retirement" in error for error in errors))

    def test_p3_rollout_windows_require_evidence_labels(self) -> None:
        body = "Canary a tenant cohort and monitor for 24-48 h."
        errors = plan_document.validate_rollout_windows(body)
        self.assertTrue(any("evidence label" in error for error in errors))
        self.assertEqual(
            plan_document.validate_rollout_windows("PROPOSED: Canary for 24 h."),
            [],
        )

    def test_open_decisions_require_matching_status_and_decision_table(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        text = text.replace("**Status:** AWAITING_DECISIONS", "**Status:** PROPOSED")
        text = text.replace("**Result:** AWAITING_DECISIONS", "**Result:** FAIL")
        errors = plan_document.validate(text, "P3")
        self.assertTrue(any("owner input" in error for error in errors))

    def test_owner_decision_blocker_wording_requires_awaiting_decisions(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        text = text.replace("**Status:** AWAITING_DECISIONS", "**Status:** PROPOSED")
        text = text.replace(
            "**Result:** AWAITING_DECISIONS",
            "**Result:** FAIL (semantic audit blocked by owner decisions)",
        )
        errors = plan_document.validate(text, "P3")
        self.assertTrue(any("owner input" in error for error in errors))

    def test_ready_plan_rejects_unknown_owner_and_material_inputs(self) -> None:
        text = """
# Migration plan

**Status:** READY
**Owners:** UNKNOWN

## Evidence and assumptions

| Input | Label | Value |
| --- | --- | --- |
| Authorization model | UNKNOWN | Confirm before implementation |

## Plan audit

**Result:** READY
"""
        errors = plan_document.validate_ready_state(text, "READY", "READY")
        self.assertTrue(any("named accountable owner" in error for error in errors))
        self.assertTrue(any("material UNKNOWN" in error for error in errors))

    def test_ready_plan_rejects_self_approved_assumptions_package(self) -> None:
        text = """
# Migration plan

**Status:** READY
**Owners:** Search platform

## Planning assumptions package

To move to READY without owner input, the database is assumed true and must be
validated before implementation.

## Plan audit

**Result:** READY
"""
        errors = plan_document.validate_ready_state(text, "READY", "READY")
        self.assertTrue(any("assumptions package" in error for error in errors))
        self.assertTrue(any("contradicts unresolved" in error for error in errors))

    def test_awaiting_decisions_requires_recommendations_and_impacts(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        text = text.replace("| Decision | Recommendation | Alternatives | Impact |", "Questions:")
        errors = plan_document.validate(text, "P3")
        self.assertTrue(any("decision table" in error for error in errors))

    def test_security_contract_rejects_fail_open_and_stale_failover(self) -> None:
        text = """
Unauthorized result: fail open to deny-by-default.
Demote Vendor A to read-only failover.
"""
        errors = plan_document.validate_security_language(text)
        self.assertTrue(any("fail closed" in error for error in errors))
        self.assertTrue(any("cannot serve as failover" in error for error in errors))

    def test_no_cdc_zero_downtime_requires_atomic_capture_and_barrier(self) -> None:
        text = """
Zero-downtime migration is required, but the source has no CDC or mutation log.
An IndexRouter writes to an independent journal after each source mutation.
Uncontrolled admin writers make the zero-loss guarantee unprovable.
"""
        errors = plan_document.validate_zero_downtime_without_cdc(text)
        self.assertTrue(any("atomic source-mutation capture" in error for error in errors))
        self.assertTrue(any("before the bootstrap snapshot" in error for error in errors))

    def test_no_cdc_zero_downtime_accepts_transactional_capture_boundary(self) -> None:
        text = """
Zero-downtime migration is required, but the source has no CDC or mutation log.
Commit each source mutation and transactional outbox event in the same transaction.
Activate outbox capture before the bootstrap snapshot, then replay from its barrier.
Any admin or background writer that bypasses capture blocks cutover unless the owner
approves a bounded write freeze.
"""
        self.assertEqual(plan_document.validate_zero_downtime_without_cdc(text), [])

    def test_migration_fallback_requires_ordered_mutations_and_two_freshness_gates(self) -> None:
        text = """
## Migration correctness

Old-Vendor remains the fallback, but it receives only nightly snapshots.
Fallback is acceptable when the query tolerates stale data.

## Rollout and rollback

Roll back to Old-Vendor when Vendor B fails.
"""
        errors = plan_document.validate_migration_fallback(text)
        self.assertTrue(any("ordered content" in error for error in errors))
        self.assertTrue(any("separate data and policy" in error for error in errors))
        self.assertTrue(any("query sensitivity" in error for error in errors))

    def test_migration_fallback_accepts_fresh_ordered_old_vendor(self) -> None:
        text = """
## Migration correctness

Vendor A remains fallback only while it receives ordered content updates,
deletes, and permission revocations. Fallback eligibility requires a current
data freshness watermark and a separate policy freshness watermark.

## Rollout and rollback

Roll back to Vendor A only while both freshness gates pass; otherwise fail closed.
"""
        self.assertEqual(plan_document.validate_migration_fallback(text), [])

    def test_backfill_formula_can_follow_its_label_in_a_code_block(self) -> None:
        text = (FIXTURES / "p3-migration-plan.md").read_text(encoding="utf-8")
        text = text.replace(
            "UNKNOWN: effective chunks per second and production QPS. Migration duration =\n"
            "remaining chunks / effective chunks per second. One-time backfill cost =\n"
            "billable chunks / billing unit chunks * price per billing unit + source reads +\n"
            "egress + optional embedding.",
            """UNKNOWN: effective chunks per second and production QPS.

Backfill cost:

```text
backfill_duration = total chunks / effective chunks per second
backfill_write_cost = billable chunks / billing unit chunks * price per billing unit
```""",
        )
        self.assertEqual(plan_document.validate(text, "P3"), [])


class SkillEvaluationTests(unittest.TestCase):
    def test_repository_corpus_is_valid_and_balanced(self) -> None:
        cases = skill_evals.load_jsonl(ROOT / "evals" / "cases.jsonl", "cases")
        self.assertEqual(skill_evals.validate_cases(cases), [])
        self.assertGreaterEqual(sum(case["should_trigger"] for case in cases), 8)
        self.assertGreaterEqual(sum(not case["should_trigger"] for case in cases), 4)

    def test_matching_result_passes_all_checks(self) -> None:
        case = {
            "id": "migration",
            "prompt": "Migrate a RAG vendor.",
            "should_trigger": True,
            "expected_mode": "MIGRATE",
            "expected_plan_level": "P3",
            "required_signals": {"rollback": ["rollback"]},
            "forbidden_signals": {"false-completion": ["already deployed"]},
        }
        result = {
            "case_id": "migration",
            "triggered": True,
            "response": "Mode: MIGRATE. Planning level P3. Define rollback first.",
        }
        report = skill_evals.score_case(case, result)
        self.assertEqual(report["score"], 1.0)
        self.assertEqual(report["failures"], [])

    def test_manual_review_checks_are_validated_and_reported(self) -> None:
        case = {
            "id": "capacity",
            "prompt": "Design capacity.",
            "should_trigger": True,
            "expected_mode": "DESIGN",
            "expected_plan_level": "P3",
            "manual_review": ["Recompute cost with explicit units."],
        }
        self.assertEqual(skill_evals.validate_cases([case]), [])
        result = {
            "case_id": "capacity",
            "triggered": True,
            "response": "Mode: DESIGN. Planning level P3.",
        }
        report = skill_evals.score_case(case, result)
        self.assertEqual(report["manual_review"], case["manual_review"])

    def test_invalid_manual_review_check_is_rejected(self) -> None:
        case = {
            "id": "capacity",
            "prompt": "Design capacity.",
            "should_trigger": True,
            "expected_mode": "DESIGN",
            "expected_plan_level": "P3",
            "manual_review": [""],
        }
        errors = skill_evals.validate_cases([case])
        self.assertTrue(any("manual_review" in error for error in errors))

    def test_missing_result_is_reported(self) -> None:
        indexed, errors = skill_evals.validate_results([], {"required-case"})
        self.assertEqual(indexed, {})
        self.assertIn("missing result for case_id required-case", errors)

    def test_cli_returns_distinct_status_for_pass_and_failure(self) -> None:
        case = {
            "id": "design",
            "prompt": "Design a production RAG system.",
            "should_trigger": True,
            "expected_mode": "DESIGN",
            "expected_plan_level": "P2",
            "required_signals": {"evaluation": ["evaluation"]},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case_path = root / "cases.jsonl"
            pass_path = root / "pass.jsonl"
            fail_path = root / "fail.jsonl"
            case_path.write_text(json.dumps(case) + "\n", encoding="utf-8")
            pass_path.write_text(
                json.dumps(
                    {
                        "case_id": "design",
                        "triggered": True,
                        "response": "Mode: DESIGN. Use a P2 evaluation plan.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            fail_path.write_text(
                json.dumps(
                    {"case_id": "design", "triggered": False, "response": ""}
                )
                + "\n",
                encoding="utf-8",
            )
            command = [
                "python3",
                str(ROOT / "scripts" / "run_skill_evals.py"),
                str(case_path),
                "--results",
            ]
            passing = subprocess.run(
                command + [str(pass_path)], capture_output=True, text=True, check=False
            )
            failing = subprocess.run(
                command + [str(fail_path)], capture_output=True, text=True, check=False
            )
        self.assertEqual(passing.returncode, 0, passing.stderr)
        self.assertEqual(failing.returncode, 1, failing.stderr)


class RepositoryContractTests(unittest.TestCase):
    def test_ci_cache_tracks_the_development_requirements(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("cache-dependency-path: requirements-dev.txt", workflow)

    def test_ci_actions_use_node_24_runtimes(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )
        for action in ("checkout", "setup-python", "setup-node"):
            self.assertIn(f"actions/{action}@v6", workflow)
        self.assertIn("node-version: 24", workflow)

    def test_skill_stays_within_progressive_disclosure_limit(self) -> None:
        skill = ROOT / "skills" / "rag-production-engineer" / "SKILL.md"
        self.assertLessEqual(len(skill.read_text(encoding="utf-8").splitlines()), 500)

    def test_large_scale_greenfield_case_requires_p3(self) -> None:
        cases = skill_evals.load_jsonl(ROOT / "evals" / "cases.jsonl", "cases")
        case = next(
            case for case in cases if case["id"] == "greenfield-production-design"
        )
        self.assertEqual(case["expected_plan_level"], "P3")

    def test_adversarial_migration_cases_cover_distinct_failure_modes(self) -> None:
        cases = skill_evals.load_jsonl(ROOT / "evals" / "cases.jsonl", "cases")
        indexed = {case["id"]: case for case in cases}
        expected = {
            "migration-incompatible-embeddings": "MIGRATE",
            "migration-without-cdc": "MIGRATE",
            "migration-acl-capability-gap": "MIGRATE",
            "stale-fallback-incident": "OPERATE",
            "planning-owner-decision-pressure": "MIGRATE",
        }
        for case_id, mode in expected.items():
            with self.subTest(case_id=case_id):
                self.assertEqual(indexed[case_id]["expected_mode"], mode)
                self.assertTrue(indexed[case_id]["manual_review"])

    def test_missing_target_case_forbids_substitute_artifacts(self) -> None:
        cases = skill_evals.load_jsonl(ROOT / "evals" / "cases.jsonl", "cases")
        case = next(
            case for case in cases if case["id"] == "missing-bounded-change-target"
        )
        self.assertEqual(case["expected_mode"], "IMPLEMENT")
        self.assertIn("substitute-artifacts", case["forbidden_signals"])
        self.assertTrue(case["manual_review"])

    def test_skill_enforces_numeric_and_workspace_integrity(self) -> None:
        text = (
            ROOT / "skills" / "rag-production-engineer" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("RECOMPUTATION CHECK", text)
        self.assertIn("NO SUBSTITUTE FILES", text)
        self.assertIn("NO ZERO-DOWNTIME MIGRATION CLAIM", text)
        self.assertIn("NO HOT FALLBACK OR ROLLBACK CLAIM", text)
        self.assertIn("Do not convert unavailable owner decisions", text)
        self.assertIn("workspace mismatch", text)
        self.assertIn("Do not create substitute application artifacts", text)
        self.assertIn("Any requested repository mutation starts at `P1`", text)
        self.assertIn("Capacity, latency, and cost budgets", text)
        self.assertIn("structural validator pass means only", text)
        self.assertIn("avoid duplicating artifacts", text)

    def test_skill_description_pushes_small_rag_config_triggers(self) -> None:
        text = (
            ROOT / "skills" / "rag-production-engineer" / "SKILL.md"
        ).read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        self.assertIn("implement", frontmatter)
        self.assertIn("chunking", frontmatter)
        self.assertIn("Analyze existing", frontmatter)
        self.assertIn("Spec Kit", frontmatter)
        self.assertIn("MCP tools", frontmatter)

    def test_any_repository_mutation_starts_at_p1(self) -> None:
        text = (
            ROOT / "skills" / "rag-production-engineer" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("read-only inspection with no repository mutation", text)
        self.assertIn("Any requested repository mutation starts at `P1`", text)
        self.assertIn("config plus focused-test work", text)
        self.assertIn("Do not delegate", text)
        self.assertIn("additional speculative searches add latency", text)

    def test_skill_defines_top_down_execution_and_host_composition(self) -> None:
        skill_root = ROOT / "skills" / "rag-production-engineer"
        execution = (skill_root / "references" / "execution-protocol.md").read_text(
            encoding="utf-8"
        )
        interop = (
            skill_root / "references" / "agent-interoperability.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Build a top-down system model", execution)
        self.assertIn("Implement a vertical slice", execution)
        self.assertIn("Do not stop after producing a plan", execution)
        self.assertIn("Compose instead of competing", interop)
        self.assertIn("Spec Kit", interop)
        self.assertIn("Use tools by capability", interop)
        self.assertIn("unknown agent", interop)

        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("locate this skill's installed directory", skill)
        self.assertRegex(skill, r"Do\s+not resolve that script relative")

        evaluation = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Avoid benchmark overfitting", evaluation)
        self.assertIn("Workspace fixtures", evaluation)
        self.assertIn("Cross-agent matrix", evaluation)

        results = json.loads(
            (ROOT / "evals" / "records" / "v0.2.0-cross-agent.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(results["case_id"], "top-down-rag-implementation")
        self.assertEqual(len(results["runs"]), 2)
        self.assertTrue(all(run["verification"]["passed"] for run in results["runs"]))

        current_results = json.loads(
            (ROOT / "evals" / "records" / "v0.3.0-cross-agent.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(current_results["runs"]), 4)
        self.assertEqual(current_results["summary"]["extended_audit_failures"], 1)
        self.assertEqual(
            current_results["summary"][
                "core_instruction_changes_from_model_specific_failures"
            ],
            0,
        )

        runtime_results = json.loads(
            (ROOT / "evals" / "records" / "v0.4.0-cross-agent.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(runtime_results["runs"]), 6)
        self.assertEqual(runtime_results["summary"]["automatic_skill_triggers"], 6)
        self.assertEqual(runtime_results["summary"]["visible_suites_passed"], 6)
        self.assertEqual(runtime_results["summary"]["extended_audit_failures"], 3)
        self.assertEqual(
            runtime_results["summary"][
                "core_instruction_changes_from_model_specific_failures"
            ],
            0,
        )

    def test_skill_guides_the_host_instead_of_claiming_execution(self) -> None:
        skill_root = ROOT / "skills" / "rag-production-engineer"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        interop = (
            skill_root / "references" / "agent-interoperability.md"
        ).read_text(encoding="utf-8")
        self.assertIn("This skill guides the host agent", skill)
        self.assertIn("The host agent remains the executor", interop)
        self.assertIn("Bundled scripts support deterministic", interop)

    def test_domain_references_include_implementation_guidance(self) -> None:
        references = ROOT / "skills" / "rag-production-engineer" / "references"
        expected_sections = {
            "ingestion-indexing.md": "Guide an ingestion implementation",
            "evaluation.md": "Guide an evaluation implementation",
            "observability.md": "Guide instrumentation changes",
            "reliability-security.md": "Guide a policy-sensitive fallback change",
            "retrieval-generation.md": "Guide a retrieval implementation",
            "scale-performance.md": "Guide a performance implementation",
            "vendor-integration.md": "Guide an integration implementation",
        }
        for filename, section in expected_sections.items():
            with self.subTest(filename=filename):
                text = (references / filename).read_text(encoding="utf-8")
                self.assertIn(section, text)

        self.assertIn(
            "Guide deadline propagation",
            (references / "scale-performance.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Guide citation validation changes",
            (references / "retrieval-generation.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Guide tool-call security changes",
            (references / "reliability-security.md").read_text(encoding="utf-8"),
        )

    def test_skill_relative_file_references_exist(self) -> None:
        skill_root = ROOT / "skills" / "rag-production-engineer"
        text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        references = re.findall(r"(?:\(|`)\s*((?:assets|references|scripts)/[^)`\s]+)", text)
        self.assertGreater(len(references), 10)
        missing = [path for path in references if not (skill_root / path).exists()]
        self.assertEqual(missing, [])

    def test_json_assets_are_valid(self) -> None:
        asset_root = ROOT / "skills" / "rag-production-engineer" / "assets"
        for path in asset_root.glob("*.json"):
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(value, dict)


class EvaluationWorkspaceTests(unittest.TestCase):
    def test_adversarial_migration_fixtures_are_preparable(self) -> None:
        case_ids = (
            "migration-incompatible-embeddings",
            "migration-without-cdc",
            "migration-acl-capability-gap",
            "stale-fallback-incident",
            "planning-owner-decision-pressure",
        )
        for case_id in case_ids:
            with self.subTest(case_id=case_id), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "workspace"
                result = eval_workspace.prepare_workspace(case_id, output)
                status = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=output,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(status.stdout, "")
                self.assertTrue((output / "CURRENT_STATE.txt").is_file())
                self.assertEqual(result["case_id"], case_id)

    def test_vendor_migration_fixture_preserves_blocking_unknowns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "workspace"
            result = eval_workspace.prepare_workspace(
                "multi-vendor-migration", output
            )
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=output,
                capture_output=True,
                text=True,
                check=True,
            )
            context = (output / "CURRENT_STATE.txt").read_text(encoding="utf-8")
            self.assertEqual(status.stdout, "")
            self.assertIn("80 million chunks", context)
            self.assertIn("Unknown inputs", context)
            self.assertIn("Vendor B sustained write throughput", context)
            self.assertIn("docs/plans", result["verify"])

    def test_greenfield_design_fixture_has_no_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "workspace"
            result = eval_workspace.prepare_workspace(
                "greenfield-production-design", output
            )
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=output,
                capture_output=True,
                text=True,
                check=True,
            )
            context = (output / "PROJECT.txt").read_text(encoding="utf-8")
            self.assertEqual(status.stdout, "")
            self.assertIn("No application", context)
            self.assertFalse((output / "app").exists())
            self.assertIn("docs/plans", result["verify"])

    def test_bounded_change_fixture_is_runnable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "workspace"
            result = eval_workspace.prepare_workspace(
                "bounded-chunk-config", output
            )
            self.assertEqual(result["case_id"], "bounded-chunk-config")
            self.assertIn("from 40 to 60", result["prompt"])
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=output,
                capture_output=True,
                text=True,
                check=True,
            )
            baseline = subprocess.run(
                ["git", "show", "HEAD:app/config.py"],
                cwd=output,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(status.stdout, "")
            self.assertIn("CHUNK_OVERLAP = 40", baseline.stdout)
            completed = subprocess.run(
                ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
                cwd=output,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_top_down_implementation_fixture_has_executable_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "workspace"
            result = eval_workspace.prepare_workspace(
                "top-down-rag-implementation", output
            )
            baseline = subprocess.run(
                ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
                cwd=output,
                capture_output=True,
                text=True,
                check=False,
            )
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=output,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(status.stdout, "")
            self.assertNotEqual(baseline.returncode, 0)
            self.assertIn("test_exact_sku_prefers", baseline.stderr)
            self.assertTrue((output / ".specify" / "memory" / "constitution.md").is_file())
            self.assertIn("unittest", result["verify"])
            self.assertIn("Do not stop after planning", result["prompt"])

    def test_ingestion_and_fallback_fixtures_have_bounded_failures(self) -> None:
        cases = {
            "ingestion-replay-revocation": (3, "test_revocation_removes_document"),
            "stale-policy-fallback": (1, "test_stale_policy_fallback_is_blocked"),
        }
        for case_id, (failure_count, expected_test) in cases.items():
            with self.subTest(case_id=case_id), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "workspace"
                result = eval_workspace.prepare_workspace(case_id, output)
                baseline = subprocess.run(
                    ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
                    cwd=output,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                status = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=output,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(status.stdout, "")
                self.assertNotEqual(baseline.returncode, 0)
                self.assertEqual(baseline.stderr.count("... FAIL"), failure_count)
                self.assertIn(expected_test, baseline.stderr)
                self.assertIn("unittest", result["verify"])
                self.assertTrue((output / ".specify" / "memory").is_dir())

    def test_runtime_safety_fixtures_have_bounded_failures(self) -> None:
        cases = {
            "deadline-budget-propagation": (2, "test_healthy_path_receives"),
            "claim-citation-validation": (2, "test_valid_but_unrelated"),
            "retrieved-tool-injection": (3, "test_allowlisted_tool_from"),
        }
        for case_id, (failure_count, expected_test) in cases.items():
            with self.subTest(case_id=case_id), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "workspace"
                result = eval_workspace.prepare_workspace(case_id, output)
                baseline = subprocess.run(
                    ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
                    cwd=output,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                status = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=output,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(status.stdout, "")
                self.assertNotEqual(baseline.returncode, 0)
                self.assertEqual(baseline.stderr.count("... FAIL"), failure_count)
                self.assertIn(expected_test, baseline.stderr)
                self.assertIn("unittest", result["verify"])
                self.assertTrue((output / ".specify" / "memory").is_dir())

    def test_workspace_setup_rejects_nonempty_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "existing.txt").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not empty"):
                eval_workspace.prepare_workspace("bounded-chunk-config", output)

    def test_missing_target_fixture_is_plan_only_and_clean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "workspace"
            result = eval_workspace.prepare_workspace(
                "missing-bounded-change-target", output
            )
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=output,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(status.stdout, "")
            self.assertFalse((output / "app").exists())
            self.assertFalse((output / "tests").exists())
            self.assertEqual(result["verify"], "git status --short")
            self.assertNotIn("do not scaffold", result["prompt"].lower())


if __name__ == "__main__":
    unittest.main()
