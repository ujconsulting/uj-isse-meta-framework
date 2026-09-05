#!/usr/bin/env python3
"""Starting an analysis spends the owner's money, so something has to count them.

Nothing did. `/api/execute` accepted every POST it received and launched a
subprocess for each; a hundred requests meant a hundred runs at roughly $0.31
apiece. The exposure review of 05.09.2026 filed this against a route that is
unauthenticated by design and binds 0.0.0.0 -- so the money is protected here or
it is not protected at all.

The limits are deliberately generous: ordinary use never meets them, and both are
env-overridable. The point is that a ceiling exists, not where it sits.

Also pinned here: the execution id. It was `exec_<unix seconds>`, which collides
whenever two runs start in the same second -- the second overwrites the first's
status entry, and each then reports the other's progress. That is a correctness
bug before it is a security one; the same change fixes both.
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from app import app, demo


class TestTheCeiling(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        app_module._run_starts[:] = []
        self.saved_status = dict(demo.execution_status)
        demo.execution_status.clear()
        # Never actually launch anything: the thread would spawn a real subprocess
        # and, with API keys present, spend real money in a test run.
        self.thread = mock.patch("app.threading.Thread").start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        demo.execution_status.clear()
        demo.execution_status.update(self.saved_status)
        app_module._run_starts[:] = []

    def start(self):
        return self.client.post("/api/execute", json={"query": "q"})

    def test_a_normal_start_is_allowed(self):
        response = self.start()
        self.assertEqual(response.status_code, 200)
        self.assertIn("execution_id", response.get_json())

    def test_the_hourly_limit_refuses_the_one_too_many(self):
        allowed = app_module.MAX_RUNS_PER_HOUR
        for i in range(allowed):
            self.assertEqual(self.start().status_code, 200, f"start {i + 1} refused")

        refused = self.start()
        self.assertEqual(refused.status_code, 429)
        self.assertIn("last hour", refused.get_json()["error"])

    def test_concurrent_runs_are_capped(self):
        for i in range(app_module.MAX_CONCURRENT_RUNS):
            demo.execution_status[f"exec_fake_{i}"] = {"status": "running"}

        refused = self.start()

        self.assertEqual(refused.status_code, 429)
        self.assertIn("already running", refused.get_json()["error"])

    def test_a_finished_run_does_not_occupy_a_slot(self):
        for i in range(app_module.MAX_CONCURRENT_RUNS):
            demo.execution_status[f"exec_done_{i}"] = {"status": "completed"}

        self.assertEqual(self.start().status_code, 200)

    def test_a_refused_start_does_not_consume_an_hourly_slot(self):
        """Otherwise a burst against the concurrency cap would eat the hour."""
        for i in range(app_module.MAX_CONCURRENT_RUNS):
            demo.execution_status[f"exec_fake_{i}"] = {"status": "running"}
        for _ in range(5):
            self.assertEqual(self.start().status_code, 429)

        demo.execution_status.clear()

        self.assertEqual(self.start().status_code, 200)

    def test_a_body_that_is_not_an_object_is_refused_before_anything_starts(self):
        response = self.client.post("/api/execute", json=None,
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(app_module._run_starts, [],
                         "a rejected request must not count against the hour")


class TestTheExecutionId(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        app_module._run_starts[:] = []
        mock.patch("app.threading.Thread").start()
        self.addCleanup(mock.patch.stopall)
        self.addCleanup(lambda: app_module._run_starts.clear())

    def test_two_starts_in_the_same_second_get_different_ids(self):
        first = self.client.post("/api/execute", json={"query": "q"}).get_json()
        second = self.client.post("/api/execute", json={"query": "q"}).get_json()

        self.assertNotEqual(first["execution_id"], second["execution_id"],
                            "ids collide, so one run overwrites the other's status")

    def test_the_id_is_not_derivable_from_the_clock(self):
        import time

        identifier = self.client.post(
            "/api/execute", json={"query": "q"}).get_json()["execution_id"]

        self.assertNotEqual(identifier, f"exec_{int(time.time())}")
        self.assertRegex(identifier, r"^exec_\d+_[0-9a-f]{8}$")


if __name__ == "__main__":
    unittest.main()
