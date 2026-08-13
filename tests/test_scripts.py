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
        self.assertIn("workspace mismatch", text)
        self.assertIn("Do not create substitute application artifacts", text)
        self.assertIn("Planning level: P1", text)

    def test_skill_description_pushes_small_rag_config_triggers(self) -> None:
        text = (
            ROOT / "skills" / "rag-production-engineer" / "SKILL.md"
        ).read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        self.assertIn("Always use this skill", frontmatter)
        self.assertIn("small config", frontmatter)
        self.assertIn("chunk overlap", frontmatter)
        self.assertIn("before\n  repository exploration", frontmatter)

    def test_any_repository_mutation_starts_at_p1(self) -> None:
        text = (
            ROOT / "skills" / "rag-production-engineer" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("read-only inspection with no repository mutation", text)
        self.assertIn("Any requested repository mutation starts at `P1`", text)
        self.assertIn("config plus focused-test work", text)

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
