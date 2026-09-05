#!/usr/bin/env python3
"""The pre-run estimate learns from what runs were actually billed.

`TYPICAL_RESPONSE_TOKENS` is one measurement, of one query, on one day, and its own
comment says to re-measure before trusting it further. Since 03.09.2026 every run
writes `cost_report.json` carrying the tokens the provider actually billed, so the
estimate can correct itself instead of waiting for someone to re-measure by hand.

The fallback matters as much as the measurement: a self-correcting number that
corrects itself from two data points is worse than an honest constant.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import ISEEGuardrails


def write_report(root, run, per_model):
    directory = os.path.join(root, f"run_{run}")
    os.makedirs(directory, exist_ok=True)
    with io.open(os.path.join(directory, "cost_report.json"), "w", encoding="utf-8") as fh:
        json.dump({"per_model": per_model}, fh)


class TestMeasuredResponseTokens(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_nothing_on_record_yields_no_measurement(self):
        self.assertIsNone(ISEEGuardrails.measured_response_tokens(self.root))

    def test_too_few_calls_yield_no_measurement(self):
        # Below the threshold the constant must win, however tempting the number.
        write_report(self.root, "20260903_010000",
                     {"m1": {"calls": 5, "completion_tokens": 50_000}})

        self.assertIsNone(ISEEGuardrails.measured_response_tokens(self.root))

    def test_enough_calls_yield_the_billed_average(self):
        write_report(self.root, "20260903_010000",
                     {"m1": {"calls": 15, "completion_tokens": 30_000},
                      "m2": {"calls": 15, "completion_tokens": 30_000}})

        self.assertEqual(ISEEGuardrails.measured_response_tokens(self.root), 2000)

    def test_several_runs_are_pooled(self):
        for i in range(3):
            write_report(self.root, f"2026090{i}_010000",
                         {"m": {"calls": 10, "completion_tokens": 10_000}})

        self.assertEqual(ISEEGuardrails.measured_response_tokens(self.root), 1000)

    def test_only_the_most_recent_runs_count(self):
        # A portfolio or question style that changed months ago must not keep
        # dragging today's estimate.
        for i in range(ISEEGuardrails.MEASURED_TOKENS_RUNS + 3):
            tokens = 100_000 if i < 3 else 10_000     # the oldest three are outliers
            write_report(self.root, f"202609{i:02d}_010000",
                         {"m": {"calls": 10, "completion_tokens": tokens}})

        self.assertEqual(ISEEGuardrails.measured_response_tokens(self.root), 1000)

    def test_a_malformed_report_is_skipped_not_guessed_at(self):
        write_report(self.root, "20260903_010000",
                     {"m": {"calls": 25, "completion_tokens": 50_000}})
        broken = os.path.join(self.root, "run_20260903_020000")
        os.makedirs(broken, exist_ok=True)
        with io.open(os.path.join(broken, "cost_report.json"), "w", encoding="utf-8") as fh:
            fh.write("{not json")

        self.assertEqual(ISEEGuardrails.measured_response_tokens(self.root), 2000)


class TestTheEstimateUsesIt(unittest.TestCase):
    def test_the_estimate_still_works_without_any_measurement(self):
        estimate = ISEEGuardrails.estimate_cost(66)

        self.assertGreater(estimate, 0)
        self.assertLess(estimate, 5, "a 66-call run costing over $5 is the old 17x error")


if __name__ == "__main__":
    unittest.main(verbosity=2)
