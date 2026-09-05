#!/usr/bin/env python3
"""A run that quietly changed what it asked must say so in its own deliverable.

`query_generator` falls back to static variations when the dynamic system raises,
and stamps a flag onto each variation's `variables`. Those are spread into
`template.format(...)` — which silently drops any key the template does not use.

Measured 05.09.2026: the flag reached the prompt, `combinations.csv` and the report
exactly nowhere. `dynamic_variation_degraded` was written in one place and read in
none, so a run whose variation system had failed was indistinguishable from one
where it worked.

A commit message in this session claimed the opposite — that the flag "reaches the
run's own output, not just a log nobody tails". It did not. These tests exist so
that claim stays true from now on.
"""

import os
import sys
import types
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


def make_args():
    return types.SimpleNamespace(
        query="Testfrage", models=1, instructions=1, variations=2,
        max_combinations=2, provider="openrouter",
        config="openrouter_config.json", output_format="markdown",
        simulate=True, parallel=True)


class FakeRun:
    """Only the attributes the metadata header reads."""
    combinations = []
    results = {}
    evaluations = {}
    synthesized_ideas = {}
    run_output_dir = "."
    model_configs = {}

    def __init__(self, report=None):
        self.query_generation_report = report


class TestDegradationReachesTheDeliverable(unittest.TestCase):
    def header(self, report):
        now = datetime.now()
        return main.generate_metadata_header(make_args(), FakeRun(report), now, now)

    def test_a_clean_run_says_nothing_about_degradation(self):
        text = self.header(None)

        self.assertNotIn("Query variation degraded", text)

    def test_a_degraded_run_says_so(self):
        text = self.header({"degraded_to_static": True,
                            "degradation_reason": "the dynamic system was unreachable"})

        self.assertIn("Query variation degraded", text)

    def test_the_reason_is_carried_not_just_the_fact(self):
        text = self.header({"degraded_to_static": True,
                            "degradation_reason": "the dynamic system was unreachable"})

        self.assertIn("the dynamic system was unreachable", text)

    def test_a_missing_reason_is_admitted_rather_than_invented(self):
        text = self.header({"degraded_to_static": True})

        self.assertIn("not recorded", text)

    def test_a_shortfall_in_variations_is_reported(self):
        text = self.header({"shortfall": 2})

        self.assertIn("Fewer variations than requested", text)
        self.assertIn("2 short", text)

    def test_no_shortfall_produces_no_line(self):
        text = self.header({"shortfall": 0})

        self.assertNotIn("Fewer variations", text)


class TestTheFlagAloneWouldNotHaveBeenEnough(unittest.TestCase):
    """Why the header line exists at all."""

    def test_template_formatting_drops_unused_variables(self):
        # This is the mechanism that swallowed the flag. If it ever changes, the
        # header line is still correct, but the reason recorded above is not.
        from instruction_templates import InstructionTemplate

        template = InstructionTemplate(id="x", name="X",
                                       template="Analyse {domain} carefully.")
        rendered = template.format({"domain": "heat",
                                    "dynamic_variation_degraded": True,
                                    "degradation_reason": "gone"})

        self.assertNotIn("degraded", rendered)
        self.assertNotIn("gone", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
