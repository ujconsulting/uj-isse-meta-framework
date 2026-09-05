#!/usr/bin/env python3
"""The Cognitive Diversity Explorer could not open a single run on this machine.

CLAUDE.md calls it the flagship feature and "fully operational and battle-tested".
Measured on 05.09.2026: not one run directory under data/output contained a
cognitive_diversity_index.json, and every attempt to build one failed.

Two causes, both about text encoding, both invisible in the error they produced:

1. `cognitive_diversity_extractor.py` printed a checkmark emoji. Run by hand its
   output is a TTY, which copes; app.py runs it with capture_output=True, so the
   stream is a pipe and Windows falls back to cp1252, where the emoji raises
   UnicodeEncodeError. That print sits BEFORE save_index, so the index was never
   written. The error handler then crashed as well, printing a cross. app.py
   reported "Cognitive diversity extraction failed" with a traceback about a
   checkmark, which reads like a formatting complaint and was in fact the feature
   being off.

   The identical guard has been at the top of main.py since this branch began, with
   a comment describing this exact failure. The file app.py actually pipes never
   got it.

2. `launch_cognitive_explorer.py` opened files without naming an encoding, so the
   platform default applied. The explorer template is full of framework emoji and
   failed to decode at byte 20231; the route caught it and returned 500.

These tests run the extractor the way app.py does -- a subprocess with its output
captured -- because that is the condition that broke it. A test that merely
imported the module would have passed throughout.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

RESPONSE = """# Response

**Model:** or_claude_sonnet_5
**Framework:** integrative
**Domain:** dynamic Urban Planning

The answer, at some length, so the extractor has something to measure. It mentions
Kubernetes and a 30% reduction and three weeks, which is the kind of concrete
detail the scoring looks for.
"""


class TestTheExtractorSurvivesAPipe(unittest.TestCase):

    def setUp(self):
        self.run_dir = Path(tempfile.mkdtemp()) / "run_20260905_120000"
        raw = self.run_dir / "raw_responses"
        raw.mkdir(parents=True)
        for i in range(2):
            (raw / f"0{i + 1}_or_claude_sonnet_5_ins_integrative.md").write_text(
                RESPONSE, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.run_dir.parent, ignore_errors=True)

    def test_it_exits_cleanly_with_its_output_captured(self):
        """capture_output=True is exactly how app.py invokes it."""
        completed = subprocess.run(
            [sys.executable, str(REPO / "cognitive_diversity_extractor.py"),
             str(self.run_dir)],
            capture_output=True, text=True, cwd=str(REPO), timeout=300)

        self.assertEqual(
            completed.returncode, 0,
            "the extractor failed when its output was a pipe:\n"
            f"{completed.stderr[-2000:]}")

    def test_the_index_is_actually_written(self):
        """The crash landed before save_index, so a clean exit is not enough."""
        subprocess.run(
            [sys.executable, str(REPO / "cognitive_diversity_extractor.py"),
             str(self.run_dir)],
            capture_output=True, text=True, cwd=str(REPO), timeout=300)

        index = self.run_dir / "cognitive_diversity_index.json"
        self.assertTrue(index.is_file(), "no index file was written")

        data = json.loads(index.read_text(encoding="utf-8"))
        self.assertEqual(len(data["responses"]), 2,
                         "the index does not describe the responses on disk")


class TestTheExplorerFilesNameTheirEncoding(unittest.TestCase):
    """A decode of the emoji-laden template under cp1252 is what returned 500."""

    def test_no_bare_open_in_the_launcher(self):
        source = (REPO / "launch_cognitive_explorer.py").read_text(encoding="utf-8")

        offenders = [
            line.strip() for line in source.splitlines()
            if "open(" in line and "encoding=" not in line
            and not line.strip().startswith("#")
            and "webbrowser.open" not in line
        ]

        self.assertEqual(
            offenders, [],
            "a file is opened without an encoding, which uses the platform "
            f"default: {offenders}")


if __name__ == "__main__":
    unittest.main()
