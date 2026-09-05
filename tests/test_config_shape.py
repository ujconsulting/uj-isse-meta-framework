"""openrouter_config.json keeps only the sections the code actually reads, and the
favicon route resolves the console's only 404.

Background (todo items 3.1 and 2.3): a 2026-09 audit found five top-level blocks
in openrouter_config.json that no non-archive, non-test source ever looked up
(`cognitive_diversity`, `integration_notes`, `scoring_criteria`,
`evaluation_settings`, `extraction_settings`) and removed them. `cognitive_diversity`
in particular referenced model ids (e.g. "anthropic/claude-sonnet-4") that were never
in this file's `models.api_models` list under any version — evidence it had drifted
out of use rather than being a planned-but-unbuilt feature. The tests below guard
against both regressions: an unread block quietly creeping back in, and a model id
appearing anywhere in the file without a matching `models.api_models` entry.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app

CONFIG_PATH = Path(__file__).parent.parent / "openrouter_config.json"

# The six keys something in the codebase actually reads (see app.py's config loads,
# main.py's query loop, cost_estimation.py, domain_manager.py's usage of
# converted_params, and query_generator.py's 'queries' lookup).
EXPECTED_TOP_LEVEL_KEYS = {
    "description",
    "version",
    "models",
    "instructions",
    "queries",
    "domains",
}

# Blocks measured as unread anywhere outside archive/ and tests/ at the time of the
# 2026-09 audit. If one of these reappears, it should come back deliberately (with a
# real reader added alongside it), not as leftover drift.
REMOVED_UNREAD_KEYS = {
    "cognitive_diversity",
    "integration_notes",
    "scoring_criteria",
    "evaluation_settings",
    "extraction_settings",
}

# Matches a "provider/model-name" style id such as "anthropic/claude-sonnet-5" or
# "x-ai/grok-4.3": exactly one slash, no whitespace, no "://". This intentionally
# does not match `pricing.source` ("openrouter /api/v1/models", which has a space)
# or the provider_config URLs (which contain "://" and multiple slashes) -- both are
# legitimate non-model-id strings that happen to contain a "/".
MODEL_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*/[a-z0-9][a-z0-9_.:-]*$")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def find_model_id_like_strings(node):
    """Walk the whole config and collect every string that looks like a model id.

    This is deliberately structure-agnostic: the point of the guard is to catch a
    model id turning up in some *new* block (a future cognitive_diversity-shaped
    section, say) that nobody thought to cross-check against models.api_models --
    the exact way the removed cognitive_diversity block went stale.
    """
    found = []
    if isinstance(node, dict):
        for value in node.values():
            found.extend(find_model_id_like_strings(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(find_model_id_like_strings(item))
    elif isinstance(node, str) and MODEL_ID_PATTERN.match(node):
        found.append(node)
    return found


def test_the_config_file_is_valid_json():
    load_config()  # raises json.JSONDecodeError on malformed content


def test_the_six_keys_something_reads_are_present():
    config = load_config()
    missing = EXPECTED_TOP_LEVEL_KEYS - config.keys()
    assert not missing, f"expected top-level keys missing: {missing}"


def test_the_unread_blocks_have_not_crept_back_without_a_reader():
    config = load_config()
    present_again = REMOVED_UNREAD_KEYS & config.keys()
    assert not present_again, (
        f"these keys were removed as unread and are back: {present_again}. "
        "If this is intentional, add the code that reads them and drop the key "
        "from REMOVED_UNREAD_KEYS in this test."
    )


def test_every_model_id_referenced_anywhere_exists_in_api_models():
    config = load_config()
    valid_ids = {
        model["parameters"]["model"]
        for model in config["models"]["api_models"]
    }
    referenced_ids = set(find_model_id_like_strings(config))
    unknown_ids = referenced_ids - valid_ids
    assert not unknown_ids, (
        f"model ids referenced in the config but absent from models.api_models: "
        f"{unknown_ids}. This is exactly how cognitive_diversity drifted out of "
        "sync with the model roster before it was removed."
    )


def test_favicon_ico_resolves_instead_of_404ing():
    """/favicon.ico is the only console error the web interface produces: browsers
    request it unconditionally, and isee-ui.html (the primary interface) never
    linked an icon, so the request fell through to a 404. Verified via the test
    client rather than a live server per this task's instructions.
    """
    app.config["TESTING"] = True
    client = app.test_client()

    response = client.get("/favicon.ico")

    assert response.status_code == 200
    assert response.content_type.startswith("image/")
