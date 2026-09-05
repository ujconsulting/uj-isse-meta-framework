#!/usr/bin/env python3
"""Constructing the application is not the same as starting a run.

ISEEApplication.__init__ created its run directory immediately. Several callers
only ever construct the object: /api/preview-queries builds a whole application to
show the user which questions would be asked, and `--list-domains` builds one to
read the domain list. Each of those left an empty directory behind.

Counted on 05.09.2026: 724 empty run directories under data/output, 264 of them
from the previous two hours, and the newest timestamped to the second in which a
test had merely imported the module. They were deleted; three of them were not
preview leftovers but real web runs whose subprocess died before writing anything,
and after deletion those are indistinguishable.

Which is the second reason this matters. An empty directory from a preview and an
empty directory from a run that failed before its first call look exactly alike, so
the archive cannot tell the truth about either. Not creating the directory until
something is written makes an empty one mean one thing again.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import ISEEApplication, update_latest_symlink


class TestConstructionWritesNothing(unittest.TestCase):

    def setUp(self):
        self.previous = os.getcwd()
        self.root = tempfile.mkdtemp()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.previous)
        shutil.rmtree(self.root, ignore_errors=True)

    def test_constructing_leaves_no_run_directory(self):
        application = ISEEApplication()
        self.assertFalse(
            os.path.exists(application.run_output_dir),
            "constructing the application created a run directory; a preview is "
            "not a run")
        self.assertEqual(
            [p for p in Path("data/output").rglob("run_*")], [],
            "something under data/output was created by construction alone")

    def test_the_directory_appears_when_it_is_needed(self):
        application = ISEEApplication()
        returned = application.ensure_output_directory()

        self.assertTrue(os.path.isdir(application.run_output_dir))
        self.assertEqual(returned, application.run_output_dir)

    def test_ensuring_twice_is_harmless(self):
        """Every writer calls it, so it is called many times per run."""
        application = ISEEApplication()
        first = application.ensure_output_directory()
        (Path(first) / "written.md").write_text("kept", encoding="utf-8")

        application.ensure_output_directory()

        self.assertEqual((Path(first) / "written.md").read_text(encoding="utf-8"),
                         "kept", "a second call must not disturb the directory")


class TestTheLatestPointerNamesSomethingThatExists(unittest.TestCase):
    """The pointer compared paths as strings, and the two sides were built with
    different separators: os.path.join gives "data\\output" on Windows while the run
    directory is assembled by f-string as "data/output/2026-09/...". The test was
    therefore False for every command-line run and the pointer recorded a bare
    basename -- naming data/output/run_X for a run that lives in
    data/output/2026-09/week1/run_X.

    Measured on 05.09.2026: latest.txt named a path that did not exist. A pointer to
    a missing directory is worse than no pointer, because every reader of it fails
    somewhere else, far from the cause.
    """

    def setUp(self):
        self.previous = os.getcwd()
        self.root = tempfile.mkdtemp()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.previous)
        shutil.rmtree(self.root, ignore_errors=True)

    def test_a_nested_run_is_recorded_with_its_whole_path(self):
        run = "data/output/2026-09/week1/run_20260905_124411"
        os.makedirs(run)

        update_latest_symlink(run)

        recorded = Path("data/output/latest.txt").read_text(encoding="utf-8").strip()
        self.assertTrue(
            Path("data/output", recorded).is_dir(),
            f"latest.txt records {recorded!r}, which is not a directory")

    def test_a_flat_run_is_recorded_too(self):
        run = "data/output/run_20260905_124411"
        os.makedirs(run)

        update_latest_symlink(run)

        recorded = Path("data/output/latest.txt").read_text(encoding="utf-8").strip()
        self.assertEqual(recorded, "run_20260905_124411")
        self.assertTrue(Path("data/output", recorded).is_dir())


if __name__ == "__main__":
    unittest.main()
