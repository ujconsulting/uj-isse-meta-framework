#!/usr/bin/env python3
"""Which columns of combinations.csv are averaged as scores.

The selection used to be an exclusion list: everything that is not one of ten named
columns was treated as a scoring component and averaged. That is backwards — a
column added later is a score by default — and it broke within a day.

A `status` column ("succeeded" / "failed" / "not_executed") was added on 03.09.2026
so that failed calls stop vanishing from the statistics. The next full run then died
in the analysis step:

    TypeError: Cannot perform reduction 'mean' with string dtype

after the models had been called and paid for, while writing the report. Found by
running the pipeline end to end; no unit test could have seen it, because each half
was correct on its own.

Selection is now by dtype, so a new text column is ignored rather than averaged.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

import analysis


CSV = """combination_id,model_id,model_name,instruction_id,domain_id,query_id,executed,status,response_length,execution_time,overall_score,actionability,impact
c1,or_m,Model,ins_analytical,d,q,True,succeeded,459,,0.33,0.02,0.30
c2,or_m,Model,ins_critical,d,q,True,failed,0,1.5,0.10,0.05,0.10
"""


class TestScoreColumnSelection(unittest.TestCase):
    def analyse(self, csv_text):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "combinations.csv")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(csv_text)
            analyzer = analysis.ResultAnalyzer(data_directory=tmp)
            analyzer.combinations_df = pd.read_csv(path)
            return analyzer.analyze()

    def test_a_text_column_does_not_break_the_analysis(self):
        result = self.analyse(CSV)

        self.assertIn("scoring_components", result)

    def test_a_text_column_is_not_averaged_as_a_score(self):
        result = self.analyse(CSV)

        self.assertNotIn("status", result["scoring_components"])

    def test_the_real_score_columns_are_still_averaged(self):
        result = self.analyse(CSV)

        self.assertIn("actionability", result["scoring_components"])
        self.assertIn("impact", result["scoring_components"])
        self.assertAlmostEqual(result["scoring_components"]["impact"], 0.20)

    def test_the_named_non_score_numbers_stay_excluded(self):
        # response_length and execution_time are numeric but are not scores; the
        # dtype filter must not pull them back in.
        result = self.analyse(CSV)

        for column in ("response_length", "execution_time", "overall_score"):
            with self.subTest(column=column):
                self.assertNotIn(column, result["scoring_components"])

    def test_a_future_text_column_is_also_ignored(self):
        # The point of selecting by dtype rather than by exclusion list.
        widened = CSV.replace(",impact\n", ",impact,provider_note\n")
        widened = widened.replace(",0.30\n", ",0.30,routed via gateway\n")
        widened = widened.replace(",0.10\n", ",0.10,retried once\n")

        result = self.analyse(widened)

        self.assertNotIn("provider_note", result["scoring_components"])
        self.assertIn("impact", result["scoring_components"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
