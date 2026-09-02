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


class TestOpenRouterPayload(unittest.TestCase):
    """The exact request body sent to OpenRouter.

    Two defect classes are guarded here. Sampling parameters must be sent only when the
    configuration asks for them — `anthropic/claude-sonnet-5` and `openai/gpt-5.6-luna`
    accept neither `temperature` nor `top_p`, and the client used to inject
    `temperature=0.7` whenever the config omitted it, so opting out was impossible. And
    the mandatory fields must all still be present: while moving `temperature` out of the
    payload literal, `messages` was briefly dropped with it, which would have made every
    request invalid.
    """

    def _capture_payload(self, params):
        from model_api_integration import OpenRouterClient

        client = OpenRouterClient.__new__(OpenRouterClient)
        # "example-" prefix: matches the secret-scan hook's placeholder convention,
        # so a dummy in a test file does not read as a leaked credential.
        client.api_key = "example-key-used-only-in-this-test"
        client.base_url = "https://openrouter.ai/api/v1/chat/completions"
        client.site_url = None
        client.app_name = None

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        with patch("model_api_integration.requests.post", return_value=response) as post:
            OpenRouterClient.generate(client, "PROMPT", params)
        return post.call_args.kwargs["json"]

    def test_mandatory_fields_present(self):
        payload = self._capture_payload({"model": "x/y", "max_tokens": 16000})
        self.assertEqual(payload["model"], "x/y")
        self.assertEqual(payload["max_tokens"], 16000)
        self.assertEqual(payload["messages"], [{"role": "user", "content": "PROMPT"}],
                         "messages is mandatory — without it every request is invalid")

    def test_sampling_params_omitted_when_config_omits_them(self):
        payload = self._capture_payload(
            {"model": "anthropic/claude-sonnet-5", "max_tokens": 16000})
        self.assertNotIn("temperature", payload,
                         "models that reject temperature must not receive it")
        self.assertNotIn("top_p", payload)

    def test_sampling_params_passed_through_when_supplied(self):
        payload = self._capture_payload(
            {"model": "x-ai/grok-4.3", "max_tokens": 16000,
             "temperature": 0.7, "top_p": 0.95})
        self.assertEqual(payload["temperature"], 0.7)
        self.assertEqual(payload["top_p"], 0.95)


class TestConfiguredPortfolio(unittest.TestCase):
    """The shipped configuration must match the contract the code reads."""

    @classmethod
    def setUpClass(cls):
        import json
        import io

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with io.open(os.path.join(root, "openrouter_config.json"), encoding="utf-8") as f:
            cls.config = json.load(f)
        cls.models = cls.config["models"]["api_models"]

    def test_fourteen_models_one_per_house(self):
        self.assertEqual(len(self.models), 14)
        houses = {m["parameters"]["model"].split("/")[0] for m in self.models}
        self.assertEqual(len(houses), 14, f"expected one model per house, got {sorted(houses)}")

    def test_required_fields_present(self):
        # strategic_order is required by validate_expanded_config.py; cost_tier and
        # features drive selection and display in ~140 places; ui_priority gates the
        # Web UI's curated portfolio (app.py:_filter_strategic_models).
        for m in self.models:
            for field in ("id", "name", "provider", "requires", "parameters",
                          "features", "cost_tier", "ui_priority", "strategic_order"):
                self.assertIn(field, m, f"{m.get('id')} is missing {field}")
            self.assertIn(m["cost_tier"], ("budget", "standard", "premium", "premium_plus"))

    def test_strategic_subset_is_not_empty(self):
        strategic = [m for m in self.models if m.get("ui_priority") == "strategic"]
        self.assertTrue(strategic, "an empty strategic subset empties the Web UI portfolio")

    def test_max_tokens_raised(self):
        # The old configuration capped output at 2048-4096 against models allowing
        # 16k-943k, and evaluation_scoring.py penalises truncated answers.
        for m in self.models:
            self.assertGreaterEqual(m["parameters"]["max_tokens"], 16000, m["id"])

    def test_models_rejecting_sampling_params_do_not_declare_them(self):
        rejecting = {"anthropic/claude-sonnet-5", "openai/gpt-5.6-luna"}
        for m in self.models:
            if m["parameters"]["model"] in rejecting:
                self.assertNotIn("temperature", m["parameters"], m["id"])
                self.assertNotIn("top_p", m["parameters"], m["id"])

    def test_ollama_models_are_disabled(self):
        # main.py loads ollama_models into the SAME selection pool as api_models, so an
        # enabled entry is selectable and would fail against a runtime that is not there.
        for m in self.config["models"].get("ollama_models", []):
            self.assertTrue(m.get("disabled"), f"{m.get('id')} must be disabled")


class TestTextFilesAreUtf8(unittest.TestCase):
    """Every text-mode open() in the core modules must state its encoding.

    Without it Python uses the locale encoding, which on Windows is cp1252. This
    framework writes model output to disk, and model output routinely contains
    characters cp1252 cannot represent — a run once completed all fourteen calls,
    evaluated them, ranked them, synthesised the findings, and then died writing the
    final file because the text contained "→" (U+2192).

    A lint-style test rather than a per-path one: the defect class is "somebody added an
    open() and forgot", and only a sweep catches the next one.
    """

    CORE_MODULES = [
        "main.py", "app.py", "reporting.py", "analysis.py", "query_export.py",
        "cognitive_diversity_extractor.py", "evaluation_scoring.py", "domain_manager.py",
        "performance_tracker.py", "cost_estimation.py",
    ]

    def test_no_text_open_without_encoding(self):
        import io
        import re

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        call = re.compile(r"open\((?P<args>[^()]*?(?:\([^()]*\)[^()]*?)*)\)")
        text_mode = re.compile(r"""['"]([rwax]\+?t?)['"]""")

        offenders = []
        for name in self.CORE_MODULES:
            path = os.path.join(root, name)
            if not os.path.exists(path):
                continue
            source = io.open(path, encoding="utf-8").read()
            for lineno, line in enumerate(source.splitlines(), 1):
                for m in call.finditer(line):
                    args = m.group("args")
                    if "encoding" in args or "b'" in args or 'b"' in args:
                        continue
                    if text_mode.search(args):
                        offenders.append(f"{name}:{lineno}  {line.strip()[:80]}")

        self.assertEqual(
            offenders, [],
            "text-mode open() without encoding='utf-8' (cp1252 on Windows):\n  "
            + "\n  ".join(offenders))

    def test_non_ascii_round_trips_through_a_written_file(self):
        """The concrete characters that broke a real run."""
        import io
        import tempfile
        from pathlib import Path

        payload = "Rang 1 → Rang 2 · Wärmepumpe · „Handwerker\" · 🏆"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "out.md"
            with open(target, "w", encoding="utf-8") as f:
                f.write(payload)
            self.assertEqual(io.open(target, encoding="utf-8").read(), payload)


class TestCostEstimatesAreDerived(unittest.TestCase):
    """Cost figures must come from recorded prices, not from constants or guesses.

    Three defects are guarded. The CLI guardrail priced every combination at a flat
    $0.08 regardless of the configured portfolio — for the current one that overstates a
    66-call run as $5.28 against roughly $0.31, and the guardrail *blocks* runs on that
    number. The response-token estimate used 0.85 × max_tokens, which was reasonable at
    max_tokens 4096 and predicts 13,600 tokens per call at 16,000. And an OpenRouter
    model with no known price was charged at Anthropic rates, which for
    upstage/solar-pro4 is wrong by about sixty times.
    """

    @classmethod
    def setUpClass(cls):
        import io
        import json

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.root = root
        with io.open(os.path.join(root, "openrouter_config.json"), encoding="utf-8") as f:
            cls.models = json.load(f)["models"]["api_models"]

    def test_every_model_carries_a_price(self):
        for m in self.models:
            pricing = m.get("pricing")
            self.assertIsInstance(pricing, dict, f"{m['id']} has no pricing block")
            for field in ("prompt_per_mtok", "completion_per_mtok", "fetched"):
                self.assertIn(field, pricing, f"{m['id']} pricing lacks {field}")
            # Per-MILLION, not per-token. A missing 1e6 conversion is a six-order-of-
            # magnitude error that still looks like a working feature, so assert the
            # magnitude rather than trusting the field name.
            self.assertGreater(pricing["completion_per_mtok"], 0.001, m["id"])
            self.assertLess(pricing["completion_per_mtok"], 1000, m["id"])

    def test_guardrail_uses_configured_prices_not_a_constant(self):
        from main import ISEEGuardrails

        cost = ISEEGuardrails.estimate_cost(
            66, config_path=os.path.join(self.root, "openrouter_config.json"))
        self.assertNotAlmostEqual(cost, 66 * 0.08, places=2,
                                  msg="still returning the flat $0.08 per combination")
        # Derived from the recorded prices: well under a dollar for this portfolio.
        self.assertLess(cost, 1.0)
        self.assertGreater(cost, 0.0)

    def test_guardrail_scales_with_the_portfolio(self):
        """A cheaper portfolio must produce a cheaper estimate — a constant would not."""
        import io
        import json
        import tempfile

        with io.open(os.path.join(self.root, "openrouter_config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        for m in cfg["models"]["api_models"]:
            m["pricing"]["prompt_per_mtok"] /= 10
            m["pricing"]["completion_per_mtok"] /= 10

        from main import ISEEGuardrails

        with tempfile.TemporaryDirectory() as tmp:
            cheap = os.path.join(tmp, "cheap.json")
            with io.open(cheap, "w", encoding="utf-8") as f:
                json.dump(cfg, f)
            expensive = ISEEGuardrails.estimate_cost(
                66, config_path=os.path.join(self.root, "openrouter_config.json"))
            self.assertAlmostEqual(
                ISEEGuardrails.estimate_cost(66, config_path=cheap), expensive / 10,
                places=4)

    def test_response_tokens_capped_at_the_measured_typical(self):
        from cost_estimation import TYPICAL_RESPONSE_TOKENS, CostEstimator

        est = CostEstimator.__new__(CostEstimator)
        # A high ceiling must not be mistaken for a forecast...
        self.assertEqual(
            CostEstimator._estimate_response_tokens(est, {"parameters": {"max_tokens": 16000}}),
            TYPICAL_RESPONSE_TOKENS)
        # ...but a genuinely low ceiling still binds.
        self.assertEqual(
            CostEstimator._estimate_response_tokens(est, {"parameters": {"max_tokens": 1000}}),
            850)

    def test_unknown_openrouter_model_is_not_priced_as_anthropic(self):
        import logging as _logging

        from cost_estimation import CostEstimator

        est = CostEstimator.__new__(CostEstimator)
        _logging.disable(_logging.CRITICAL)
        try:
            rate = CostEstimator._get_model_cost_rate(
                est, {"provider": "openrouter",
                      "parameters": {"model": "someone/model-invented-for-this-test"}})
        finally:
            _logging.disable(_logging.NOTSET)

        self.assertTrue(rate.get("price_unavailable"),
                        "an unknown model must be flagged, not silently priced")
        self.assertEqual(rate["input"], 0.0)

    def test_configured_price_beats_the_static_table(self):
        """The embedded price wins even where MODEL_COSTS holds a (stale) entry."""
        from cost_estimation import CostEstimator

        est = CostEstimator.__new__(CostEstimator)
        entry = {
            "provider": "openrouter",
            "parameters": {"model": "openai/gpt-4o-mini"},   # present in MODEL_COSTS
            "pricing": {"prompt_per_mtok": 42.0, "completion_per_mtok": 43.0,
                        "fetched": "2026-09-02"},
        }
        rate = CostEstimator._get_model_cost_rate(est, entry)
        self.assertEqual((rate["input"], rate["output"]), (42.0, 43.0))


class TestEstimatorPricesTheRightModels(unittest.TestCase):
    """Findings from the web-interface smoke test.

    `/api/estimate` for a request selecting three OpenRouter models answered with a
    breakdown for 'Claude Sonnet 4', 'GPT-4 Turbo' and 'Gemini 2.5 Pro' — the first three
    entries of globant_enterprise_config.json, a provider this installation cannot reach.
    Every `*config*.json` in the directory is merged into one pool and the selection was
    ignored entirely.
    """

    class _Params(dict):
        def get(self, key, default=None):
            return dict.get(self, key, default)

    def setUp(self):
        import logging as _logging

        from cost_estimation import CostEstimator

        _logging.disable(_logging.CRITICAL)
        self.addCleanup(_logging.disable, _logging.NOTSET)
        self.est = CostEstimator()

    def test_pool_is_not_empty(self):
        """Regression guard for a filter that silently emptied it.

        A `requires`-based credential filter looked principled but emptied the pool in any
        context that had not loaded .env, and the estimator then fell back to five
        hardcoded 2024 models without saying so.
        """
        self.assertGreaterEqual(len(self.est.models_info), 14)

    def test_selected_models_are_the_ones_priced(self):
        chosen = self.est._get_available_models_for_params(
            self._Params(selected_models=["or_claude_sonnet_5", "or_glm_53_flash"], models=2))
        self.assertEqual(
            sorted(m["parameters"]["model"] for m in chosen),
            ["anthropic/claude-sonnet-5", "z-ai/glm-5.3-flash"])

    def test_unselected_estimate_prefers_models_with_known_prices(self):
        chosen = self.est._get_available_models_for_params(self._Params(models=3))
        self.assertTrue(chosen)
        for m in chosen:
            self.assertIsInstance(
                m.get("pricing"), dict,
                f"{m.get('name')} has no recorded price and must not drive an estimate")

    def test_disabled_models_are_excluded(self):
        from cost_estimation import CostEstimator

        self.assertFalse(CostEstimator._model_is_usable({"id": "x", "disabled": True}))
        self.assertTrue(CostEstimator._model_is_usable({"id": "x"}))


class TestWebRunOutcomePlumbing(unittest.TestCase):
    """The web layer must read the child's output as UTF-8.

    main.py reconfigures its own streams, but app.py decoded them with the locale
    encoding. TextIOWrapper decodes in chunks, so one undefined byte discarded a whole
    8 KB block — and main.py prints "🏁 Parallel execution completed" 149 bytes after the
    `parallel_execution_complete` event, in the same block. The tally was lost and
    succeeded_combinations stayed 0 after three successful calls, visible only as a DEBUG
    line.
    """

    def test_subprocess_is_read_as_utf8(self):
        import io
        import re

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source = io.open(os.path.join(root, "app.py"), encoding="utf-8").read()
        m = re.search(r"subprocess\.Popen\((.*?)\n            \)", source, re.S)
        self.assertIsNotNone(m, "could not locate the Popen call")
        call = m.group(1)
        self.assertIn('encoding="utf-8"', call,
                      "without an explicit encoding the parent decodes as cp1252 on Windows")
        self.assertIn('errors="replace"', call,
                      "a bad byte must cost one character, not a block of progress events")

    def test_no_invented_domain_placeholder(self):
        """app.py inserted the domain "Technology", which does not exist.

        main.py then returned early without an error and the caller concatenated None
        onto a string, so every web run reaching that fallback died with
        `TypeError: can only concatenate str (not "NoneType") to str`.
        """
        import io
        import json

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source = io.open(os.path.join(root, "app.py"), encoding="utf-8").read()
        self.assertNotIn('converted["domain"] = "Technology"', source)

        with io.open(os.path.join(root, "openrouter_config.json"), encoding="utf-8") as f:
            names = {d["name"] for d in json.load(f)["domains"]}
        self.assertNotIn("Technology", names,
                         "if a domain by this name ever exists, revisit the fallback")


if __name__ == "__main__":
    unittest.main(verbosity=2)
