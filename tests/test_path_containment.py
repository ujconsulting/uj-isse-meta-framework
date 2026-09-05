#!/usr/bin/env python3
"""Two routes serve files from disk. Neither may serve a file from anywhere else.

Found by an exposure review of app.py on 05.09.2026 and confirmed against the
running application before anything was changed.

`/api/raw-response` rejected only ".." and a leading "/". An absolute Windows path
contains neither, and `os.path.join` discards everything before an absolute second
argument — so the run directory vanished and the file was read and returned. A bait
file outside data/output came back HTTP 200 with its contents.

`/api/download-file` resolved paths properly and then compared them as strings with
`startswith`, so a sibling whose name merely begins with the allowed one —
"data/output_backup" beside "data/output" — passed containment.

Both matter more than "it is a local tool" suggests: a service on localhost is
reachable from any page the browser visits, and this one sets no CORS policy and
validates no Host header.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import ISEEWebDemo, app
from pathlib import Path

BAIT = "CONFIDENTIAL-MUST-NOT-BE-SERVED"


class TestResolveInside(unittest.TestCase):
    """The helper both routes now use."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        (self.base / "inside.txt").write_text("ok", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_a_path_inside_resolves(self):
        resolved = ISEEWebDemo.resolve_inside(self.base, "inside.txt")

        self.assertTrue(str(resolved).endswith("inside.txt"))

    def test_a_parent_traversal_is_refused(self):
        with self.assertRaises(ValueError):
            ISEEWebDemo.resolve_inside(self.base, "..", "outside.txt")

    def test_an_absolute_path_is_refused(self):
        outside = Path(tempfile.mkdtemp()) / "secret.txt"

        with self.assertRaises(ValueError):
            ISEEWebDemo.resolve_inside(self.base, str(outside))

    def test_a_sibling_with_a_matching_prefix_is_refused(self):
        # The exact shape that defeated the startswith comparison.
        sibling = self.base.parent / (self.base.name + "_backup")
        sibling.mkdir(exist_ok=True)
        try:
            with self.assertRaises(ValueError):
                ISEEWebDemo.resolve_inside(self.base, str(sibling / "secret.txt"))
        finally:
            shutil.rmtree(sibling, ignore_errors=True)


class TestRawResponseRoute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.elsewhere = tempfile.mkdtemp()
        self.bait = os.path.join(self.elsewhere, "secret.txt")
        io.open(self.bait, "w", encoding="utf-8").write(BAIT)

    def tearDown(self):
        shutil.rmtree(self.elsewhere, ignore_errors=True)

    def test_an_absolute_path_does_not_reach_the_file(self):
        response = self.client.get(
            f"/api/raw-response/run_20260101_000000?file={self.bait}")

        self.assertNotIn(BAIT, response.get_data(as_text=True))
        self.assertEqual(response.status_code, 403)

    def test_a_run_id_that_is_not_a_run_id_is_refused(self):
        response = self.client.get("/api/raw-response/anything?file=x.md")

        self.assertEqual(response.status_code, 400)

    def test_a_traversal_in_the_run_id_is_refused(self):
        # The run id used to be interpolated into the path unchecked while only
        # the file parameter was examined.
        response = self.client.get("/api/raw-response/run_20260101_000000/../..?file=x")

        self.assertNotEqual(response.status_code, 200)


class TestDownloadFileRoute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.sibling = Path("data/output_backup").resolve()
        self.sibling.mkdir(parents=True, exist_ok=True)
        (self.sibling / "secret.txt").write_text(BAIT, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.sibling, ignore_errors=True)

    def test_a_sibling_directory_is_not_inside_the_output_directory(self):
        response = self.client.get(
            f"/api/download-file?path={self.sibling / 'secret.txt'}")

        self.assertNotIn(BAIT, response.get_data(as_text=True))
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
