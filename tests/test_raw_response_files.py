#!/usr/bin/env python3
"""Every response a run receives has to survive as a readable file.

A combination id carries its domain, and a dynamic domain puts a colon into it
("…_dynamic:Energy Efficiency Engineering"). On NTFS a colon in a path does not
raise — it addresses an *alternate data stream*. So `open(path, "w")` wrote the
answer into a hidden stream and left a visible 0-byte file behind.

Measured on 03.09.2026 against a real run: 11 of 11 files in `raw_responses/`
were 0 bytes, with one holding 3,651 bytes in a stream named
`Sustainable IT Infrastructure_or_claude_sonnet_5_ins_creative.md`. Nothing
reads those: not the diversity explorer, not the ZIP export, and nothing at all
once the run is copied off NTFS.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import ISEEApplication


class TestSafeFilenamePart(unittest.TestCase):
    """The sanitiser itself.

    Imported per-test rather than at module scope, so that the behavioural tests
    below still run — and still fail — against a tree that has no sanitiser yet.
    """

    def setUp(self):
        from main import safe_filename_part
        self.sanitise = safe_filename_part

    def test_a_colon_never_survives(self):
        self.assertNotIn(":", self.sanitise("dynamic:Energy Systems"))

    def test_every_reserved_character_is_replaced(self):
        out = self.sanitise('a<b>c:d"e/f\\g|h?i*j')

        for ch in '<>:"/\\|?*':
            self.assertNotIn(ch, out)

    def test_readable_text_is_left_alone(self):
        self.assertEqual(self.sanitise("or_claude_sonnet_5_ins_creative"),
                         "or_claude_sonnet_5_ins_creative")

    def test_the_result_is_bounded(self):
        self.assertEqual(len(self.sanitise("x" * 500)), 120)
        self.assertEqual(len(self.sanitise("x" * 500, limit=40)), 40)

    def test_something_unusable_still_yields_a_name(self):
        self.assertEqual(self.sanitise("..."), "unnamed")
        self.assertEqual(self.sanitise(""), "unnamed")

    def test_a_trailing_dot_or_space_is_stripped(self):
        # Windows silently drops both from a filename, so a name ending in one
        # cannot be looked up again under the name it was written with.
        self.assertEqual(self.sanitise("name. "), "name")


class TestRawResponseIsWritten(unittest.TestCase):
    """The end that actually matters: bytes on disk, under a name you can list."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.app = ISEEApplication.__new__(ISEEApplication)
        self.app.output_directory = self.tmp

    def combination(self, domain="dynamic:Energy Efficiency Engineering"):
        return {"model": "or_claude_sonnet_5", "template": "ins_creative",
                "domain": domain, "query": "q"}

    def result(self, response="The full answer.", combo_id=None):
        return {
            "combination_id": combo_id or
                "or_claude_sonnet_5_ins_creative_query_223849eb_dynamic:Energy Systems",
            "response": response,
            "prompt": "the prompt",
            "metadata": {"timestamp": "2026-09-03T19:00:00", "duration": 1.0},
        }

    def written_files(self, subdir="raw_responses"):
        return sorted(Path(self.tmp, subdir).glob("*"))

    def test_the_response_reaches_the_file(self):
        self.app.save_raw_response(self.result(), self.combination())

        files = self.written_files()
        self.assertEqual(len(files), 1)
        self.assertGreater(files[0].stat().st_size, 0,
                           "the file is empty — the body went somewhere else")
        self.assertIn("The full answer.", files[0].read_text(encoding="utf-8"))

    def test_the_filename_carries_no_colon(self):
        self.app.save_raw_response(self.result(), self.combination())

        self.assertNotIn(":", self.written_files()[0].name)

    def test_the_file_ends_in_md(self):
        # The rank renaming and the diversity extractor both look for *.md; a name
        # truncated at the colon lost the extension along with the content.
        self.app.save_raw_response(self.result(), self.combination())

        self.assertEqual(self.written_files()[0].suffix, ".md")

    def test_a_failure_goes_to_the_other_directory(self):
        failed = {"combination_id": "c1:x", "response": None, "status": "failed",
                  "error": {"kind": "api_error", "message": "HTTP 500"}}

        self.app.save_raw_response(failed, self.combination())

        self.assertEqual(self.written_files("raw_responses"), [])
        failures = self.written_files("failed_responses")
        self.assertEqual(len(failures), 1)
        self.assertIn("HTTP 500", failures[0].read_text(encoding="utf-8"))

    def test_a_static_domain_still_works(self):
        self.app.save_raw_response(
            self.result(combo_id="or_x_ins_creative_query_1_technical_writing"),
            self.combination(domain="technical_writing"))

        self.assertGreater(self.written_files()[0].stat().st_size, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
