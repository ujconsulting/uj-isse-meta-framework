#!/usr/bin/env python3
"""A requested zero is a request, not an absence.

The command builder tested numeric parameters for truthiness:

    if converted_params.get("variations"):
        cmd.extend(["--variations", str(...)])

so an explicitly requested 0 was dropped exactly as a missing key is, and argparse
fell back to its own default of 2. Asking for no query variations produced two of
them — three queries instead of one, and the paid model calls that go with them.
The opposite of what was asked, and nothing said so.

Found on 05.09.2026 while inventorying the parameters that cross the web-to-engine
seam, which is the same seam that produced the domain defect two days earlier.
"""

import inspect
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import ISEEWebDemo


class TestNumericParametersAreNotTestedForTruthiness(unittest.TestCase):
    """Read on the source, because building the command needs a live subprocess."""

    def setUp(self):
        self.source = inspect.getsource(ISEEWebDemo.execute_isee_command)

    def test_a_variations_count_of_zero_still_reaches_the_engine(self):
        self.assertIn('get("variations") is not None', self.source)

    def test_a_max_combinations_of_zero_still_reaches_the_engine(self):
        self.assertIn('get("max_combinations") is not None', self.source)

    def test_no_numeric_flag_is_gated_on_truthiness_any_more(self):
        # The class, not the two instances: any future numeric parameter added with
        # a bare truthiness check would silently drop a legitimate zero.
        numeric = ("variations", "max_combinations", "models", "instructions",
                   "max_workers", "max_tokens")
        for name in numeric:
            with self.subTest(parameter=name):
                bare = re.search(rf'if converted_params\.get\("{name}"\):', self.source)
                self.assertIsNone(
                    bare,
                    f"{name} is gated on truthiness, so a requested 0 is dropped")


if __name__ == "__main__":
    unittest.main(verbosity=2)
