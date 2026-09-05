#!/usr/bin/env python3
"""An execution id nobody can resolve must be answered as unresolvable.

Three routes did the opposite. When the id did not resolve, each walked
`data/output` and returned whichever run was newest and non-empty. Measured
against the running application on 05.09.2026 with the invented id
`exec_erfunden`, before anything was changed:

    /api/download-zip/exec_erfunden    HTTP 200  160,854 bytes
    /api/markdown/exec_erfunden        HTTP 200   19,400 bytes
    /api/query-details/exec_erfunden   HTTP 200   13,156 bytes

The security reading — a caller learns the contents of runs whose ids they never
knew — is the smaller half. The plainer problem is correctness: on a machine with
a single user, "download my results" could hand back a DIFFERENT run's results,
with a 200 and no warning. Somebody comparing two runs would have no way to tell
they were reading the same one twice.

The case the fallback was written for is real: run status lives in a per-process
dictionary, so a server restart makes every earlier id unresolvable. But an
arbitrary substitute is not recovery. It is a wrong answer wearing a right
answer's clothes — the shape this repository keeps producing.

`/api/query-details` hid it best. Its own search list ended with

    f"data/output/run_*/queries_detailed_*.csv",   # matches every run
    f"data/output/queries_detailed_*.csv"          # matches every file

followed by `max(matches, key=mtime)`, so it looked like a search and behaved
like a default.
"""

import os
import shutil
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

BAIT = "MUST-NOT-BE-SERVED-FOR-AN-UNKNOWN-ID"
INVENTED = "exec_erfunden_0000000000"


class TestUnknownExecutionId(unittest.TestCase):
    """A newest, richest, most tempting run exists — and stays unreachable."""

    def setUp(self):
        self.client = app.test_client()
        # The bait is deliberately the newest thing in data/output, because
        # "newest" is exactly what the removed fallbacks selected on.
        self.run_dir = Path("data/output") / "run_20260905_235959_bait"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "isee_result.md").write_text(BAIT, encoding="utf-8")
        (self.run_dir / "queries_detailed_20260905_235959.csv").write_text(
            f"query,model\n{BAIT},x\n", encoding="utf-8")
        now = time.time()
        for p in self.run_dir.rglob("*"):
            os.utime(p, (now, now))

    def tearDown(self):
        shutil.rmtree(self.run_dir, ignore_errors=True)

    def test_no_route_substitutes_another_run(self):
        for route in ("/api/download-zip", "/api/markdown", "/api/query-details"):
            with self.subTest(route=route):
                response = self.client.get(f"{route}/{INVENTED}")
                body = response.get_data()
                self.assertNotIn(BAIT.encode(), body,
                                 f"{route} served an unrelated run's contents")
                self.assertEqual(
                    response.status_code, 404,
                    f"{route} answered {response.status_code} for an id it "
                    f"cannot resolve; unresolvable must read as unresolvable")

    def test_query_details_searches_only_for_the_id_it_was_given(self):
        """Guards the specific regression: a pattern that matches everything."""
        import inspect

        import app as app_module

        source = inspect.getsource(app_module.api_query_details)
        patterns = [line for line in source.splitlines()
                    if "queries_detailed_" in line and 'f"data/output' in line]
        self.assertTrue(patterns, "search patterns not found — did the route move?")
        for pattern in patterns:
            self.assertIn(
                "{execution_id}", pattern,
                "a search pattern without the execution id in it matches other "
                f"runs and turns the search into a default: {pattern.strip()}")


if __name__ == "__main__":
    unittest.main()
