#!/usr/bin/env python3
"""What the /runs archive page shows, and how it admits what it does not know.

The owner asked for an overview of past runs on 02.09.2026
(docs/todos/2026-09-02-offene-punkte.md, 1.1); this exercises run_archive.py, the
pure-function module that reads a run directory and summarises it, independent of
Flask. The fixtures below are built from what real data/output/run_* directories
actually look like (inspected 05.09.2026), not from an idealised "complete" run:
several genuinely differ in which files exist, and the whole point of this module
is to degrade per-field instead of per-run when one is missing.

The last two test classes exercise the two routes added to app.py, using
app.test_client() only - no server is started, per this task's instructions.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_archive import list_run_directories, list_run_summaries, summarize_run


def make_run_dir(root: Path, run_id: str) -> Path:
    run_dir = root / run_id
    run_dir.mkdir(parents=True)
    return run_dir


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


class TestACompleteRunReportsWhatActuallyHappened(unittest.TestCase):
    """A run with every artefact present: the real shape of a run from
    03.09.2026 onward, once cost reporting existed."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.run_dir = make_run_dir(self.root, "run_20260903_195844")

        write(
            self.run_dir / "run_summary.md",
            '# ISEE Meta-Framework Run Summary\n\n## Run Configuration\n'
            '- **Query**: "Wie lässt sich die Abwärme sinnvoll nutzen?"\n'
            "- **Timestamp**: 2026-09-03 20:00:55\n",
        )
        write(
            self.run_dir / "metadata.md",
            "# ISEE Meta-Framework Combination Metadata Report\n\n"
            "## Combination Overview\n\n"
            "- **Total Combinations**: 3\n"
            "- **Executed Combinations**: 3\n",
        )
        write(
            self.run_dir / "combinations.csv",
            "combination_id,model_id,model_name,instruction_id,domain_id,query_id,"
            "executed,response_length,execution_time,overall_score\n"
            "a,or_x,X,ins_a,dom_a,q1,True,100,1.0,0.5\n"
            "b,or_x,X,ins_b,dom_a,q1,True,120,1.1,0.6\n"
            "c,or_x,X,ins_c,dom_a,q1,True,90,0.9,0.4\n",
        )
        write(
            self.run_dir / "cost_report.json",
            '{"total_cost_usd": 0.123456, "priced_calls": 3}',
        )
        write(self.run_dir / "isee_result.md", "# Query Information\n\nignored\n")
        write(self.run_dir / "analysis.md", "analysis")
        write(self.run_dir / "ideas.csv", "idea\n")
        write(self.run_dir / "model_performance.csv", "model\n")
        write(self.run_dir / "cost_report.txt", "text report")
        write(self.run_dir / "queries_detailed_20260903_200055.csv", "q\n")
        write(self.run_dir / "queries_summary_20260903_200055.json", "{}")
        for chart in (
            "domain_comparison.png",
            "instruction_comparison.png",
            "model_comparison.png",
            "scoring_components.png",
        ):
            (self.run_dir / chart).write_bytes(b"\x89PNG")

        raw_dir = self.run_dir / "raw_responses"
        raw_dir.mkdir()
        (raw_dir / "01_a.md").write_text("response a", encoding="utf-8")
        (raw_dir / "02_b.md").write_text("response b", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_the_query_comes_from_run_summary_not_isee_result(self):
        summary = summarize_run(self.run_dir)

        self.assertEqual(
            summary["query"],
            "Wie lässt sich die Abwärme sinnvoll nutzen?",
        )

    def test_the_timestamp_is_parsed_from_the_run_id(self):
        summary = summarize_run(self.run_dir)

        self.assertEqual(summary["timestamp"], "2026-09-03T19:58:44")

    def test_combination_counts_come_from_the_actual_files(self):
        summary = summarize_run(self.run_dir)

        self.assertEqual(summary["combinations_total"], 3)
        self.assertEqual(summary["combinations_succeeded"], 3)
        # This fixture's combinations.csv is the old format (no "status" column)
        # and there is no failed_responses/ directory. run_archive.py refuses to
        # infer zero failures from that absence - a missing failed_responses/
        # directory is not proof nothing failed, just the only real run_archive.py
        # signal was not present. See _count_combinations' docstring.
        self.assertIsNone(summary["combinations_failed"])

    def test_the_cost_is_read_from_cost_report_json(self):
        summary = summarize_run(self.run_dir)

        self.assertEqual(summary["cost_usd"], 0.123456)

    def test_every_existing_artefact_gets_a_path(self):
        summary = summarize_run(self.run_dir)
        artifacts = summary["artifacts"]

        self.assertEqual(
            artifacts["isee_result_md"],
            "data/output/run_20260903_195844/isee_result.md",
        )
        self.assertEqual(
            artifacts["cost_report_json"],
            "data/output/run_20260903_195844/cost_report.json",
        )
        self.assertEqual(artifacts["raw_responses_count"], 2)
        self.assertEqual(
            artifacts["cognitive_diversity_explorer_url"],
            "/cognitive_diversity_explorer/run_20260903_195844",
        )

    def test_a_run_with_no_failures_has_no_failed_responses_directory_link(self):
        summary = summarize_run(self.run_dir)

        self.assertIsNone(summary["artifacts"]["failed_responses_count"])


class TestARunMissingItsCostReportSaysSoInsteadOfShowingZero(unittest.TestCase):
    """This is the case the task calls out by name: an older run without a cost
    report must read as "not recorded", never as a free run."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.run_dir = make_run_dir(self.root, "run_20260902_212847")
        write(
            self.run_dir / "run_summary.md",
            '- **Query**: "Name one failure mode."\n',
        )
        write(
            self.run_dir / "combinations.csv",
            "combination_id,model_id,model_name,instruction_id,domain_id,query_id,"
            "executed,response_length,execution_time,overall_score\n"
            "a,or_x,X,ins_a,dom_a,q1,True,100,1.0,0.5\n",
        )
        # Deliberately no cost_report.json and no cost_report.txt.

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_cost_is_none_not_zero(self):
        summary = summarize_run(self.run_dir)

        self.assertIsNone(summary["cost_usd"])

    def test_the_cost_report_artefacts_are_marked_absent(self):
        summary = summarize_run(self.run_dir)

        self.assertIsNone(summary["artifacts"]["cost_report_json"])
        self.assertIsNone(summary["artifacts"]["cost_report_txt"])

    def test_fields_that_are_available_are_still_reported(self):
        # Missing cost must not blank out the rest of the summary.
        summary = summarize_run(self.run_dir)

        self.assertEqual(summary["query"], "Name one failure mode.")
        self.assertEqual(summary["combinations_succeeded"], 1)


class TestARunWithOnlyOneFileStillReportsWhatItHas(unittest.TestCase):
    """The real run_20260902_222121: reporting.py crashed on a failed
    combination before writing metadata.md, run_summary.md, combinations.csv or
    a cost report, but main.py had already written isee_result.md and the query
    export. This checks the degraded-almost-completely case, one step further
    than "missing the cost report": only a single file survives."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.run_dir = make_run_dir(self.root, "run_20260902_222121")
        write(
            self.run_dir / "isee_result.md",
            "# Query Information\n\n"
            "What limits heat pump adoption in older German apartment buildings?\n\n"
            "# Parameters\n",
        )

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_the_query_falls_back_to_isee_result_md(self):
        summary = summarize_run(self.run_dir)

        self.assertEqual(
            summary["query"],
            "What limits heat pump adoption in older German apartment buildings?",
        )

    def test_everything_without_a_surviving_file_is_none_not_a_guess(self):
        summary = summarize_run(self.run_dir)

        self.assertIsNone(summary["combinations_total"])
        self.assertIsNone(summary["combinations_succeeded"])
        self.assertIsNone(summary["combinations_failed"])
        self.assertIsNone(summary["cost_usd"])

    def test_only_the_one_surviving_artefact_has_a_path(self):
        summary = summarize_run(self.run_dir)
        artifacts = summary["artifacts"]

        self.assertEqual(
            artifacts["isee_result_md"],
            "data/output/run_20260902_222121/isee_result.md",
        )
        self.assertIsNone(artifacts["metadata"])
        self.assertIsNone(artifacts["run_summary"])
        self.assertIsNone(artifacts["combinations_csv"])
        self.assertIsNone(artifacts["cost_report_json"])
        self.assertIsNone(artifacts["raw_responses_count"])


class TestANewFormatCombinationsCsvWithAStatusColumn(unittest.TestCase):
    """reporting.py's current code (post the crash-on-failure fix) writes a
    "status" column for every planned combination, succeeded or not - no real
    run on disk uses this shape yet, but the next one will, so the reader must
    not silently mis-score it by falling back to the old "executed" logic."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.run_dir = make_run_dir(self.root, "run_20260905_000000")
        write(
            self.run_dir / "combinations.csv",
            "combination_id,model_id,model_name,instruction_id,domain_id,query_id,"
            "executed,status,response_length,execution_time,overall_score\n"
            "a,or_x,X,ins_a,dom_a,q1,True,succeeded,100,1.0,0.5\n"
            "b,or_x,X,ins_b,dom_a,q1,True,failed,,2.0,\n"
            "c,or_x,X,ins_c,dom_a,q1,False,not_executed,,,\n",
        )

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_succeeded_and_failed_are_read_from_the_status_column(self):
        summary = summarize_run(self.run_dir)

        self.assertEqual(summary["combinations_total"], 3)
        self.assertEqual(summary["combinations_succeeded"], 1)
        self.assertEqual(summary["combinations_failed"], 2)


class TestADirectoryThatIsNotARunAtAll(unittest.TestCase):
    """data/output holds more than run directories: latest.txt is a file, and
    session-summaries/ and the nested 2026-09/week1/... layout are directories
    that are not named like a run. Both must be recognisable as "not a run"
    rather than crashing or being summarised as an empty one."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_a_wrongly_named_directory_is_reported_as_not_a_run(self):
        stray = make_run_dir(self.root, "session-summaries")
        write(stray / "SESSION-SUMMARY-2025-01-01-01.md", "notes")

        summary = summarize_run(stray)

        self.assertFalse(summary["is_run"])

    def test_listing_skips_non_run_entries_but_keeps_real_runs(self):
        make_run_dir(self.root, "session-summaries")
        (self.root / "latest.txt").write_text("run_20260903_195844", encoding="utf-8")
        real_run = make_run_dir(self.root, "run_20260903_195844")

        found = list_run_directories(self.root)

        self.assertEqual(found, [real_run])

    def test_an_empty_run_directory_is_still_a_run_with_nothing_recorded(self):
        # Three real run directories on disk (05.09.2026) are exactly this:
        # the name was created but no file was ever written into it.
        empty_run = make_run_dir(self.root, "run_20260902_212316")

        summary = summarize_run(empty_run)

        self.assertTrue(summary["is_run"])
        self.assertIsNone(summary["query"])
        self.assertIsNone(summary["cost_usd"])
        self.assertIsNone(summary["combinations_total"])


class TestRunsAreListedNewestFirst(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_ordering_matches_the_run_id_timestamp(self):
        make_run_dir(self.root, "run_20260902_100000")
        make_run_dir(self.root, "run_20260903_090000")
        make_run_dir(self.root, "run_20260902_235959")

        found = [p.name for p in list_run_directories(self.root)]

        self.assertEqual(
            found,
            ["run_20260903_090000", "run_20260902_235959", "run_20260902_100000"],
        )

    def test_list_run_summaries_returns_one_dict_per_run_newest_first(self):
        make_run_dir(self.root, "run_20260902_100000")
        make_run_dir(self.root, "run_20260903_090000")

        summaries = list_run_summaries(self.root)

        self.assertEqual(
            [s["run_id"] for s in summaries],
            ["run_20260903_090000", "run_20260902_100000"],
        )

    def test_a_missing_output_directory_yields_no_runs_rather_than_an_error(self):
        missing = self.root / "does-not-exist"

        self.assertEqual(list_run_directories(missing), [])
        self.assertEqual(list_run_summaries(missing), [])


class TestTheRunsPageRoute(unittest.TestCase):
    """/runs and /api/runs, exercised only through app.test_client() - no
    server. The routes read data/output relative to the process's working
    directory (matching every other run-directory route already in app.py), so
    the fixture directory is installed by chdir'ing into a temp root, the same
    approach tests/test_latest_pointer.py already uses for the same reason.
    """

    @classmethod
    def setUpClass(cls):
        from app import app

        app.config["TESTING"] = True
        cls.client = app.test_client()

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.previous_cwd = os.getcwd()
        os.chdir(self.root)
        run_dir = make_run_dir(self.root / "data" / "output", "run_20260903_195844")
        write(run_dir / "run_summary.md", '- **Query**: "Test query for the route"\n')

    def tearDown(self):
        os.chdir(self.previous_cwd)
        shutil.rmtree(self.root, ignore_errors=True)

    def test_the_page_route_serves_html_without_touching_a_server(self):
        response = self.client.get("/runs")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"text/html", response.content_type.encode())

    def test_the_json_route_lists_the_fixture_run(self):
        response = self.client.get("/api/runs")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["run_id"], "run_20260903_195844")
        self.assertEqual(payload[0]["query"], "Test query for the route")

    def test_the_json_route_is_empty_when_no_runs_exist_yet(self):
        shutil.rmtree(self.root / "data" / "output")

        response = self.client.get("/api/runs")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
