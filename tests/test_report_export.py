#!/usr/bin/env python3
"""CSV export safety and completeness for the reporting module.

Two defects, both live on every real run:

1. CSV formula injection. `ideas.csv` (and, defensively, every other CSV this
   module writes) put model-generated text straight into a cell. A response to
   an arbitrary user question that happens to start with "=", "+", "-" or "@"
   is not text to Excel or LibreOffice — it is a formula, and it runs the
   moment the export is opened.

2. Lost execution duration. The old code decided whether to read
   `metadata.duration` based on whether `"response" in result` — but a failed
   combination carries an explicit `"response": None` (see
   `main.py::_failed_model_response`), so that key check is true for failures
   too. The immediate consequence was worse than losing the duration: every
   failed combination sent `len(None)` into the CSV writers and crashed report
   generation outright the moment a run contained one failure.

Nothing here makes a network call or costs money.
"""

import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporting import ReportingSystem, _csv_safe  # noqa: E402


COMBINATIONS = [
    {"id": "combo_ok", "model": "or_claude_sonnet_5", "template": "ins_analytical",
     "domain": "domain_general", "query": "query_1"},
    {"id": "combo_failed", "model": "or_mistral_small", "template": "ins_creative",
     "domain": "domain_general", "query": "query_1"},
]

MODEL_CONFIGS = {
    "or_claude_sonnet_5": {"name": "Claude Sonnet 5", "provider": "anthropic"},
    "or_mistral_small": {"name": "Mistral Small", "provider": "mistral"},
}


def _results_with_one_failure():
    """A succeeded call and a failed-but-timed call, shaped like main.py's records."""
    return {
        "combo_ok": {
            "status": "succeeded",
            "response": "A perfectly ordinary answer.",
            "metadata": {"model": "or_claude_sonnet_5", "duration": 1.5},
        },
        "combo_failed": {
            "status": "failed",
            "response": None,
            "error": {"kind": "timeout", "message": "upstream timed out"},
            "metadata": {"model": "or_mistral_small", "duration": 12.3},
        },
    }


def _read_csv_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestCsvSafeHelper(unittest.TestCase):
    def test_a_leading_equals_sign_gets_an_apostrophe(self):
        self.assertEqual(_csv_safe("=1+1"), "'=1+1")

    def test_a_leading_plus_minus_or_at_sign_gets_an_apostrophe(self):
        for char in ("+", "-", "@"):
            with self.subTest(char=char):
                self.assertEqual(_csv_safe(f"{char}cmd|'/c calc'!A1"),
                                  f"'{char}cmd|'/c calc'!A1")

    def test_ordinary_text_passes_through_unchanged(self):
        self.assertEqual(_csv_safe("A perfectly ordinary title"),
                          "A perfectly ordinary title")

    def test_non_string_values_pass_through_unchanged(self):
        # A numeric column must not be turned into a text column by this pass.
        self.assertEqual(_csv_safe(42), 42)
        self.assertEqual(_csv_safe(None), None)
        self.assertEqual(_csv_safe(True), True)


class TestIdeasCsvFormulaInjection(unittest.TestCase):
    """`ideas.csv` writes a model's synthesized title and description raw."""

    def _export_ideas(self, ideas):
        with tempfile.TemporaryDirectory() as tmp:
            rs = ReportingSystem(run_output_dir=tmp)
            path = rs._generate_ideas_csv(ideas, {}, {}, MODEL_CONFIGS)
            return _read_csv_rows(path)

    def test_a_response_starting_with_equals_cannot_become_a_formula(self):
        ideas = {
            "idea_1": {
                "title": "=cmd|'/c calc'!A1",
                "description": "Ordinary description",
            }
        }
        rows = self._export_ideas(ideas)

        self.assertEqual(rows[0]["title"], "'=cmd|'/c calc'!A1")
        # The apostrophe must have actually landed in the file, not merely be
        # absent from a title that happened not to need it — assert the raw
        # attack string is not what got written.
        self.assertNotEqual(rows[0]["title"], "=cmd|'/c calc'!A1")

    def test_a_description_starting_with_at_sign_is_also_defused(self):
        ideas = {
            "idea_1": {
                "title": "Ordinary title",
                "description": "@SUM(1+1)*cmd",
            }
        }
        rows = self._export_ideas(ideas)

        self.assertEqual(rows[0]["description"], "'@SUM(1+1)*cmd")

    def test_plus_and_minus_leading_text_are_defused_too(self):
        for char in ("+", "-"):
            with self.subTest(char=char):
                ideas = {"idea_1": {"title": f"{char}2+3", "description": "d"}}
                rows = self._export_ideas(ideas)
                self.assertTrue(rows[0]["title"].startswith("'" + char))

    def test_text_not_starting_with_a_formula_character_is_unchanged(self):
        ideas = {"idea_1": {"title": "A normal idea", "description": "Fine."}}
        rows = self._export_ideas(ideas)

        self.assertEqual(rows[0]["title"], "A normal idea")
        self.assertEqual(rows[0]["description"], "Fine.")


class TestCombinationsCsvDuration(unittest.TestCase):
    """Duration must survive a failed call, and reading it must not crash."""

    def _export_combinations(self, results):
        with tempfile.TemporaryDirectory() as tmp:
            rs = ReportingSystem(run_output_dir=tmp)
            path = rs._generate_combinations_csv(COMBINATIONS, results, {}, MODEL_CONFIGS)
            return _read_csv_rows(path)

    def test_a_failed_combination_does_not_crash_the_export(self):
        # Before the fix, "response" in results[combo_id] was true even for a
        # failed record (response is explicitly None), so the code proceeded to
        # len(None) and raised — this call must simply succeed.
        try:
            rows = self._export_combinations(_results_with_one_failure())
        except TypeError as exc:
            self.fail(f"combinations.csv generation crashed on a failed result: {exc}")

        self.assertEqual(len(rows), 2)

    def test_a_failed_but_timed_call_keeps_its_duration(self):
        rows = self._export_combinations(_results_with_one_failure())
        failed_row = next(r for r in rows if r["combination_id"] == "combo_failed")

        self.assertEqual(failed_row["execution_time"], "12.3")
        self.assertEqual(failed_row["status"], "failed")
        self.assertEqual(failed_row["response_length"], "")

    def test_a_succeeded_call_is_still_reported_correctly(self):
        rows = self._export_combinations(_results_with_one_failure())
        ok_row = next(r for r in rows if r["combination_id"] == "combo_ok")

        self.assertEqual(ok_row["status"], "succeeded")
        self.assertEqual(ok_row["execution_time"], "1.5")
        self.assertEqual(ok_row["response_length"], str(len("A perfectly ordinary answer.")))

    def test_a_combination_never_attempted_is_marked_not_executed(self):
        rows = self._export_combinations({"combo_ok": _results_with_one_failure()["combo_ok"]})
        skipped_row = next(r for r in rows if r["combination_id"] == "combo_failed")

        self.assertEqual(skipped_row["status"], "not_executed")
        self.assertEqual(skipped_row["execution_time"], "")


class TestModelPerformanceCsvDuration(unittest.TestCase):
    """The same 'response' key-vs-value bug, in the pandas-based model CSV."""

    def _export_models(self, results):
        with tempfile.TemporaryDirectory() as tmp:
            rs = ReportingSystem(run_output_dir=tmp)
            path = rs._generate_models_csv(COMBINATIONS, results, {}, MODEL_CONFIGS)
            return _read_csv_rows(path)

    def test_a_failed_combination_does_not_crash_the_export(self):
        try:
            rows = self._export_models(_results_with_one_failure())
        except TypeError as exc:
            self.fail(f"model_performance.csv generation crashed on a failed result: {exc}")

        self.assertEqual(len(rows), 2)

    def test_the_failed_models_duration_is_counted_not_dropped(self):
        rows = self._export_models(_results_with_one_failure())
        mistral_row = next(r for r in rows if r["model_id"] == "or_mistral_small")

        # A single failed call is this model's only data point: its duration
        # must show up as the average, not be silently excluded from it.
        self.assertEqual(mistral_row["avg_execution_time"], "12.3")
        self.assertEqual(mistral_row["failed_count"], "1")

    def test_a_successful_models_failed_count_is_zero(self):
        rows = self._export_models(_results_with_one_failure())
        claude_row = next(r for r in rows if r["model_id"] == "or_claude_sonnet_5")

        self.assertEqual(claude_row["failed_count"], "0")


class TestSummaryAndMetadataReportsSurviveAFailure(unittest.TestCase):
    """The same key-vs-value bug also lived in the Markdown/JSON report bodies.

    Fixed alongside finding 6 because it is the identical defect (a failed
    result's "response": None satisfies "response" in result) in the same
    file — leaving it in place would still crash report generation for any
    run containing a failure, just one function later.
    """

    def _reporting_system(self, tmp):
        return ReportingSystem(run_output_dir=tmp, report_format="markdown")

    def test_the_markdown_run_summary_does_not_crash_on_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            rs = self._reporting_system(tmp)
            try:
                rs.generate_run_summary(
                    query="test query",
                    combinations=COMBINATIONS,
                    results=_results_with_one_failure(),
                    evaluations={},
                    synthesized_ideas={},
                    config={},
                    model_configs=MODEL_CONFIGS,
                    run_params={},
                )
            except TypeError as exc:
                self.fail(f"run summary generation crashed on a failed result: {exc}")

    def test_the_json_run_summary_does_not_crash_on_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            rs = ReportingSystem(run_output_dir=tmp, report_format="json")
            try:
                rs.generate_run_summary(
                    query="test query",
                    combinations=COMBINATIONS,
                    results=_results_with_one_failure(),
                    evaluations={},
                    synthesized_ideas={},
                    config={},
                    model_configs=MODEL_CONFIGS,
                    run_params={},
                )
            except TypeError as exc:
                self.fail(f"run summary (json) generation crashed on a failed result: {exc}")

    def test_the_metadata_report_does_not_crash_on_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            rs = self._reporting_system(tmp)
            try:
                rs.generate_metadata_report(
                    combinations=COMBINATIONS,
                    results=_results_with_one_failure(),
                    evaluations={},
                    model_configs=MODEL_CONFIGS,
                    instruction_templates={},
                )
            except TypeError as exc:
                self.fail(f"metadata report generation crashed on a failed result: {exc}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
