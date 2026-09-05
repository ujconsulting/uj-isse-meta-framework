"""Contract tests for evaluation_scoring.py.

Guards two defects from the 2026-09 audit (baseline findings #7 and #9):

  1. ScoringFramework.score_text() swallowed every per-criterion exception and
     substituted 0.0, so a broken scorer looked exactly like a genuinely bad response.
  2. create_default_framework()'s weights summed to 1.2, not 1.0, so the documented
     percentages (e.g. "Impact: 25%") were not the effective ones once
     calculate_weighted_score() divided by the total weight.

Both are exercised end to end via score_text() -> calculate_weighted_score(), the
exact call sequence main.py uses, so the fix is proven against the real contract
rather than against internals only.

Out of scope, deliberately: the quality-gate apparatus (score_text_with_quality_gates,
placeholder/buzzword detection, gate thresholds). That is dead code today (main.py
calls the plain score_text()) and its repair is a separate, already-reviewed plan
(docs/plans/2026-09-03-bewertung-reparieren.md). Nothing here touches it.
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation_scoring import (  # noqa: E402
    ScoringCriterion,
    ScoringFramework,
    create_default_framework,
)


def _framework_with_one_broken_criterion():
    """A minimal framework: one criterion that always works, one that always raises."""
    framework = ScoringFramework()
    framework.add_criterion(ScoringCriterion(
        name="good", description="always scores 0.8", weight=0.5,
        scoring_function=lambda text: 0.8,
    ))
    framework.add_criterion(ScoringCriterion(
        name="broken", description="always raises", weight=0.5,
        scoring_function=lambda text: 1 / 0,
    ))
    return framework


class TestFailingCriterionIsVisible(unittest.TestCase):
    """Baseline finding #7: a scorer exception must not look like a score of 0.0."""

    def test_a_failing_criterion_is_not_reported_as_a_zero_score(self):
        framework = _framework_with_one_broken_criterion()
        scores = framework.score_text("irrelevant input")
        self.assertNotEqual(scores["broken"], 0.0)
        self.assertIsNone(scores["broken"],
                          "a failed criterion must be marked absent, not scored")

    def test_a_working_criterion_alongside_a_broken_one_still_scores_normally(self):
        framework = _framework_with_one_broken_criterion()
        scores = framework.score_text("irrelevant input")
        self.assertEqual(scores["good"], 0.8)

    def test_a_failing_criterion_is_recorded_as_a_structured_error(self):
        framework = _framework_with_one_broken_criterion()
        framework.score_text("irrelevant input")
        errors = framework.get_scoring_errors()
        self.assertIn("broken", errors)
        self.assertEqual(errors["broken"]["criterion"], "broken")
        self.assertIn("ZeroDivisionError", errors["broken"]["error_type"])
        self.assertNotIn("good", errors,
                          "a criterion that scored successfully is not an error")

    def test_scoring_errors_reset_between_calls(self):
        """A criterion that failed once must not stay flagged after a call where it works."""
        framework = _framework_with_one_broken_criterion()
        framework.score_text("first call")
        self.assertIn("broken", framework.get_scoring_errors())

        framework.criteria["broken"].scoring_function = lambda text: 0.3
        framework.score_text("second call")
        self.assertEqual(framework.get_scoring_errors(), {})

    def test_weighted_score_excludes_a_failed_criterion_instead_of_treating_it_as_zero(self):
        # Same call sequence main.py uses: score_text() then calculate_weighted_score().
        framework = _framework_with_one_broken_criterion()
        scores = framework.score_text("irrelevant input")
        weighted = framework.calculate_weighted_score(scores)
        # Old behaviour: broken counted as 0.0, so (0.8*0.5 + 0.0*0.5) / 1.0 == 0.4 --
        # a scorer bug silently halved the score of a response that was never assessed
        # on that criterion at all.
        # Correct behaviour: broken is excluded and its weight drops from the
        # denominator too, so the surviving criterion is scored on its own: 0.8.
        self.assertAlmostEqual(weighted, 0.8)

    def test_calculate_weighted_score_does_not_crash_on_an_all_failed_input(self):
        framework = _framework_with_one_broken_criterion()
        scores = {"good": None, "broken": None}
        self.assertEqual(framework.calculate_weighted_score(scores), 0.0)


class TestTheMarkerIsNotNaN(unittest.TestCase):
    """Why None and not NaN, pinned so the choice cannot quietly revert.

    NaN would mark the gap just as well and mark it by lying: measured on
    03.09.2026, `sorted([0.9, nan, 0.1])` returns the list unchanged, `nan > 0.5`
    and `nan <= 0.5` are both False, and `json.dumps` emits a bare NaN, which is
    not valid JSON. Run results are written as JSON and ranked by sorting.
    """

    def test_a_failed_criterion_survives_json_serialisation(self):
        import json

        framework = _framework_with_one_broken_criterion()
        scores = framework.score_text("irrelevant input")

        encoded = json.dumps(scores, allow_nan=False)   # raises on NaN
        self.assertIsNone(json.loads(encoded)["broken"])

    def test_no_scoring_path_produces_a_nan(self):
        framework = _framework_with_one_broken_criterion()
        scores = framework.score_text("irrelevant input")

        for name, value in scores.items():
            with self.subTest(criterion=name):
                self.assertFalse(isinstance(value, float) and math.isnan(value))


class TestDefaultFrameworkWeights(unittest.TestCase):
    """Baseline finding #9: documented percentages must equal the effective ones."""

    # The weights as documented in create_default_framework()'s comments, i.e. the
    # proportions the fix must preserve -- only the common scale factor may change.
    DOCUMENTED_RAW = {
        "impact": 0.25,
        "novelty": 0.15,
        "feasibility": 0.25,
        "comprehensiveness": 0.10,
        "specificity": 0.25,
        "actionability": 0.20,
    }

    def test_default_framework_weights_sum_to_one(self):
        framework = create_default_framework()
        total = sum(framework.get_criterion_weights().values())
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_relative_proportions_between_criteria_are_unchanged(self):
        # The fix must rescale, not re-balance: every weight divided by the same
        # constant (the old total, 1.2) so each criterion's share of the total is
        # unchanged and the documented ordering survives.
        framework = create_default_framework()
        weights = framework.get_criterion_weights()
        old_total = sum(self.DOCUMENTED_RAW.values())
        for name, raw in self.DOCUMENTED_RAW.items():
            self.assertAlmostEqual(weights[name], raw / old_total, places=9,
                                    msg=f"{name} weight was not rescaled proportionally")


if __name__ == "__main__":
    unittest.main(verbosity=2)
