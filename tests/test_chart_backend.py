#!/usr/bin/env python3
"""Charts must render where the code actually runs.

`analysis.py` draws the run's charts. Today that happens in a subprocess, on its
main thread, where whatever backend matplotlib guesses happens to work. The web
interface is moving to calling the engine directly, and then this runs on a Flask
worker thread.

Measured on 03.09.2026: importing `matplotlib.pyplot` without choosing a backend
first and drawing from a non-main thread on this machine picks TkAgg and dies with

    RuntimeError: main thread is not in main loop
    Tcl_AsyncDelete: async handler deleted by the wrong thread

Importing through `analysis` instead selects Agg and produces all four charts.
"""

import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestChartBackend(unittest.TestCase):
    def test_importing_analysis_selects_a_headless_backend(self):
        import analysis  # noqa: F401  — the import is the thing under test
        import matplotlib

        self.assertEqual(matplotlib.get_backend().lower(), "agg")

    def test_the_backend_is_chosen_before_pyplot_is_imported(self):
        # Order is the whole point: matplotlib.use() after pyplot is imported does
        # not reliably switch an already-initialised backend.
        import io

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with io.open(os.path.join(root, "analysis.py"), encoding="utf-8") as fh:
            source = fh.read()

        use_at = source.find('matplotlib.use("Agg")')
        pyplot_at = source.find("import matplotlib.pyplot")
        self.assertGreater(use_at, -1, "the backend is not selected at all")
        self.assertGreater(pyplot_at, -1)
        self.assertLess(use_at, pyplot_at, "use() must come before the pyplot import")

    def test_a_chart_renders_from_a_worker_thread(self):
        import analysis  # noqa: F401
        import matplotlib.pyplot as plt

        outcome = {}

        def draw():
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    target = os.path.join(tmp, "chart.png")
                    fig, ax = plt.subplots()
                    ax.bar(["a", "b"], [1, 2])
                    fig.savefig(target)
                    plt.close(fig)
                    outcome["size"] = os.path.getsize(target)
            except Exception as exc:  # noqa: BLE001 — the failure is the finding
                outcome["error"] = repr(exc)

        worker = threading.Thread(target=draw, name="not-the-main-thread")
        worker.start()
        worker.join(timeout=60)

        self.assertNotIn("error", outcome, outcome.get("error", ""))
        self.assertGreater(outcome.get("size", 0), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
