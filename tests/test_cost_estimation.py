#!/usr/bin/env python3
"""Tests for cost_estimation.py, added against the 2026-09-03 audit baseline.

Every finding here has a companion test that fails against the pre-fix code and passes
after it. Nothing in this file makes a network call, needs an API key, or costs money —
CostEstimator only reads local *config*.json files and static tables.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cost_estimation import CostEstimator, DEFAULT_CONCURRENCY  # noqa: E402


class _ChdirTestCase(unittest.TestCase):
    """Base class for tests that need CostEstimator to see a specific directory.

    _load_models_info() reads *config*.json via a bare os.listdir()/open(), i.e. always
    the current working directory — there is no way to point it elsewhere. Changing cwd
    for the duration of the test is the only way to control what it sees, so every such
    test must restore it afterwards or it corrupts every test that runs later in the
    same process.
    """

    def _use_tmp_cwd(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        original_cwd = os.getcwd()
        self.addCleanup(os.chdir, original_cwd)
        os.chdir(tmp.name)
        return tmp.name


class TestUnreadableConfigIsVisible(_ChdirTestCase):
    """HIGH finding 1: a config that cannot be read must not silently become a 2024
    fallback portfolio priced with the same confidence as a real answer.
    """

    def test_a_malformed_config_is_reported_not_silently_replaced(self):
        tmp = self._use_tmp_cwd()
        with open(os.path.join(tmp, "broken_config.json"), "w", encoding="utf-8") as f:
            f.write("{ this is not valid json")

        estimator = CostEstimator()

        self.assertTrue(estimator.config_errors,
                        "a malformed config file must be recorded as a config error")
        self.assertIn("broken_config.json", estimator.config_errors[0])

        estimate = estimator.estimate_cost({"models": 1, "instructions": 1, "variations": 0})
        self.assertTrue(estimate["config_errors"],
                        "the error must reach the returned estimate, not stay internal")

        message = estimator.get_warning_message(estimate)
        self.assertIsNotNone(message)
        self.assertIn("CONFIGURATION WARNING", message)
        self.assertIn("broken_config.json", message)

    def test_a_config_with_no_usable_models_is_also_reported(self):
        tmp = self._use_tmp_cwd()
        with open(os.path.join(tmp, "empty_config.json"), "w", encoding="utf-8") as f:
            json.dump({"not_models": []}, f)

        estimator = CostEstimator()

        self.assertTrue(estimator.config_errors,
                        "a config that declares zero usable models is an error, not silence")

    def test_genuinely_absent_configuration_stays_silent(self):
        """The ONE case the fallback is intended: no *config*.json exists at all.

        This is the control for the two tests above — proving they fail for the right
        reason (a bad file), not merely because the fallback path was reached at all.
        """
        self._use_tmp_cwd()

        estimator = CostEstimator()

        self.assertEqual(estimator.config_errors, [],
                         "no configuration to read is not a failure and must not warn")
        estimate = estimator.estimate_cost({"models": 1, "instructions": 1, "variations": 0})
        self.assertEqual(estimate["config_errors"], [])
        self.assertIsNone(estimator.get_warning_message(estimate))


class TestNumericParameterValidation(unittest.TestCase):
    """HIGH finding 4: negative or non-integer numeric parameters must be rejected
    clearly at the estimate_cost() boundary, not silently turned into a negative price
    or a bare TypeError somewhere downstream.
    """

    def setUp(self):
        # A real instance: the "valid parameters" case must run the full pipeline,
        # which needs self.models_info populated the way __init__ does it.
        self.est = CostEstimator()

    def test_negative_max_tokens_is_rejected(self):
        estimate = self.est.estimate_cost(
            {"models": 1, "instructions": 1, "variations": 0,
             "parameters": {"max_tokens": -100}})
        self.assertTrue(estimate["is_invalid"])
        self.assertTrue(any("max_tokens" in e for e in estimate["parameter_errors"]))
        self.assertIsNone(estimate["total_cost"])

    def test_negative_models_count_is_rejected(self):
        estimate = self.est.estimate_cost({"models": -3, "instructions": 1, "variations": 0})
        self.assertTrue(estimate["is_invalid"])
        self.assertTrue(any("models" in e for e in estimate["parameter_errors"]))

    def test_non_integer_variations_is_rejected(self):
        estimate = self.est.estimate_cost(
            {"models": 1, "instructions": 1, "variations": "two"})
        self.assertTrue(estimate["is_invalid"])
        self.assertTrue(any("variations" in e for e in estimate["parameter_errors"]))

    def test_negative_max_combinations_is_rejected(self):
        estimate = self.est.estimate_cost(
            {"models": 1, "instructions": 1, "variations": 0, "max_combinations": -1})
        self.assertTrue(estimate["is_invalid"])

    def test_boolean_is_not_accepted_as_a_count(self):
        """bool is a subclass of int — True/False must not silently pass as 1/0."""
        estimate = self.est.estimate_cost(
            {"models": True, "instructions": 1, "variations": 0})
        self.assertTrue(estimate["is_invalid"])

    def test_valid_parameters_are_accepted(self):
        estimate = self.est.estimate_cost(
            {"models": 2, "instructions": 3, "variations": 2,
             "parameters": {"max_tokens": 4096}})
        self.assertNotIn("is_invalid", estimate)
        self.assertIsInstance(estimate["total_cost"], float)

    def test_invalid_estimate_does_not_crash_the_indicator_helpers(self):
        """A caller that formats total_cost/time without checking is_invalid first must
        get a clear string, not a TypeError from formatting None."""
        estimate = self.est.estimate_cost({"models": -1})
        self.assertEqual(self.est.get_cost_indicator(estimate), "N/A (invalid parameters)")
        self.assertEqual(self.est.get_time_indicator(estimate), "N/A (invalid parameters)")
        message = self.est.get_warning_message(estimate)
        self.assertIn("INVALID PARAMETERS", message)


class TestDomainsListCountsAsDomainContext(unittest.TestCase):
    """MEDIUM finding 5: `_estimate_combinations` already treats `domains` (a list) as
    domain context; `_estimate_prompt_tokens` only checked `domain` (singular), so a run
    selecting several domains via `domains` was quoted as if none of them added any
    prompt tokens at all.
    """

    def setUp(self):
        self.est = CostEstimator.__new__(CostEstimator)

    def test_domains_list_without_domain_key_adds_domain_context_tokens(self):
        with_domains = self.est._estimate_prompt_tokens(
            {"query": "q", "domains": ["finance", "health"]})
        without_domain = self.est._estimate_prompt_tokens({"query": "q"})
        self.assertGreater(with_domains, without_domain)

    def test_single_domain_still_works(self):
        with_domain = self.est._estimate_prompt_tokens({"query": "q", "domain": "finance"})
        without_domain = self.est._estimate_prompt_tokens({"query": "q"})
        self.assertGreater(with_domain, without_domain)

    def test_domains_and_domain_add_the_same_amount(self):
        via_domain = self.est._estimate_prompt_tokens({"query": "q", "domain": "finance"})
        via_domains = self.est._estimate_prompt_tokens({"query": "q", "domains": ["finance"]})
        self.assertEqual(via_domain, via_domains)


class TestTimeEstimateReflectsParallelExecution(unittest.TestCase):
    """HIGH finding 6: execution is parallel (main.py's ParallelExecutionEngine, shared
    worker pool), but the displayed estimate used to be the SERIAL sum of every model's
    own processing time — a run with several slow models looked far longer than it
    would actually take.
    """

    def setUp(self):
        self.est = CostEstimator()

    def _params(self, **overrides):
        params = {"models": 4, "instructions": 3, "variations": 2,
                  "parameters": {"max_tokens": 16000}}
        params.update(overrides)
        return params

    def test_makespan_is_smaller_than_the_serial_sum_when_concurrency_allows_it(self):
        estimate = self.est.estimate_cost(self._params())
        self.assertLess(estimate["time_estimate_max"], estimate["sequential_time_max"],
                        "with more than one worker the makespan must beat the serial sum")

    def test_default_concurrency_matches_the_documented_worker_pool(self):
        estimate = self.est.estimate_cost(self._params())
        self.assertEqual(estimate["concurrency_assumed"],
                         min(DEFAULT_CONCURRENCY, estimate["combinations_estimate"]))

    def test_caller_supplied_concurrency_changes_the_makespan(self):
        one_worker = self.est.estimate_cost(self._params(max_workers=1))
        many_workers = self.est.estimate_cost(self._params(max_workers=100))
        self.assertEqual(one_worker["time_estimate_max"], one_worker["sequential_time_max"],
                         "a single worker IS the serial case")
        self.assertLess(many_workers["time_estimate_max"], one_worker["time_estimate_max"])

    def test_sequential_total_is_still_available_but_separately_labelled(self):
        estimate = self.est.estimate_cost(self._params())
        self.assertIn("sequential_time_max", estimate)
        self.assertIn("sequential_time_min", estimate)
        self.assertNotEqual(estimate["time_estimate_max"], estimate["sequential_time_max"])

    def test_time_warning_level_is_based_on_the_makespan_not_the_serial_sum(self):
        """A portfolio whose serial sum alone would cross a warning threshold must not
        trigger it once parallel execution brings the makespan back under it.

        With this fixture (measured): sequential_time_max ~= 32 min, which alone would
        clear even the "high" (15 min) threshold — but with 100 workers available for
        36 combinations the makespan drops under 1 minute, below the lowest ("notice",
        2 min) threshold. The old, serial-sum-based warning level would have been
        wrong in the direction that matters: alarming a user over a run that finishes
        in under a minute.
        """
        from cost_estimation import TIME_WARNING_THRESHOLDS

        estimate = self.est.estimate_cost(self._params(max_workers=100))
        self.assertGreaterEqual(estimate["sequential_time_max"], TIME_WARNING_THRESHOLDS["high"])
        self.assertLess(estimate["time_estimate_max"], TIME_WARNING_THRESHOLDS["notice"])
        self.assertIsNone(estimate["time_warning_level"])


class TestDocumentationClaimsAreTruthful(unittest.TestCase):
    """MEDIUM finding 8 + LOW finding 9: two comments asserted things that are false.

    A textual check rather than a behavioural one, because the defect IS the text —
    matches the pattern already used elsewhere in this suite (see
    TestWebServerDefaults / TestWebAndCliAgreeOnOutputFormat in test_failure_visibility.py).
    """

    @classmethod
    def setUpClass(cls):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "cost_estimation.py"), encoding="utf-8") as f:
            cls.source = f.read()

    def test_pricing_table_no_longer_claims_a_specific_currency_date(self):
        # The corrected comment is allowed to quote the old wrong claim for context
        # (as it does), so check for the exact original line rather than a substring
        # that context would also contain.
        self.assertNotIn(
            "Based on publicly available pricing as of May 2024, updated for 2025 models "
            "and dual provider support",
            self.source)
        self.assertIn("STATIC FALLBACK ONLY", self.source)

    def test_tokenizer_is_not_misattributed_to_claude(self):
        self.assertNotIn("Claude's encoding", self.source)
        # The corrected comment must still explain what cl100k_base actually is.
        self.assertIn("cl100k_base", self.source)
        self.assertIn("OpenAI", self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
