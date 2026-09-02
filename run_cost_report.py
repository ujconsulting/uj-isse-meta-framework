"""What a run actually cost, per model, from billed tokens.

Every cost figure in this project used to be a forecast: combinations times an assumed
per-call price, compared against nothing. This reports the other number — what the
provider actually billed, taken from the `usage` block OpenRouter returns with each
response and priced from the rates recorded in the model configuration.

Keeping both matters. A forecast that is never checked against an invoice drifts without
anyone noticing, which is how a constant of $0.08 per combination survived long enough to
overstate a run by a factor of seventeen.

Prices come from `openrouter_config.json`; see the `pricing` block on each model entry.
Where OpenRouter reports its own cost (`usage.cost`), that figure wins — it is the
provider's own accounting rather than our arithmetic over its rate card.
"""

from __future__ import annotations

import io
import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

CONFIG_PATH = "openrouter_config.json"
CREDITS_URL = "https://openrouter.ai/api/v1/credits"


def load_rates(config_path: str = CONFIG_PATH) -> Dict[str, Dict[str, float]]:
    """Map model id -> {input, output} USD per million tokens, from the configuration."""
    with io.open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    rates: Dict[str, Dict[str, float]] = {}
    for model in config.get("models", {}).get("api_models", []):
        pricing = model.get("pricing")
        if not isinstance(pricing, dict):
            continue
        entry = {
            "input": pricing["prompt_per_mtok"],
            "output": pricing["completion_per_mtok"],
            "fetched": pricing.get("fetched", "undated"),
            "name": model.get("name", model["id"]),
            "api_model": model["parameters"]["model"],
        }
        # Reachable by either key: results record the configuration id, while the API
        # echoes back the provider's model string.
        rates[model["id"]] = entry
        rates[model["parameters"]["model"]] = entry
    return rates


def cost_of(usage: Dict[str, Any], rate: Optional[Dict[str, float]]) -> Optional[float]:
    """Cost of one call in USD, or None when it cannot be established honestly.

    None is a deliberate outcome: a missing price is a visible gap, whereas a guessed one
    is a number people act on. Nothing here substitutes a default rate.
    """
    reported = usage.get("reported_cost_usd")
    if isinstance(reported, (int, float)):
        return float(reported)

    if not rate:
        return None
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    if prompt_tokens is None or completion_tokens is None:
        return None
    return (prompt_tokens * rate["input"] + completion_tokens * rate["output"]) / 1_000_000


def summarise(results: Dict[str, Any], config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Aggregate billed tokens and cost per model across a run's results."""
    rates = load_rates(config_path)
    per_model: Dict[str, Dict[str, Any]] = {}
    unpriced: List[str] = []
    no_usage = 0

    for result in results.values():
        if not isinstance(result, dict) or result.get("status") == "failed":
            continue
        usage = result.get("usage") or {}
        model_id = result.get("metadata", {}).get("model") or usage.get("model") or "unknown"
        rate = rates.get(model_id) or rates.get(usage.get("model") or "")

        if usage.get("total_tokens") is None and usage.get("completion_tokens") is None:
            no_usage += 1
            continue

        row = per_model.setdefault(model_id, {
            "name": (rate or {}).get("name", model_id),
            "calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
            "cost_usd": 0.0, "priced": True,
        })
        row["calls"] += 1
        row["prompt_tokens"] += usage.get("prompt_tokens") or 0
        row["completion_tokens"] += usage.get("completion_tokens") or 0

        cost = cost_of(usage, rate)
        if cost is None:
            row["priced"] = False
            if model_id not in unpriced:
                unpriced.append(model_id)
        else:
            row["cost_usd"] += cost

    # Roll the models up by HOUSE — the vendor before the slash in the model id
    # (anthropic/…, openai/…). Today the portfolio holds one model per house so the two
    # views coincide, but that is a property of this configuration, not of the report:
    # add a second Anthropic model and only this level answers "what did Anthropic cost".
    # Note that the *provider* field is "openrouter" for every entry — OpenRouter is the
    # gateway, not the house, and grouping by it would produce a single row.
    per_house: Dict[str, Dict[str, Any]] = {}
    for model_id, row in per_model.items():
        api_model = (rates.get(model_id) or {}).get("api_model") or model_id
        house = api_model.split("/")[0] if "/" in api_model else "unknown"
        bucket = per_house.setdefault(house, {
            "calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
            "cost_usd": 0.0, "models": 0, "priced": True,
        })
        bucket["calls"] += row["calls"]
        bucket["prompt_tokens"] += row["prompt_tokens"]
        bucket["completion_tokens"] += row["completion_tokens"]
        bucket["cost_usd"] += row["cost_usd"]
        bucket["models"] += 1
        bucket["priced"] = bucket["priced"] and row["priced"]

    total = sum(r["cost_usd"] for r in per_model.values() if r["priced"])
    return {
        "per_model": per_model,
        "per_house": per_house,
        "total_cost_usd": total,
        "priced_calls": sum(r["calls"] for r in per_model.values() if r["priced"]),
        "unpriced_models": unpriced,
        "calls_without_usage": no_usage,
    }


def remaining_credit(timeout: int = 20) -> Optional[Tuple[float, float, float]]:
    """(total_credits, total_usage, remaining) from OpenRouter, or None if unavailable.

    Network call. Returns None rather than raising: not knowing the balance must never be
    the reason a finished run fails to report what it cost.
    """
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    try:
        request = urllib.request.Request(
            CREDITS_URL, headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response).get("data", {})
        total = float(data["total_credits"])
        used = float(data["total_usage"])
        return total, used, total - used
    except (urllib.error.URLError, KeyError, ValueError, TypeError, OSError):
        return None


def format_report(summary: Dict[str, Any], credit: Optional[Tuple[float, float, float]] = None) -> str:
    """Human-readable breakdown. Returns a string; printing is the caller's business."""
    lines = ["", "═══ Actual cost of this run (billed tokens) ═══", ""]
    if not summary["per_model"]:
        lines.append("  No usage data was reported for any call.")
    else:
        lines.append(f"  {'Model':<26}{'calls':>6}{'in':>10}{'out':>10}{'USD':>10}")
        lines.append("  " + "─" * 62)
        for row in sorted(summary["per_model"].values(),
                          key=lambda r: -r["cost_usd"]):
            cost = f"{row['cost_usd']:.4f}" if row["priced"] else "unpriced"
            lines.append(f"  {row['name'][:25]:<26}{row['calls']:>6}"
                         f"{row['prompt_tokens']:>10,}{row['completion_tokens']:>10,}"
                         f"{cost:>10}")
        lines.append("  " + "─" * 62)
        lines.append(f"  {'TOTAL':<26}{summary['priced_calls']:>6}"
                     f"{'':>10}{'':>10}{summary['total_cost_usd']:>10.4f}")

    houses = summary.get("per_house") or {}
    if len(houses) > 1:
        lines += ["", "  By house (the vendor behind the model, not the gateway):"]
        for house, row in sorted(houses.items(), key=lambda kv: -kv[1]["cost_usd"]):
            cost = f"{row['cost_usd']:.4f}" if row["priced"] else "unpriced"
            share = (row["cost_usd"] / summary["total_cost_usd"] * 100
                     if summary["total_cost_usd"] else 0)
            lines.append(f"    {house:<22}{row['models']:>3} model(s)"
                         f"{row['calls']:>5} calls{cost:>11}{share:>7.1f}%")

    if summary["unpriced_models"]:
        lines += ["", f"  ⚠️  No price recorded for: {', '.join(summary['unpriced_models'])}",
                  "      Those calls are excluded from the total; add a `pricing` block to",
                  "      their openrouter_config.json entries."]
    if summary["calls_without_usage"]:
        lines.append(f"  ⚠️  {summary['calls_without_usage']} call(s) reported no usage data "
                     f"and are not counted.")

    if credit:
        total, used, left = credit
        lines += ["", f"  OpenRouter balance: ${left:,.2f} remaining "
                      f"(${used:,.2f} used of ${total:,.2f})"]
        if summary["total_cost_usd"] > 0:
            runs_left = int(left / summary["total_cost_usd"])
            lines.append(f"  At this run's cost that is roughly {runs_left:,} more runs.")
        if left < 5:
            lines.append("  ⚠️  Under $5 remaining.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("usage: python run_cost_report.py <run_directory|isee_result.json>")
        credit = remaining_credit()
        if credit:
            total, used, left = credit
            print(f"\nOpenRouter balance: ${left:,.2f} remaining "
                  f"(${used:,.2f} used of ${total:,.2f})")
        raise SystemExit(0)

    target = sys.argv[1]
    path = (os.path.join(target, "isee_result.json")
            if os.path.isdir(target) else target)
    with io.open(path, encoding="utf-8") as f:
        payload = json.load(f)
    results = payload.get("results", payload)
    print(format_report(summarise(results), remaining_credit()))
