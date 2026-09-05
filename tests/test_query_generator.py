#!/usr/bin/env python3
"""Tests for query_generator.py, the module that builds every prompt variation that
goes out in a paid model call.

Guards four findings from docs/audit/2026-09-03-baseline.md (section "query_generator.py"):

- finding 5: a failure in the dynamic variation system used to be caught, logged, and
  silently replaced with static generation — the run then proceeded on materially
  different prompts while looking successful.
- finding 4: generate_variations(count=N) documents N as a guarantee, but duplicate
  elimination plus an attempt cap could silently return fewer.
- finding 7: _rephrase_question() lowercased the entire question before splicing it
  into the next prompt, corrupting acronyms and identifiers ahead of a paid call.
- finding 9: the constraint/context strategies appended ", ...?" even when the base
  question already ended in "?", producing "...?, within a tight budget?".

Nothing here makes a network call, needs an API key, or costs money.
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_generator import Query, QueryGenerator  # noqa: E402


def _make_generator(use_dynamic_variations: bool = False) -> QueryGenerator:
    """A generator with a fixed base query, dynamic system off unless requested.

    Dynamic variations call out to dynamic_query_variation.DynamicQueryVariator, which
    would make a real HTTP request if it ever got past the (missing) API key check.
    Tests that need the dynamic path stub it out explicitly instead of relying on that
    check; tests that don't care use the static path so nothing network-shaped is even
    constructed.
    """
    generator = QueryGenerator(use_dynamic_variations=use_dynamic_variations)
    generator.add_base_query(Query(id="q1", text="How might we scale the ACME API?"))
    return generator


class TestDynamicFallbackIsVisible(unittest.TestCase):
    """Finding 5: a dynamic-variation failure must not look like a clean success."""

    def test_a_dynamic_failure_is_recorded_on_the_generator_report(self):
        generator = _make_generator(use_dynamic_variations=True)
        # DYNAMIC_VARIATIONS_AVAILABLE may be False in an environment without the
        # optional module; force the dynamic path on regardless, since the point of
        # this test is what happens when that path raises, not whether it is present.
        generator.use_dynamic_variations = True
        generator.dynamic_variator = object()  # any truthy stand-in
        with patch.object(
            QueryGenerator, "_create_dynamic_variations",
            side_effect=RuntimeError("analysis model returned 404"),
        ):
            generator.generate_variations("q1", count=2)

        report = generator.last_generation_report
        self.assertIsNotNone(report, "generate_variations must record what happened")
        self.assertTrue(report["degraded_to_static"],
                        "a caught dynamic-variation exception must be reported as a degradation")
        self.assertFalse(report["used_dynamic_variations"])
        self.assertIn("404", report["degradation_reason"])

    def test_a_dynamic_failure_is_stamped_onto_every_returned_query(self):
        """Not just a log line: the flag must survive into what the caller keeps.

        main.py spreads Query.variables into every combination dict it builds
        (main.py:1443, 1631), so stamping it here is what makes the degradation visible
        downstream in the run's own output, not only to someone reading the log.
        """
        generator = _make_generator(use_dynamic_variations=True)
        generator.use_dynamic_variations = True
        generator.dynamic_variator = object()
        with patch.object(
            QueryGenerator, "_create_dynamic_variations",
            side_effect=RuntimeError("boom"),
        ):
            variations = generator.generate_variations("q1", count=2)

        self.assertTrue(variations, "the static fallback must still produce variations")
        for variation in variations:
            self.assertTrue(variation.variables.get("dynamic_variation_degraded"))
            self.assertEqual(variation.variables.get("degradation_reason"), "boom")

    def test_a_clean_dynamic_success_is_not_flagged_as_degraded(self):
        """The flag must be specific to an actual fallback, not always-on noise."""
        generator = _make_generator(use_dynamic_variations=True)
        generator.use_dynamic_variations = True
        generator.dynamic_variator = object()
        fake_variation = Query(id="q1_dyn_1", text="A dynamically produced variation?")
        with patch.object(
            QueryGenerator, "_create_dynamic_variations", return_value=[fake_variation],
        ):
            variations = generator.generate_variations("q1", count=1)

        self.assertTrue(generator.last_generation_report["used_dynamic_variations"])
        self.assertFalse(generator.last_generation_report["degraded_to_static"])
        self.assertNotIn("dynamic_variation_degraded", variations[0].variables)


class TestShortfallIsReported(unittest.TestCase):
    """Finding 4: generate_variations(count=N) must not silently under-deliver."""

    def test_a_duplicate_exhausted_run_reports_its_shortfall(self):
        """Force every strategy attempt to produce the identical text.

        Patching random.choice to always return the first element of whatever
        sequence it is given makes _create_variations pick the same strategy and the
        same option every time, so only the first attempt is unique — the rest are
        duplicates the dedup logic discards. This deterministically reproduces the
        under-delivery the audit flagged, without relying on genuine bad luck.
        """
        generator = _make_generator(use_dynamic_variations=False)

        with patch("query_generator.random.choice", side_effect=lambda seq: seq[0]):
            with self.assertLogs("query_generator", level="WARNING") as logs:
                variations = generator.generate_variations("q1", count=5)

        self.assertEqual(len(variations), 1,
                         "identical attempts must collapse to exactly one unique variation")
        report = generator.last_generation_report
        self.assertEqual(report["requested_count"], 5)
        self.assertEqual(report["returned_count"], 1)
        self.assertEqual(report["shortfall"], 4)
        self.assertTrue(any("shortfall" in line for line in logs.output),
                        "the shortfall must be logged explicitly, not just computable")

    def test_a_fully_satisfied_request_reports_no_shortfall(self):
        generator = _make_generator(use_dynamic_variations=False)
        variations = generator.generate_variations("q1", count=3)
        self.assertEqual(len(variations), 3)
        self.assertEqual(generator.last_generation_report["shortfall"], 0)


class TestRephrasingPreservesCase(unittest.TestCase):
    """Finding 7: acronyms and identifiers must survive _rephrase_question."""

    def test_an_acronym_survives_rephrasing(self):
        generator = _make_generator()
        query = Query(id="q1", text="How might we integrate the ACME API with GDPR compliance?")

        rephrased = generator._rephrase_question(query)

        self.assertIn("ACME", rephrased.text)
        self.assertIn("API", rephrased.text)
        self.assertIn("GDPR", rephrased.text)
        self.assertNotIn("acme", rephrased.text)

    def test_the_recognized_lead_in_is_still_swapped(self):
        """The fix must not just skip rephrasing — the substitution still has to happen."""
        generator = _make_generator()
        query = Query(id="q1", text="How might we reduce churn?")

        rephrased = generator._rephrase_question(query)

        self.assertTrue(rephrased.text.startswith("What are effective ways to"))
        self.assertIn("reduce churn", rephrased.text)

    def test_a_lowercase_lead_in_is_still_matched(self):
        """Detection must stay case-insensitive even though the output is not lowered."""
        generator = _make_generator()
        query = Query(id="q1", text="how might we reduce churn for the EU market?")

        rephrased = generator._rephrase_question(query)

        self.assertTrue(rephrased.text.lower().startswith("what are effective ways to"))
        self.assertIn("EU", rephrased.text)


class TestConstraintAndContextPunctuation(unittest.TestCase):
    """Finding 9: no second question mark bolted onto an already-terminated question."""

    def test_a_question_mark_terminated_base_query_gets_no_double_question_mark_from_constraints(self):
        generator = _make_generator()
        query = Query(id="q1", text="How might we scale the ACME API on a tight budget?")

        variation = generator._add_constraints(query)

        self.assertNotIn("?,", variation.text)
        self.assertEqual(variation.text.count("?"), 1)

    def test_a_question_mark_terminated_base_query_gets_no_double_question_mark_from_context(self):
        generator = _make_generator()
        query = Query(id="q1", text="How might we scale the ACME API on a tight budget?")

        variation = generator._add_context(query)

        self.assertNotIn("?,", variation.text)
        self.assertEqual(variation.text.count("?"), 1)

    def test_a_base_query_without_terminal_punctuation_is_untouched(self):
        generator = _make_generator()
        query = Query(id="q1", text="How might we scale the ACME API")

        variation = generator._add_constraints(query)

        self.assertTrue(variation.text.startswith("How might we scale the ACME API, "))


if __name__ == "__main__":
    unittest.main(verbosity=2)
