#!/usr/bin/env python3
"""Which model and which framework a report credits for a winning response.

Both report writers used to take the combination id apart on "_" and assume the
model name occupied its first two segments. Every model in the configured
portfolio has more than two — `or_claude_sonnet_5` has four — so `run_summary.md`
of a real run on 03.09.2026 read:

    1. **or_claude with Sonnet Instruction** (Score: 0.414)
    2. **or_mistral with Small Instruction** (Score: 0.400)

`or_claude` is not a configured model, and "Sonnet" is not a cognitive framework —
it is a fragment of the model's own name. The frameworks that actually produced
those answers (Integrative, Disruption) appeared nowhere. The deliverable's
central claim was wrong in every run the project ever produced.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporting import ReportingSystem

#: Shaped exactly like the ids of the run of 03.09.2026, colon and all.
COMBINATIONS = [
    {"id": "or_claude_sonnet_5_ins_integrative_query_dfed2d83_dynamic:Urban Planning",
     "model": "or_claude_sonnet_5", "template": "ins_integrative",
     "domain": "dynamic:Urban Planning"},
    {"id": "or_mistral_small_ins_disruption_query_dfed2d83_dynamic:Thermal Engineering",
     "model": "or_mistral_small", "template": "ins_disruption",
     "domain": "dynamic:Thermal Engineering"},
    {"id": "or_gpt_56_luna_ins_first_principles_query_1_technical_writing",
     "model": "or_gpt_56_luna", "template": "ins_first_principles",
     "domain": "technical_writing"},
]

MODEL_CONFIGS = {
    "or_claude_sonnet_5": {"name": "Claude Sonnet 5"},
    "or_mistral_small": {"name": "Mistral Small"},
    "or_gpt_56_luna": {"name": "GPT-5.6 Luna"},
}


class TestDescribeCombination(unittest.TestCase):
    def describe(self, combo_id, **kw):
        return ReportingSystem.describe_combination(
            combo_id, kw.get("combinations", COMBINATIONS),
            kw.get("model_configs", MODEL_CONFIGS))

    def test_a_four_part_model_id_is_not_truncated(self):
        model, framework = self.describe(COMBINATIONS[0]["id"])

        self.assertEqual(model, "Claude Sonnet 5")
        self.assertNotEqual(model, "or_claude")

    def test_the_framework_is_the_framework_not_the_model_tail(self):
        _, framework = self.describe(COMBINATIONS[0]["id"])

        self.assertEqual(framework, "Integrative")
        self.assertNotEqual(framework, "Sonnet")

    def test_every_configured_model_shape_resolves(self):
        for combo in COMBINATIONS:
            model, framework = self.describe(combo["id"])
            self.assertNotIn("unknown", model)
            self.assertNotIn("unknown", framework)
            self.assertNotIn("_", framework)

    def test_a_multi_word_framework_reads_as_words(self):
        _, framework = self.describe(COMBINATIONS[2]["id"])

        self.assertEqual(framework, "First Principles")

    def test_a_colon_in_the_domain_does_not_disturb_the_lookup(self):
        # Dynamic domains put "dynamic:<name>" into the id, and the name carries
        # spaces. Nothing about the lookup may depend on the id's shape.
        model, framework = self.describe(COMBINATIONS[1]["id"])

        self.assertEqual((model, framework), ("Mistral Small", "Disruption"))

    def test_a_model_missing_from_the_config_falls_back_to_its_id(self):
        model, framework = self.describe(COMBINATIONS[0]["id"], model_configs={})

        self.assertEqual(model, "or_claude_sonnet_5")
        self.assertEqual(framework, "Integrative")

    def test_an_unknown_combination_is_admitted_not_invented(self):
        # The old code produced a plausible-looking wrong answer for anything.
        # An attribution that cannot be made must say so.
        model, framework = self.describe("something_that_was_never_run")

        self.assertIn("unknown", model)
        self.assertIn("unknown", framework)

    def test_empty_inputs_do_not_raise(self):
        model, framework = ReportingSystem.describe_combination("x", [], None)

        self.assertIn("unknown", model)
        self.assertIn("unknown", framework)

    def test_a_combination_without_a_template_is_not_credited_to_one(self):
        combos = [{"id": "c1", "model": "or_claude_sonnet_5"}]

        model, framework = self.describe("c1", combinations=combos)

        self.assertEqual(model, "Claude Sonnet 5")
        self.assertIn("unknown", framework)


class TestNoIdParsingRemains(unittest.TestCase):
    def test_neither_report_writer_takes_the_id_apart_again(self):
        # The two writers had the same parser copied into both. A fix applied to
        # one of them only would leave the JSON summary wrong while the markdown
        # one looked right.
        import inspect

        for name in ("_generate_run_summary_markdown", "_generate_run_summary_json"):
            source = inspect.getsource(getattr(ReportingSystem, name))
            self.assertNotIn('combo_id.split("_")', source,
                             f"{name} still derives attribution from the id")


if __name__ == "__main__":
    unittest.main(verbosity=2)
