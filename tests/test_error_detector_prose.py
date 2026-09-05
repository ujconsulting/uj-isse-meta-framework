#!/usr/bin/env python3
"""An answer about failure is not a failed answer.

`main.py:1480` runs every model response through `APIErrorDetector.is_api_error`,
and since this branch a flagged response is recorded as a failed call — dropped
from scoring, from the synthesis and from the deliverable.

The detector counted error vocabulary by substring and treated two hits in a
response under 500 characters as proof of an API error. Measured on 03.09.2026,
that discarded:

    "A blameless post-mortem culture reduces repeat failures. When an error
     occurs, the team documents the timeout and the failed request without
     assigning blame."

which is not an error — it is the answer. This tool's critical, contrarian and
first-principles frameworks explicitly commission prose about what goes wrong, so
the heuristic was measuring the topic and calling it the outcome.

Structural detection (JSON error bodies, provider patterns, HTTP status, empty
responses) was sound and is unchanged; these tests pin both directions.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_error_detector import APIErrorDetector

LEGITIMATE = {
    "prose about organisations":
        "The organization should adopt an enterprise-wide governance model. "
        "Organizational change management is the binding constraint here, not the technology.",
    "prose about failure culture":
        "A blameless post-mortem culture reduces repeat failures. When an error occurs, "
        "the team documents the timeout and the failed request without assigning blame.",
    "a contrarian answer":
        "The premise is invalid. Every attempt to scale this failed for the same reason: "
        "the request timeout was treated as a symptom, not the constraint it is.",
    "a German answer about outages":
        "Der haeufigste Fehler ist die Annahme, ein Timeout sei ein Netzproblem. "
        "Tatsaechlich scheitert die Anfrage meist an einer ungueltigen Konfiguration.",
}

REAL_ERRORS = {
    "a JSON error body": '{"error": {"message": "invalid api key", "code": 401}}',
    "a terse error line": "Error: unauthorized",
    "two error words, no known pattern": "invalid credentials, request failed",
    "a provider's own message": "Invalid organization credentials",
    "an HTTP status": "HTTP 503 Service unavailable",
    "nothing at all": "",
}


class TestLegitimateAnswersSurvive(unittest.TestCase):
    def setUp(self):
        self.detector = APIErrorDetector()

    def test_prose_is_never_judged_by_its_vocabulary(self):
        for label, text in LEGITIMATE.items():
            with self.subTest(answer=label):
                is_error, reason = self.detector.is_api_error(text)
                self.assertFalse(is_error, f"{label} was discarded as an API error: {reason}")

    def test_organisation_and_enterprise_are_not_error_terms(self):
        # They were listed as "Globant-specific error indicators". Globant's actual
        # error strings have their own whole-phrase patterns; these two words alone
        # are ordinary business vocabulary.
        self.assertNotIn("organization", self.detector.error_indicators)
        self.assertNotIn("enterprise", self.detector.error_indicators)

    def test_a_word_is_matched_whole_not_as_a_fragment(self):
        # "organizational" used to count as "organization", "errors" as "error".
        self.assertTrue(self.detector._reads_as_prose(LEGITIMATE["prose about organisations"]))
        matched = [p.pattern for p in self.detector._indicator_patterns
                   if p.search("organizational restructuring")]
        self.assertEqual(matched, [])


class TestRealErrorsAreStillCaught(unittest.TestCase):
    def setUp(self):
        self.detector = APIErrorDetector()

    def test_every_known_error_shape_is_recognised(self):
        for label, text in REAL_ERRORS.items():
            with self.subTest(error=label):
                is_error, _ = self.detector.is_api_error(text)
                self.assertTrue(is_error, f"{label} slipped through as legitimate content")

    def test_a_short_fragment_is_not_treated_as_prose(self):
        self.assertFalse(self.detector._reads_as_prose("Error: unauthorized"))
        self.assertFalse(self.detector._reads_as_prose('{"error": "nope"}'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
