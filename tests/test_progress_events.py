#!/usr/bin/env python3
"""Folding PROGRESS_JSON events into a run's status.

These exercise `ISEEWebDemo._apply_progress_event` directly. The method touches
only `execution_status` and `logger`, so the tests build a bare instance rather
than a full application — importing app.py already costs a config load, and a
constructed demo would add a rankings service and a domain manager on top.

Every case here corresponds to something that was measurably broken in the web
path: the parallel run announced itself with an event nobody listened for, the
resulting zero total was divided by, completions were looked up in a list that
had already been truncated, and an exhausted call emitted an event with no
handler at all.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def make_demo():
    """A bare ISEEWebDemo carrying just what the progress methods use."""
    import logging

    from app import ISEEWebDemo

    demo = ISEEWebDemo.__new__(ISEEWebDemo)
    demo.execution_status = {}
    demo.logger = logging.getLogger("test_progress_events")
    return demo


def start_run(demo, execution_id="run-1", started=None):
    demo.execution_status[execution_id] = {
        "status": "running",
        "start_time": (started or datetime.now()).isoformat(),
    }
    return demo.new_progress_context()


def start_event(combo_id, model_id="anthropic/claude", framework_id="ins_analytical",
                parallel=True, **extra):
    event = {
        "type": "combination_start_parallel" if parallel else "combination_start",
        "combination_id": combo_id,
        "model": "Claude Sonnet 4.5",
        "model_id": model_id,
        "framework": "Analytical Framework",
        "framework_id": framework_id,
        "domain": "Energy Systems",
        "provider": "openrouter",
        "progress_percent": 5,
    }
    event.update(extra)
    return event


class TestRunStart(unittest.TestCase):
    """The event that announces a parallel run."""

    def test_parallel_execution_start_sets_the_total(self):
        # main.py emits `parallel_execution_start`; app.py listened only for
        # `execution_start`, so the total stayed at zero for every web run.
        demo = make_demo()
        ctx = start_run(demo)

        demo._apply_progress_event("run-1", {
            "type": "parallel_execution_start",
            "total_combinations": 66,
            "max_workers": 8,
        }, ctx)

        self.assertEqual(ctx["total"], 66)
        self.assertEqual(demo.execution_status["run-1"]["total_combinations"], 66)

    def test_sequential_execution_start_still_sets_the_total(self):
        demo = make_demo()
        ctx = start_run(demo)

        demo._apply_progress_event("run-1", {
            "type": "execution_start",
            "total_combinations": 11,
        }, ctx)

        self.assertEqual(demo.execution_status["run-1"]["total_combinations"], 11)

    def test_start_resets_a_previous_run_in_the_same_context(self):
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", {"type": "parallel_execution_start",
                                             "total_combinations": 2}, ctx)
        demo._apply_progress_event("run-1", start_event("c1"), ctx)

        demo._apply_progress_event("run-1", {"type": "parallel_execution_start",
                                             "total_combinations": 3}, ctx)

        self.assertEqual(ctx["calls"], {})
        self.assertEqual(demo.execution_status["run-1"]["active_parallel_calls"], [])


class TestNoDivisionByZero(unittest.TestCase):
    """A missing or zero total must not take the whole event stream down."""

    def test_start_before_any_total_does_not_raise(self):
        # The old code computed `completed * 100 // total` as the *default* of a
        # .get(), which Python evaluates eagerly — so this raised
        # ZeroDivisionError, and the outer handler logged it at debug level.
        demo = make_demo()
        ctx = start_run(demo)

        demo._apply_progress_event("run-1", start_event("c1"), ctx)

        self.assertIn("c1", ctx["calls"])
        self.assertIn("Processing", demo.execution_status["run-1"]["message"])

    def test_completion_before_any_total_does_not_raise(self):
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", start_event("c1"), ctx)

        demo._apply_progress_event("run-1", {
            "type": "combination_complete_parallel",
            "combination_id": "c1",
            "success": True,
            "response_length": 4200,
        }, ctx)

        self.assertEqual(demo.execution_status["run-1"]["completed_combinations"], 1)

    def test_progress_never_exceeds_the_band_reserved_for_execution(self):
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", {"type": "parallel_execution_start",
                                             "total_combinations": 4}, ctx)

        for i in range(4):
            demo._apply_progress_event("run-1", start_event(f"c{i}"), ctx)
            demo._apply_progress_event("run-1", {
                "type": "combination_complete_parallel",
                "combination_id": f"c{i}",
                "success": True,
            }, ctx)

        self.assertEqual(demo.execution_status["run-1"]["progress"], 90)


class TestCallRegister(unittest.TestCase):
    """Completions must find the call they belong to."""

    def test_completion_resolves_a_call_from_far_back(self):
        # The register used to be cut to the last eight entries on every start,
        # so on a 66-call run most completions found nothing and were dropped.
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", {"type": "parallel_execution_start",
                                             "total_combinations": 40}, ctx)

        for i in range(40):
            demo._apply_progress_event("run-1", start_event(f"c{i}"), ctx)

        demo._apply_progress_event("run-1", {
            "type": "combination_complete_parallel",
            "combination_id": "c0",
            "success": True,
            "response_length": 1234,
        }, ctx)

        self.assertEqual(ctx["calls"]["c0"]["status"], "completed")
        self.assertEqual(ctx["calls"]["c0"]["response_length"], 1234)
        self.assertEqual(ctx["unmatched"], 0)

    def test_active_list_holds_every_call_in_flight(self):
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", {"type": "parallel_execution_start",
                                             "total_combinations": 12}, ctx)

        for i in range(12):
            demo._apply_progress_event("run-1", start_event(f"c{i}"), ctx)
        demo._apply_progress_event("run-1", {
            "type": "combination_complete_parallel",
            "combination_id": "c3",
            "success": True,
        }, ctx)

        active = demo.execution_status["run-1"]["active_parallel_calls"]
        self.assertEqual(len(active), 11)
        self.assertNotIn("c3", [call["combination_id"] for call in active])

    def test_display_list_is_capped_but_the_register_is_not(self):
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", {"type": "parallel_execution_start",
                                             "total_combinations": 66}, ctx)

        for i in range(66):
            demo._apply_progress_event("run-1", start_event(f"c{i}"), ctx)

        status = demo.execution_status["run-1"]
        self.assertEqual(len(ctx["calls"]), 66)
        self.assertEqual(len(status["current_calls"]), demo.DISPLAY_CALLS)

    def test_identifiers_reach_the_browser(self):
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", start_event(
            "c1", model_id="openai/gpt-5.6-luna", framework_id="ins_contrarian"), ctx)

        call = demo.execution_status["run-1"]["active_parallel_calls"][0]
        self.assertEqual(call["model_id"], "openai/gpt-5.6-luna")
        self.assertEqual(call["framework_id"], "ins_contrarian")


class TestFailures(unittest.TestCase):
    """A failed call has to be visible as a failed call."""

    def test_exhausted_call_is_recorded(self):
        # `combination_failed_parallel` had no handler at all: the call stayed
        # "processing" for the rest of the run and was never counted.
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", {"type": "parallel_execution_start",
                                             "total_combinations": 2}, ctx)
        demo._apply_progress_event("run-1", start_event("c1"), ctx)

        demo._apply_progress_event("run-1", {
            "type": "combination_failed_parallel",
            "combination_id": "c1",
            "error": "connection reset",
            "attempts": 3,
        }, ctx)

        status = demo.execution_status["run-1"]
        self.assertEqual(ctx["calls"]["c1"]["status"], "error")
        self.assertEqual(ctx["calls"]["c1"]["error"], "connection reset")
        self.assertEqual(ctx["calls"]["c1"]["attempts"], 3)
        self.assertEqual(status["completed_combinations"], 1)
        self.assertEqual(status["failed_combinations"], 1)
        self.assertEqual(status["active_parallel_calls"], [])

    def test_unsuccessful_completion_counts_as_a_failure(self):
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", start_event("c1"), ctx)

        demo._apply_progress_event("run-1", {
            "type": "combination_complete_parallel",
            "combination_id": "c1",
            "success": False,
            "error": "HTTP 429",
        }, ctx)

        status = demo.execution_status["run-1"]
        self.assertEqual(status["failed_combinations"], 1)
        self.assertIn("HTTP 429", status["message"])

    def test_final_tally_overrides_the_running_count(self):
        demo = make_demo()
        ctx = start_run(demo)

        demo._apply_progress_event("run-1", {
            "type": "parallel_execution_complete",
            "total_combinations": 66,
            "completed": 61,
            "failed": 5,
        }, ctx)

        status = demo.execution_status["run-1"]
        self.assertEqual(status["succeeded_combinations"], 61)
        self.assertEqual(status["failed_combinations"], 5)


class TestAttribution(unittest.TestCase):
    """Completions without an id must not be pinned on the wrong call."""

    def test_sequential_completion_resolves_the_single_call_in_flight(self):
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", start_event("c1", parallel=False), ctx)

        demo._apply_progress_event("run-1", {
            "type": "combination_complete",
            "success": True,
            "response_length": 900,
        }, ctx)

        self.assertEqual(ctx["calls"]["c1"]["status"], "completed")
        self.assertEqual(ctx["unmatched"], 0)

    def test_ambiguous_completion_is_counted_but_not_attributed(self):
        # The old code marked "the most recently started" call complete. Under
        # parallel execution that is almost never the one that finished.
        demo = make_demo()
        ctx = start_run(demo)
        demo._apply_progress_event("run-1", start_event("c1"), ctx)
        demo._apply_progress_event("run-1", start_event("c2"), ctx)

        demo._apply_progress_event("run-1", {
            "type": "combination_complete_parallel",
            "success": True,
        }, ctx)

        self.assertEqual(ctx["unmatched"], 1)
        self.assertEqual(demo.execution_status["run-1"]["completed_combinations"], 1)
        self.assertEqual(ctx["calls"]["c1"]["status"], "processing")
        self.assertEqual(ctx["calls"]["c2"]["status"], "processing")


class TestRobustness(unittest.TestCase):
    def test_event_without_a_type_is_ignored(self):
        demo = make_demo()
        ctx = start_run(demo)

        demo._apply_progress_event("run-1", {"combination_id": "c1"}, ctx)

        self.assertEqual(ctx["calls"], {})

    def test_event_for_an_unknown_run_is_ignored(self):
        demo = make_demo()
        ctx = demo.new_progress_context()

        demo._apply_progress_event("no-such-run", start_event("c1"), ctx)

        self.assertEqual(demo.execution_status, {})

    def test_unusable_start_time_does_not_raise(self):
        demo = make_demo()
        demo.execution_status["run-1"] = {"status": "running", "start_time": "not a date"}
        ctx = demo.new_progress_context()

        demo._apply_progress_event("run-1", start_event("c1"), ctx)

        self.assertIn("c1", ctx["calls"])

    def test_eta_appears_once_something_has_finished(self):
        demo = make_demo()
        ctx = start_run(demo, started=datetime.now() - timedelta(minutes=2))
        demo._apply_progress_event("run-1", {"type": "parallel_execution_start",
                                             "total_combinations": 10}, ctx)
        demo._apply_progress_event("run-1", start_event("c1"), ctx)
        demo._apply_progress_event("run-1", {"type": "combination_complete_parallel",
                                             "combination_id": "c1",
                                             "success": True}, ctx)
        demo._apply_progress_event("run-1", start_event("c2"), ctx)

        message = demo.execution_status["run-1"]["message"]
        self.assertIn("ETA:", message)
        self.assertNotIn("calculating", message)


class TestEventCoverage(unittest.TestCase):
    """Every event the engine emits needs a handler on the receiving side."""

    def test_no_emitted_event_type_is_unhandled(self):
        import re

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "main.py"), encoding="utf-8") as fh:
            emitted = set(re.findall(r'"type":\s*"([a-z_]+)"', fh.read()))
        with open(os.path.join(root, "app.py"), encoding="utf-8") as fh:
            app_source = fh.read()
        handler = app_source.split("def _apply_progress_event")[1].split("\n    def ")[0]
        handled = set(re.findall(r'"([a-z_]+)"', handler))

        self.assertTrue(emitted, "no progress events found in main.py")
        self.assertEqual(emitted - handled, set(),
                         "main.py emits progress events app.py does not handle")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestEventExtraction(unittest.TestCase):
    """Getting events out of a shared text stream.

    The engine prints progress from a thread pool, so `print()` calls interleave
    and a marker often lands mid-line behind another thread's output. Requiring
    the line to begin with the marker dropped a third of the events of a live run
    on 03.09.2026 — 6 of 18 — with nothing logged.
    """

    def setUp(self):
        self.demo = make_demo()

    def test_a_clean_line_yields_its_event(self):
        line = 'PROGRESS_JSON:{"type": "execution_start", "total_combinations": 11}'

        events = self.demo.extract_progress_events(line)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["total_combinations"], 11)

    def test_an_event_glued_behind_other_output_is_still_found(self):
        line = ('Creating client for model or_claude_sonnet_5 using provider: openrouter'
                'PROGRESS_JSON:{"type": "combination_start_parallel", "combination_id": "c1"}')

        events = self.demo.extract_progress_events(line)

        self.assertEqual([e["combination_id"] for e in events], ["c1"])

    def test_two_events_on_one_line_are_both_found(self):
        line = ('PROGRESS_JSON:{"type": "combination_complete_parallel", "combination_id": "c1"}'
                'Making real API call to or_gemini_35_fl...'
                'PROGRESS_JSON:{"type": "combination_start_parallel", "combination_id": "c2"}')

        events = self.demo.extract_progress_events(line)

        self.assertEqual([e["combination_id"] for e in events], ["c1", "c2"])

    def test_trailing_output_after_an_event_is_ignored(self):
        line = ('PROGRESS_JSON:{"type": "execution_start", "total_combinations": 3}'
                ' Loaded 15 domains')

        events = self.demo.extract_progress_events(line)

        self.assertEqual(len(events), 1)

    def test_a_line_without_a_marker_yields_nothing(self):
        self.assertEqual(self.demo.extract_progress_events("Loaded 11 templates"), [])

    def test_a_truncated_event_does_not_raise(self):
        line = 'PROGRESS_JSON:{"type": "combination_start_paral'

        self.assertEqual(self.demo.extract_progress_events(line), [])

    def test_a_non_object_payload_is_not_treated_as_an_event(self):
        self.assertEqual(self.demo.extract_progress_events('PROGRESS_JSON:"hello"'), [])
