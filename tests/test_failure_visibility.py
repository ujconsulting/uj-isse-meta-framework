#!/usr/bin/env python3
"""Tests for the failure-visibility contract.

Guards the invariant this project got wrong for a long time: **a failed API call must be
reported as a failure**. Before 2026-09-02 an HTTP 400 from every model produced a
complete, plausible, entirely fabricated report, and the run summary called it a success.

Every test here is mocked. Nothing in this file makes a network call, needs an API key,
or costs money.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_api_integration import APIIntegrationError, RateLimitError  # noqa: E402


class _StubTemplate:
    """Minimal stand-in for an InstructionTemplate."""

    metadata = {"cognitive_style": "analytical"}

    def format(self, _variables):
        return "INSTRUCTION"


class _StubQuery:
    text = "QUERY"
    variables = {}


class _StubDomain:
    description = "DOMAIN"


def _make_app():
    """Build an ISEEApplication with __init__ bypassed.

    `ISEEApplication.__init__` loads config and builds clients; none of that is needed to
    exercise the failure contract, and invoking it would reintroduce the file and network
    dependencies these tests exist to avoid.
    """
    from main import ISEEApplication

    app = ISEEApplication.__new__(ISEEApplication)
    app.model_configs = {}
    app.error_detector = MagicMock()
    app.error_detector.is_api_error.return_value = (False, "")
    return app


COMBINATION = {"id": "combo_1", "model": "anthropic/claude-sonnet-5"}


class TestStructuredError(unittest.TestCase):
    """APIIntegrationError must carry the HTTP status, not just a message."""

    def test_status_code_survives(self):
        err = APIIntegrationError("bad parameter", status_code=400, provider="OpenRouter",
                                  model="anthropic/claude-sonnet-5", retryable=False)
        self.assertEqual(err.status_code, 400)
        self.assertFalse(err.as_dict()["retryable"])
        self.assertEqual(err.as_dict()["error_type"], "APIIntegrationError")

    def test_plain_construction_still_works(self):
        """Existing `raise APIIntegrationError("msg")` call sites must not break."""
        err = APIIntegrationError("something went wrong")
        self.assertIsNone(err.status_code)
        self.assertEqual(str(err), "something went wrong")

    def test_subclass_inherits_fields(self):
        err = RateLimitError("slow down", status_code=429, retryable=True)
        self.assertEqual(err.status_code, 429)
        self.assertTrue(err.retryable)


class TestNoSilentSimulation(unittest.TestCase):
    """The three paths that used to return a simulated response instead of a failure."""

    def _assert_is_failure(self, result, kind):
        self.assertEqual(result["status"], "failed", "result must be marked failed")
        self.assertIsNone(result["response"],
                          "a failure must carry response=None, never placeholder text")
        self.assertEqual(result["error"]["kind"], kind)
        self.assertEqual(result["combination_id"], "combo_1")

    def test_http_error_is_not_simulated(self):
        app = _make_app()
        client = MagicMock()
        client.generate.side_effect = APIIntegrationError(
            "unsupported parameter: temperature", status_code=400, retryable=False)

        with patch.object(app, "_get_or_create_model_client", return_value=client), \
             patch.object(app, "_simulate_model_response",
                          side_effect=AssertionError("simulation must not be used")):
            result = app._generate_model_response(
                COMBINATION, _StubTemplate(), _StubQuery(), _StubDomain())

        self._assert_is_failure(result, "exception")
        self.assertEqual(result["error"]["status_code"], 400)
        self.assertFalse(result["error"]["retryable"])

    def test_missing_client_is_not_simulated(self):
        app = _make_app()
        with patch.object(app, "_get_or_create_model_client", return_value=None), \
             patch.object(app, "_simulate_model_response",
                          side_effect=AssertionError("simulation must not be used")):
            result = app._generate_model_response(
                COMBINATION, _StubTemplate(), _StubQuery(), _StubDomain())

        self._assert_is_failure(result, "no_client")

    def test_error_body_returned_with_http_200_is_not_simulated(self):
        """Some providers return an error *as* a 200 body. That is still a failure."""
        app = _make_app()
        app.error_detector.is_api_error.return_value = (True, "provider returned an error object")
        client = MagicMock()
        client.generate.return_value = '{"error": {"message": "no such model"}}'

        with patch.object(app, "_get_or_create_model_client", return_value=client), \
             patch.object(app, "_simulate_model_response",
                          side_effect=AssertionError("simulation must not be used")):
            result = app._generate_model_response(
                COMBINATION, _StubTemplate(), _StubQuery(), _StubDomain())

        self._assert_is_failure(result, "api_error_in_body")

    def test_success_is_marked_succeeded(self):
        app = _make_app()
        client = MagicMock()
        client.generate.return_value = "a real answer"

        with patch.object(app, "_get_or_create_model_client", return_value=client):
            result = app._generate_model_response(
                COMBINATION, _StubTemplate(), _StubQuery(), _StubDomain())

        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["response"], "a real answer")
        self.assertNotIn("error", result)


class TestPipelineSurvivesTotalFailure(unittest.TestCase):
    """An all-failure run must not crash, and must not score anything."""

    def test_partition_separates_failures(self):
        from main import ISEEApplication

        results = {
            "ok": {"status": "succeeded", "response": "text"},
            "failed": {"status": "failed", "response": None, "error": {"kind": "no_client"}},
            "legacy_ok": {"response": "text from before status existed"},
            "empty": {"response": ""},
        }
        ok, failed = ISEEApplication._partition_successful(results)
        self.assertEqual(set(ok), {"ok", "legacy_ok"})
        self.assertEqual(set(failed), {"failed", "empty"})

    def test_evaluate_results_on_all_failures_returns_empty(self):
        """The former behaviour was a KeyError on result["response"]."""
        app = _make_app()
        app.results = {}
        app.scoring_framework = MagicMock()

        results = {
            "c1": {"status": "failed", "response": None, "error": {"kind": "exception"}},
            "c2": {"status": "failed", "response": None, "error": {"kind": "no_client"}},
        }
        from main import ISEEApplication

        evaluations = ISEEApplication.evaluate_results(app, results=results)
        self.assertEqual(evaluations, {})
        app.scoring_framework.score_text.assert_not_called()


class TestRawResponseSeparation(unittest.TestCase):
    """Failures must not land in raw_responses/, which the Explorer indexes and ranks."""

    def test_failure_goes_to_failed_responses_dir(self):
        import tempfile
        from pathlib import Path
        from main import ISEEApplication

        app = ISEEApplication.__new__(ISEEApplication)
        with tempfile.TemporaryDirectory() as tmp:
            app.output_directory = tmp
            failure = {
                "combination_id": "combo_1",
                "status": "failed",
                "response": None,
                "prompt": "P",
                "error": {"kind": "exception", "message": "HTTP 400", "status_code": 400},
                "metadata": {"timestamp": 0, "duration": 0.1},
            }
            ISEEApplication.save_raw_response(app, failure, COMBINATION)

            self.assertFalse((Path(tmp) / "raw_responses").exists(),
                             "a failure must not create or populate raw_responses/")
            written = list((Path(tmp) / "failed_responses").glob("*.md"))
            self.assertEqual(len(written), 1)
            body = written[0].read_text(encoding="utf-8")
            self.assertIn("FAILED", body)
            self.assertNotIn("Response not available", body)

    def test_success_goes_to_raw_responses_dir(self):
        import tempfile
        from pathlib import Path
        from main import ISEEApplication

        app = ISEEApplication.__new__(ISEEApplication)
        with tempfile.TemporaryDirectory() as tmp:
            app.output_directory = tmp
            success = {
                "combination_id": "combo_1",
                "status": "succeeded",
                "response": "a real answer",
                "prompt": "P",
                "metadata": {"timestamp": 0, "duration": 0.1},
            }
            ISEEApplication.save_raw_response(app, success, COMBINATION)

            written = list((Path(tmp) / "raw_responses").glob("*.md"))
            self.assertEqual(len(written), 1)
            self.assertIn("a real answer", written[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
