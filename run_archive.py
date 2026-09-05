"""Summarise past ISEE runs for the /runs archive page.

The owner asked for "an overview of all past runs with the documents and results
each produced" on 02.09.2026 (docs/todos/2026-09-02-offene-punkte.md, section 1.1).
The data was always on disk under data/output/run_YYYYMMDD_HHMMSS/ - nothing here
computes anything new, it only reads what main.py and reporting.py already wrote.

Every function below is pure: given a directory path, it returns a plain dict (or
list of dicts) and touches nothing else. That is deliberate - it lets
tests/test_run_archive.py build fixture directories and assert on the result
without starting Flask or running a real analysis, and it keeps the two routes in
app.py thin wrappers instead of a second place where this logic could drift.

Two things this module is careful about, because getting them wrong is exactly
the kind of bug this repository's recent history is about:

1. Real run directories are inconsistent with each other. Inspecting the actual
   data/output/run_* directories on 05.09.2026 found: three empty run directories
   (a run that never produced a single file), one run with no metadata.md,
   combinations.csv or cost_report at all (main.py's isee_result.md and query
   export survived, but reporting.py's older combinations.csv writer crashed on
   the run's one failed combination before writing anything else - see
   _count_combinations below), some runs writing isee_result.json instead of
   isee_result.md, and cost_report.json/.txt only existing on runs from
   03.09.2026 onward (the feature did not exist before). Every reader in this
   module has to degrade per-field, not per-run: one missing file must not blank
   out the fields that other files still answer.

2. A missing number must read as missing, not as zero. An older run without a
   cost report reports cost_usd = None, and the page must render that as
   "not recorded" - never "$0.00", which would claim the run was free.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# main.py's run directories are always named run_YYYYMMDD_HHMMSS. Anything else
# under data/output (the "latest.txt" pointer, the session-summaries/ folder, and
# a leftover data/output/2026-09/week1/... nested-by-week layout from an earlier,
# abandoned organise-by-date convention - see the Route A table in
# docs/todos/2026-09-02-offene-punkte.md, "Flaches Ausgabelayout") is not a run
# and must not be listed as one.
RUN_ID_PATTERN = re.compile(r"^run_(\d{8})_(\d{6})$")

# Files whose name is fixed. Each maps to a stable key used in the returned dict
# and in templates/run_archive.html - not to the filename itself, so the template
# does not have to know these paths.
_SINGLE_FILE_ARTIFACTS = {
    "isee_result_md": "isee_result.md",
    "isee_result_json": "isee_result.json",
    "analysis": "analysis.md",
    "run_summary": "run_summary.md",
    "metadata": "metadata.md",
    "combinations_csv": "combinations.csv",
    "ideas_csv": "ideas.csv",
    "model_performance_csv": "model_performance.csv",
    "cost_report_txt": "cost_report.txt",
    "cost_report_json": "cost_report.json",
    "domain_comparison_chart": "domain_comparison.png",
    "instruction_comparison_chart": "instruction_comparison.png",
    "model_comparison_chart": "model_comparison.png",
    "scoring_components_chart": "scoring_components.png",
}

# Files whose name carries an export timestamp (auto_export_queries in main.py).
# When several match (should not happen within one run, but glob makes no
# promise), the lexicographically last one is the most recent.
_GLOB_ARTIFACTS = {
    "queries_detailed_csv": "queries_detailed_*.csv",
    "queries_summary_json": "queries_summary_*.json",
}


def is_run_directory(path: Path) -> bool:
    """True only for a directory named the way main.py names run output."""
    return path.is_dir() and RUN_ID_PATTERN.match(path.name) is not None


def parse_run_timestamp(run_id: str) -> Optional[str]:
    """'run_20260903_195844' -> ISO timestamp. None if run_id is not that shape."""
    match = RUN_ID_PATTERN.match(run_id)
    if not match:
        return None
    date_part, time_part = match.groups()
    try:
        return datetime.strptime(date_part + time_part, "%Y%m%d%H%M%S").isoformat()
    except ValueError:
        return None


def list_run_directories(output_dir: Path) -> List[Path]:
    """Every run_* directory under output_dir, at any depth, newest first.

    This searched only the top level at first, on the assumption that the nested
    data/output/YYYY-MM/weekN/ tree was an abandoned layout. It is not abandoned:
    THE TWO ENTRY POINTS STILL WRITE TO DIFFERENT PLACES. app.py creates
    data/output/run_TIMESTAMP before launching the subprocess, while main.py's own
    constructor computes data/output/YYYY-MM/weekN/run_TIMESTAMP. So every run
    started from the web interface lands flat and every run started from the command
    line lands nested.

    A top-level-only search therefore produced an archive that looked complete and
    silently omitted every CLI run - the same failure this branch keeps finding, this
    time in code written to expose it. Measured on 05.09.2026: seven runs listed, two
    on disk not listed.

    Unifying the two layouts is the actual repair, and it is not made here: CLAUDE.md
    requires a reviewed plan for changes to the run output layout, and this is a
    reader. Until then the reader takes the disk as it is.

    Sorting by name is intentional: the timestamp is baked into the name and sorts
    identically, while mtime would promote a run whose files were merely touched
    later.
    """
    if not output_dir.exists():
        return []
    runs = [p for p in output_dir.rglob("run_*") if is_run_directory(p)]
    runs.sort(key=lambda p: p.name, reverse=True)
    return runs


def _read_text(path: Path) -> Optional[str]:
    """Read a text file, or None on any failure. A run directory can contain a
    file that exists but is not readable (permissions, encoding, or - as found
    in one real run - a JSON file that is present but empty); no single bad
    file should abort summarising the rest of the run."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _extract_query(run_dir: Path) -> Optional[str]:
    """The research question the run answered.

    run_summary.md is the only place this text has ever appeared in one
    consistent, quoted shape: `- **Query**: "<text>"` (reporting.py's
    generate_run_summary). isee_result.md carries the same text under a
    '# Query Information' heading, unquoted, and is used as a fallback for runs
    whose reporting step got far enough to write isee_result.md but not
    run_summary.md - the real run_20260902_222121 is exactly that case: it has
    a failed combination, and the era's combinations.csv writer crashed on the
    first failed row before run_summary.md (which is written after) was ever
    produced, while main.py's own isee_result.md and query export had already
    landed on disk.
    """
    summary_text = _read_text(run_dir / "run_summary.md")
    if summary_text:
        match = re.search(r'\*\*Query\*\*:\s*"(.*)"', summary_text)
        if match:
            return match.group(1)

    result_text = _read_text(run_dir / "isee_result.md")
    if result_text:
        match = re.search(r"# Query Information\s*\n+(.+?)\n", result_text)
        if match:
            return match.group(1).strip()

    return None


def _extract_cost(run_dir: Path) -> Optional[float]:
    """Total cost in USD from cost_report.json, or None when it was never
    recorded. Runs from before 03.09.2026 (item 2.6 of the project todo list)
    never write this file - that is "not recorded", categorically different
    from a run that was free, so this returns None rather than 0.0.
    """
    text = _read_text(run_dir / "cost_report.json")
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    total = data.get("total_cost_usd")
    return float(total) if isinstance(total, (int, float)) else None


def _count_combinations(run_dir: Path) -> Dict[str, Optional[int]]:
    """How many combinations were planned, how many succeeded, how many failed.

    Each of the three is independently None when this run's files do not say -
    never guessed from the other two. combinations.csv has changed shape across
    this project's history: newer runs (once the fix behind reporting.py's
    "status" column ships) write "succeeded" / "failed" / "not_executed" for
    every planned combination, but every real run inspected on disk on
    05.09.2026 predates that - all six existing combinations.csv files have only
    an "executed" column, and every row in every one of them is True. That is
    not a coincidence: the pre-fix writer computed len(result["response"]) for
    every row it considered executed, and a failed combination's result carries
    "response": None, which crashes that computation - so a pre-fix run with any
    failure never got as far as writing this file at all (matching the real
    run_20260902_222121, which has a failed_responses/ entry and no
    combinations.csv). An old-format file's row count is therefore that run's
    succeeded count, but its *absence* says nothing about failures, which is why
    failed is sourced from failed_responses/ instead of inferred here.
    """
    total: Optional[int] = None
    succeeded: Optional[int] = None
    failed: Optional[int] = None

    metadata_text = _read_text(run_dir / "metadata.md")
    if metadata_text:
        match = re.search(r"\*\*Total Combinations\*\*:\s*(\d+)", metadata_text)
        if match:
            total = int(match.group(1))

    if total is None:
        for summary_file in sorted(run_dir.glob("queries_summary_*.json")):
            text = _read_text(summary_file)
            if not text:
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            candidate = data.get("metadata", {}).get("total_combinations")
            if isinstance(candidate, int):
                total = candidate
            break

    combinations_text = _read_text(run_dir / "combinations.csv")
    if combinations_text:
        # StringIO, not splitlines(): a quoted field could legitimately contain
        # a newline, and DictReader needs to see the file as one stream to
        # handle that instead of splitting mid-field.
        rows = list(csv.DictReader(io.StringIO(combinations_text)))
        if rows:
            fieldnames = rows[0].keys()
            if total is None:
                total = len(rows)
            if "status" in fieldnames:
                succeeded = sum(1 for r in rows if r.get("status") == "succeeded")
                failed = sum(
                    1 for r in rows if r.get("status") in ("failed", "not_executed")
                )
            elif "executed" in fieldnames:
                succeeded = sum(1 for r in rows if r.get("executed") == "True")

    failed_dir = run_dir / "failed_responses"
    if failed is None and failed_dir.is_dir():
        failed = sum(1 for p in failed_dir.iterdir() if p.is_file())

    return {"total": total, "succeeded": succeeded, "failed": failed}


def _artifact_paths(run_dir: Path, location: str, flat: bool) -> Dict[str, Optional[Any]]:
    """Which known artefact files exist for this run.

    `location` is the run's path relative to the repository root, with forward
    slashes - "data/output/run_X" for a run started from the web interface,
    "data/output/2026-09/week1/run_X" for one started from the command line. It is
    passed in rather than rebuilt from the run id because those two layouts exist
    side by side; building it from the id alone produced download links that
    pointed at the flat layout for runs that are not in it.

    That shape is what the existing `/api/download-file?path=...` route already
    accepts (app.py restricts it to paths under data/output), so this is not a new
    contract.
    A value of None means the file does not exist for this run - the template
    is expected to render that as "missing", never silently skip the row, per
    this task's honesty requirement.
    """
    artifacts: Dict[str, Optional[Any]] = {}

    for key, filename in _SINGLE_FILE_ARTIFACTS.items():
        exists = (run_dir / filename).exists()
        artifacts[key] = f"{location}/{filename}" if exists else None

    for key, pattern in _GLOB_ARTIFACTS.items():
        matches = sorted(run_dir.glob(pattern))
        artifacts[key] = f"{location}/{matches[-1].name}" if matches else None

    raw_dir = run_dir / "raw_responses"
    if raw_dir.is_dir():
        raw_count = sum(1 for p in raw_dir.iterdir() if p.is_file())
    else:
        raw_count = None
    artifacts["raw_responses_count"] = raw_count
    # The Cognitive Diversity Explorer is its own page (app.py's
    # /cognitive_diversity_explorer/<run_id>) - link into it rather than
    # rebuilding any part of it here, per this task's design decision.
    #
    # It can only be offered for a run in the flat layout. Its route, and the two
    # API routes the page then calls, take a run id that Flask's default converter
    # will not let contain a slash, and /api/raw-response validates that id against
    # a strict run_YYYYMMDD_HHMMSS pattern. A nested CLI run therefore cannot be
    # addressed at all today.
    #
    # The template says so rather than omitting the link, because a missing link and
    # an unavailable feature look identical, and only one of them is a bug worth
    # reporting. The real repair is one layout, which needs a reviewed plan.
    artifacts["cognitive_diversity_explorer_url"] = (
        f"/cognitive_diversity_explorer/{run_dir.name}" if raw_count and flat else None
    )
    artifacts["explorer_unavailable_reason"] = (
        "nested-layout" if raw_count and not flat else None
    )

    failed_dir = run_dir / "failed_responses"
    artifacts["failed_responses_count"] = (
        sum(1 for p in failed_dir.iterdir() if p.is_file())
        if failed_dir.is_dir()
        else None
    )

    return artifacts


def summarize_run(run_dir: Path, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Read one run directory and return a plain dict describing it.

    Returns {"run_id": ..., "is_run": False} for a directory that is not named
    like a run (see is_run_directory) instead of raising - a caller iterating a
    real data/output/ listing will encounter exactly this (latest.txt,
    session-summaries/) and should be able to filter on is_run rather than
    catch an exception.
    """
    run_dir = Path(run_dir)
    run_id = run_dir.name

    if not is_run_directory(run_dir):
        return {"run_id": run_id, "is_run": False}

    combinations = _count_combinations(run_dir)

    # Where this run actually is, relative to the repository root and with forward
    # slashes on every platform, so the browser gets one shape regardless of what
    # os.sep happens to be.
    base = Path(output_dir) if output_dir is not None else Path("data/output")
    try:
        relative = run_dir.resolve().relative_to(base.resolve())
        location = f"{base.as_posix()}/{relative.as_posix()}"
        # "flat" means sitting directly in the output directory, which is where the
        # web interface puts a run and the only shape the explorer routes can
        # address. Decided on path components against the base, never by counting
        # slashes in the string -- a run under an absolute base has plenty of those.
        flat = len(relative.parts) == 1
    except ValueError:
        location = run_dir.as_posix()
        flat = False

    return {
        "run_id": run_id,
        "is_run": True,
        "location": location,
        "timestamp": parse_run_timestamp(run_id),
        "query": _extract_query(run_dir),
        "combinations_total": combinations["total"],
        "combinations_succeeded": combinations["succeeded"],
        "combinations_failed": combinations["failed"],
        "cost_usd": _extract_cost(run_dir),
        "artifacts": _artifact_paths(run_dir, location, flat),
    }


def list_run_summaries(output_dir: Path) -> List[Dict[str, Any]]:
    """Summaries for every run under output_dir, newest first.

    This is the entire body of the /api/runs route in app.py - the route exists
    only to call this and jsonify the result, which is what keeps it thin per
    this task's separation requirement.
    """
    return [summarize_run(run_dir, output_dir)
            for run_dir in list_run_directories(output_dir)]
