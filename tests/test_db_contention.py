#!/usr/bin/env python3
"""Two writers must not lose data to a lock.

Both trackers open a connection per operation, so `check_same_thread` was never a
problem — but sqlite's default wait for a busy database is short, and the loser of
a race gets `sqlite3.OperationalError: database is locked`. Ingest failures are
already tolerated further up, so that loss is silent: the run finishes, the
performance row is simply absent.

This matters more from here on. The web interface is moving to calling the engine
in-process, so a run's ingest and a request handler can reach the same file at the
same time (docs/plans/2026-09-03-engine-naht.md, risk R9).

Written against disposable databases, never the real ones — a contention test that
writes to `data/*.db` would corrupt the very history it is testing.
"""

import os
import sqlite3
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import enhancement_tracking
import performance_tracker


class TestBusyTimeoutIsSet(unittest.TestCase):
    def test_both_modules_declare_a_wait(self):
        for module in (performance_tracker, enhancement_tracking):
            with self.subTest(module=module.__name__):
                self.assertGreaterEqual(module.DB_BUSY_TIMEOUT_SECONDS, 5)

    def test_no_connection_is_opened_without_one(self):
        import io
        import re

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name in ("performance_tracker.py", "enhancement_tracking.py"):
            with io.open(os.path.join(root, name), encoding="utf-8") as fh:
                source = fh.read()
            calls = re.findall(r"sqlite3\.connect\([^)]*\)", source)
            self.assertTrue(calls, f"{name} opens no connection at all any more?")
            without = [c for c in calls if "timeout=" not in c]
            self.assertEqual(without, [], f"{name}: {len(without)} connection(s) with no wait")


class TestConcurrentWriters(unittest.TestCase):
    """The behaviour the timeout exists for, against a throwaway database."""

    def write_from_threads(self, db_path, timeout):
        errors = []
        start = threading.Barrier(2)

        def writer(tag):
            # The connection is closed in `finally` even when the write is refused.
            # On Windows an open sqlite handle keeps the temporary directory alive,
            # and the test then fails on cleanup instead of on its own assertion —
            # which is what happened the first time this was written.
            conn = None
            try:
                start.wait(timeout=10)
                conn = sqlite3.connect(db_path, timeout=timeout)
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("INSERT INTO t (who) VALUES (?)", (tag,))
                import time
                time.sleep(0.3)          # hold the write lock long enough to collide
                conn.commit()
            except Exception as exc:  # noqa: BLE001 — the exception IS the result
                errors.append(f"{tag}: {exc}")
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

        threads = [threading.Thread(target=writer, args=(f"w{i}",)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        return errors

    def test_a_second_writer_waits_instead_of_losing_its_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "contention.db")
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE t (who TEXT)")
            conn.commit()
            conn.close()

            errors = self.write_from_threads(db, performance_tracker.DB_BUSY_TIMEOUT_SECONDS)

            self.assertEqual(errors, [], "a writer was refused despite the wait")
            conn = sqlite3.connect(db)
            rows = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            conn.close()
            self.assertEqual(rows, 2, "a row was lost to the lock")

    def test_without_a_wait_the_row_really_would_be_lost(self):
        # Guards the test itself: if this passes with timeout=0, the scenario above
        # proves nothing, because there was never any contention to survive.
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "contention.db")
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE t (who TEXT)")
            conn.commit()
            conn.close()

            errors = self.write_from_threads(db, 0)

            self.assertTrue(errors, "no contention occurred — the other test is vacuous")
            self.assertIn("locked", errors[0].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
