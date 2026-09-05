#!/usr/bin/env python3
"""Recording which run was the most recent one.

This was a symlink, created by deleting the old one and then making a new one.
Two defects, both real:

* `os.symlink` needs a privilege an ordinary Windows account does not have. It
  raised WinError 1314 on every run and printed a warning nobody could act on, so
  `data/output/latest` never existed on this machine at all.
* Delete-then-create is a race: two runs finishing together could leave no pointer,
  or one aimed at the earlier run.

Nothing in the repository reads it — checked across source, scripts and docs. It is
kept because "which run was last" is a fair question, and a text file answers it on
any platform and after the directory has been copied elsewhere.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import update_latest_symlink


class TestLatestPointer(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        self.previous = os.getcwd()
        os.chdir(self.work)
        self.output = os.path.join("data", "output")
        self.pointer = os.path.join(self.output, "latest.txt")

    def tearDown(self):
        os.chdir(self.previous)
        shutil.rmtree(self.work, ignore_errors=True)

    def record(self, name):
        run = os.path.join(self.output, name)
        os.makedirs(run, exist_ok=True)
        update_latest_symlink(run)
        return run

    def read(self):
        with io.open(self.pointer, encoding="utf-8") as fh:
            return fh.read().strip()

    def test_the_pointer_names_the_run(self):
        self.record("run_20260904_010203")

        self.assertTrue(os.path.exists(self.pointer))
        self.assertEqual(self.read(), "run_20260904_010203")

    def test_a_later_run_replaces_the_earlier_one(self):
        self.record("run_20260904_010203")
        self.record("run_20260904_010500")

        self.assertEqual(self.read(), "run_20260904_010500")

    def test_no_temporary_file_is_left_behind(self):
        # The write goes to a neighbouring file and is renamed over the target, so
        # a reader sees either the old pointer or the new one and never a partial
        # write. The temporary must not survive.
        self.record("run_20260904_010203")

        leftovers = [f for f in os.listdir(self.output) if f.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_it_needs_no_special_privilege(self):
        # The whole point: this must work on an account that cannot create symlinks.
        self.record("run_20260904_010203")

        self.assertFalse(os.path.islink(self.pointer))
        self.assertTrue(os.path.isfile(self.pointer))

    def test_a_failure_to_record_does_not_raise(self):
        # A run that produced its results has succeeded whether or not this
        # convenience file could be written.
        os.makedirs(self.output, exist_ok=True)
        os.makedirs(self.pointer, exist_ok=True)   # a directory where the file goes

        update_latest_symlink(os.path.join(self.output, "run_20260904_010203"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
